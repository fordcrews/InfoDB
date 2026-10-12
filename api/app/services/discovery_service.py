"""ARP discovery orchestration."""

import asyncio
import ipaddress
import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.encryption import decrypt_secret
from app.models.discovery import DiscoveryRun
from app.models.router import Router
from app.models.subnet import Subnet
from app.repositories.asset_repository import AssetRepository
from app.services.snmp_client import ArpEntry, SnmpCredentials, walk_arp_table

logger = logging.getLogger(__name__)


def _match_subnet(ip: str, subnets: list[Subnet]) -> int | None:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return None
    for subnet in subnets:
        try:
            network = ipaddress.ip_network(subnet.cidr, strict=False)
        except ValueError:
            continue
        if addr in network:
            return subnet.id
    return None


def _router_credentials(router: Router) -> SnmpCredentials:
    profile = router.snmp_profile
    if not profile:
        return SnmpCredentials(version="v2c", community="public")

    return SnmpCredentials(
        version=profile.version,
        community=profile.community,
        username=profile.username,
        auth_protocol=profile.auth_protocol,
        auth_password=decrypt_secret(profile.auth_password_enc),
        priv_protocol=profile.priv_protocol,
        priv_password=decrypt_secret(profile.priv_password_enc),
    )


async def _load_routers(session: AsyncSession, router_id: int | None) -> list[Router]:
    query = (
        select(Router)
        .options(selectinload(Router.snmp_profile))
        .where(Router.is_active.is_(True))
    )
    if router_id is not None:
        query = query.where(Router.id == router_id)
    result = await session.execute(query.order_by(Router.name))
    return list(result.scalars().all())


async def run_arp_discovery(session: AsyncSession, *, router_id: int | None = None) -> list[DiscoveryRun]:
    routers = await _load_routers(session, router_id)
    if not routers:
        raise ValueError("No active routers configured")

    logger.info(f"Loaded {len(routers)} router(s) for discovery")

    subnet_result = await session.execute(select(Subnet))
    subnets = list(subnet_result.scalars().all())
    asset_repo = AssetRepository(session)
    runs: list[DiscoveryRun] = []

    for router in routers:
        run = DiscoveryRun(
            run_type="arp",
            status="running",
            router_id=router.id,
            started_at=datetime.now(UTC),
        )
        session.add(run)
        await session.commit()
        await session.refresh(run)

        logger.info(f"Starting ARP discovery for router {router.name or router.ip_address} ({router.ip_address})")

        try:
            creds = _router_credentials(router)
            logger.info(f"Walking ARP table on {router.ip_address} ...")
            entries: list[ArpEntry] = await asyncio.wait_for(
                walk_arp_table(router.ip_address, creds), timeout=60
            )
            found = len(entries)
            logger.info(f"Found {found} ARP entries from {router.ip_address}")

            updated = 0
            new_count = 0

            for entry in entries:
                subnet_match = _match_subnet(entry.ip_address, subnets)
                _, is_new = await asset_repo.upsert_from_discovery(
                    mac_address=entry.mac_address,
                    ip_address=entry.ip_address,
                    subnet_id=subnet_match,
                )
                if is_new:
                    new_count += 1
                else:
                    updated += 1

            run.status = "completed"
            run.assets_found = found
            run.assets_updated = updated
            run.assets_new = new_count
            run.finished_at = datetime.now(UTC)
            logger.info(f"Discovery completed for {router.ip_address}: found={found}, new={new_count}, updated={updated}")
        except Exception as exc:
            run.status = "failed"
            run.error_message = str(exc)[:2000]
            run.finished_at = datetime.now(UTC)
            logger.exception(f"Discovery failed for router {router.ip_address}: {exc}")

        await session.commit()
        await session.refresh(run)
        runs.append(run)

    return runs