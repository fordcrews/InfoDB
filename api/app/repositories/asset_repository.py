from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.asset import Asset
from app.repositories.base import Repository


class AssetRepository(Repository[Asset]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_id(self, entity_id: int) -> Asset | None:
        result = await self.session.execute(
            select(Asset).options(selectinload(Asset.subnet)).where(Asset.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def get_by_mac(self, mac_address: str) -> Asset | None:
        result = await self.session.execute(select(Asset).where(Asset.mac_address == mac_address))
        return result.scalar_one_or_none()

    async def list_assets(
        self,
        *,
        subnet_id: int | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Asset], int]:
        query = select(Asset).options(selectinload(Asset.subnet))
        count_query = select(func.count()).select_from(Asset)

        if subnet_id is not None:
            query = query.where(Asset.subnet_id == subnet_id)
            count_query = count_query.where(Asset.subnet_id == subnet_id)

        if search:
            pattern = f"%{search}%"
            filter_clause = (
                Asset.mac_address.ilike(pattern)
                | Asset.ip_address.ilike(pattern)
                | Asset.hostname.ilike(pattern)
                | Asset.os_name.ilike(pattern)
            )
            query = query.where(filter_clause)
            count_query = count_query.where(filter_clause)

        total = (await self.session.execute(count_query)).scalar_one()
        result = await self.session.execute(
            query.order_by(Asset.last_seen.desc()).offset((page - 1) * page_size).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def upsert_from_discovery(
        self,
        *,
        mac_address: str,
        ip_address: str,
        subnet_id: int | None = None,
        sys_descr: str | None = None,
    ) -> tuple[Asset, bool]:
        """Returns (asset, is_new)."""
        asset = await self.get_by_mac(mac_address)
        is_new = asset is None

        if is_new:
            asset = Asset(
                mac_address=mac_address,
                ip_address=ip_address,
                subnet_id=subnet_id,
                sys_descr=sys_descr,
            )
            self.session.add(asset)
        else:
            assert asset is not None
            asset.ip_address = ip_address
            asset.subnet_id = subnet_id or asset.subnet_id
            if sys_descr:
                asset.sys_descr = sys_descr
            asset.last_seen = datetime.now(UTC)

        await self.session.commit()
        await self.session.refresh(asset)
        return asset, is_new