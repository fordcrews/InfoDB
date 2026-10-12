"""Seed dev data: admin user and sample inventory."""

import asyncio

from sqlalchemy import select

from app.config import get_settings
from app.core.security import hash_password
from app.database import AsyncSessionLocal
from app.models.agency import Agency
from app.models.asset import Asset
from app.models.router import Router, SnmpProfile
from app.models.subnet import Subnet
from app.models.user import User


async def seed() -> None:
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(User).where(User.email == settings.admin_email))
        if existing.scalar_one_or_none() is None:
            session.add(
                User(
                    email=settings.admin_email,
                    display_name="Administrator",
                    hashed_password=hash_password(settings.admin_password),
                    role="admin",
                )
            )
            print(f"Created admin user: {settings.admin_email}")

        agency_result = await session.execute(select(Agency).where(Agency.name == "Default Agency"))
        agency = agency_result.scalar_one_or_none()
        if agency is None:
            agency = Agency(name="Default Agency", description="Sample agency for development")
            session.add(agency)
            await session.flush()

        subnet_result = await session.execute(select(Subnet).where(Subnet.cidr == "10.0.0.0/24"))
        subnet = subnet_result.scalar_one_or_none()
        if subnet is None:
            subnet = Subnet(cidr="10.0.0.0/24", description="Lab subnet", agency_id=agency.id)
            session.add(subnet)
            await session.flush()

        profile_result = await session.execute(
            select(SnmpProfile).where(SnmpProfile.name == "Lab v2c")
        )
        profile = profile_result.scalar_one_or_none()
        if profile is None:
            profile = SnmpProfile(
                name="Lab v2c",
                version="v2c",
                community="public",
            )
            session.add(profile)
            await session.flush()

        router_result = await session.execute(
            select(Router).where(Router.ip_address == "10.0.0.1")
        )
        if router_result.scalar_one_or_none() is None:
            session.add(
                Router(
                    name="Lab Gateway",
                    ip_address="10.0.0.1",
                    description="Sample router for discovery testing",
                    snmp_profile_id=profile.id,
                    is_active=True,
                )
            )

        sample_macs = [
            ("00:11:22:33:44:55", "10.0.0.10", "workstation-01"),
            ("00:11:22:33:44:56", "10.0.0.11", "printer-01"),
            ("00:11:22:33:44:57", "10.0.0.12", "switch-01"),
        ]
        for mac, ip, hostname in sample_macs:
            asset_result = await session.execute(select(Asset).where(Asset.mac_address == mac))
            if asset_result.scalar_one_or_none() is None:
                session.add(
                    Asset(
                        mac_address=mac,
                        ip_address=ip,
                        hostname=hostname,
                        subnet_id=subnet.id,
                        os_name="Unknown",
                    )
                )

        await session.commit()
        print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())