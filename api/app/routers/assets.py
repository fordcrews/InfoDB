from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_admin
from app.database import get_db
from app.models.agency import Agency
from app.models.asset import Asset
from app.models.discovery import DiscoveryRun
from app.models.router import Router
from app.models.subnet import Subnet
from app.models.user import User
from app.repositories.asset_repository import AssetRepository
from app.schemas.asset import (
    AgencyOsCount,
    AssetListResponse,
    AssetResponse,
    AssetUpdate,
    DashboardStats,
)

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("", response_model=AssetListResponse)
async def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    subnet_id: int | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AssetListResponse:
    repo = AssetRepository(db)
    items, total = await repo.list_assets(
        subnet_id=subnet_id, search=search, page=page, page_size=page_size
    )
    return AssetListResponse(
        items=[AssetResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=DashboardStats)
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DashboardStats:
    total_assets = (await db.execute(select(func.count()).select_from(Asset))).scalar_one()
    cutoff = datetime.now(UTC) - timedelta(hours=24)
    assets_seen_24h = (
        await db.execute(select(func.count()).select_from(Asset).where(Asset.last_seen >= cutoff))
    ).scalar_one()
    router_count = (await db.execute(select(func.count()).select_from(Router))).scalar_one()
    subnet_count = (await db.execute(select(func.count()).select_from(Subnet))).scalar_one()

    last_run_result = await db.execute(
        select(DiscoveryRun).order_by(DiscoveryRun.created_at.desc()).limit(1)
    )
    last_run = last_run_result.scalar_one_or_none()

    agency_os_rows = await db.execute(
        select(
            Agency.name,
            func.coalesce(Asset.os_name, "Unknown").label("os_name"),
            func.count(Asset.id),
        )
        .select_from(Asset)
        .outerjoin(Subnet, Asset.subnet_id == Subnet.id)
        .outerjoin(Agency, Subnet.agency_id == Agency.id)
        .group_by(Agency.name, func.coalesce(Asset.os_name, "Unknown"))
        .order_by(func.count(Asset.id).desc())
        .limit(20)
    )

    agency_os_counts = [
        AgencyOsCount(
            agency_name=row[0] or "Unassigned",
            os_name=row[1],
            count=row[2],
        )
        for row in agency_os_rows.all()
    ]

    return DashboardStats(
        total_assets=total_assets,
        assets_seen_24h=assets_seen_24h,
        router_count=router_count,
        subnet_count=subnet_count,
        last_discovery_at=last_run.finished_at or last_run.started_at if last_run else None,
        last_discovery_status=last_run.status if last_run else None,
        agency_os_counts=agency_os_counts,
    )


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AssetResponse:
    repo = AssetRepository(db)
    asset = await repo.get_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return AssetResponse.model_validate(asset)


@router.patch("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: int,
    payload: AssetUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> AssetResponse:
    repo = AssetRepository(db)
    asset = await repo.get_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    data = payload.model_dump(exclude_unset=True)
    if "subnet_id" in data and data["subnet_id"] is not None:
        subnet = await db.get(Subnet, data["subnet_id"])
        if not subnet:
            raise HTTPException(status_code=404, detail="Subnet not found")

    for key, value in data.items():
        setattr(asset, key, value)

    await db.commit()
    asset = await repo.get_by_id(asset_id)
    assert asset is not None
    return AssetResponse.model_validate(asset)