from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_admin
from app.database import get_db
from app.models.discovery import DiscoveryRun
from app.models.router import Router
from app.models.user import User
from app.schemas.network import DiscoveryRunCreate, DiscoveryRunListResponse, DiscoveryRunResponse
from app.services.discovery_service import run_arp_discovery

router = APIRouter(prefix="/discovery", tags=["discovery"])


async def _run_response(db: AsyncSession, run: DiscoveryRun) -> DiscoveryRunResponse:
    router_name = None
    if run.router_id:
        router_obj = await db.get(Router, run.router_id)
        router_name = router_obj.name if router_obj else None

    return DiscoveryRunResponse(
        id=run.id,
        run_type=run.run_type,
        status=run.status,
        router_id=run.router_id,
        router_name=router_name,
        assets_found=run.assets_found,
        assets_updated=run.assets_updated,
        assets_new=run.assets_new,
        error_message=run.error_message,
        started_at=run.started_at,
        finished_at=run.finished_at,
        created_at=run.created_at,
    )


@router.get("/runs", response_model=DiscoveryRunListResponse)
async def list_discovery_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DiscoveryRunListResponse:
    total = (await db.execute(select(func.count()).select_from(DiscoveryRun))).scalar_one()
    result = await db.execute(
        select(DiscoveryRun)
        .order_by(DiscoveryRun.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    runs = result.scalars().all()
    items = [await _run_response(db, run) for run in runs]
    return DiscoveryRunListResponse(items=items, total=total)


@router.get("/runs/{run_id}", response_model=DiscoveryRunResponse)
async def get_discovery_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DiscoveryRunResponse:
    run = await db.get(DiscoveryRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Discovery run not found")
    return await _run_response(db, run)


@router.post("/runs", response_model=list[DiscoveryRunResponse], status_code=201)
async def trigger_discovery(
    payload: DiscoveryRunCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[DiscoveryRunResponse]:
    if payload.router_id is not None:
        router_obj = await db.get(Router, payload.router_id)
        if not router_obj:
            raise HTTPException(status_code=404, detail="Router not found")

    try:
        runs = await run_arp_discovery(db, router_id=payload.router_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return [await _run_response(db, run) for run in runs]