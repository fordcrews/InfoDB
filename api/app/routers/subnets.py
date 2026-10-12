from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, require_admin
from app.database import get_db
from app.models.agency import Agency
from app.models.asset import Asset
from app.models.subnet import Subnet
from app.models.user import User
from app.schemas.network import SubnetCreate, SubnetResponse, SubnetUpdate

router = APIRouter(prefix="/subnets", tags=["subnets"])


async def _subnet_response(db: AsyncSession, subnet: Subnet) -> SubnetResponse:
    count = (
        await db.execute(select(func.count()).select_from(Asset).where(Asset.subnet_id == subnet.id))
    ).scalar_one()
    return SubnetResponse(
        id=subnet.id,
        cidr=subnet.cidr,
        description=subnet.description,
        agency_id=subnet.agency_id,
        agency=subnet.agency,
        asset_count=count,
    )


@router.get("", response_model=list[SubnetResponse])
async def list_subnets(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[SubnetResponse]:
    result = await db.execute(
        select(Subnet).options(selectinload(Subnet.agency)).order_by(Subnet.cidr)
    )
    subnets = result.scalars().all()
    return [await _subnet_response(db, subnet) for subnet in subnets]


@router.post("", response_model=SubnetResponse, status_code=201)
async def create_subnet(
    payload: SubnetCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> SubnetResponse:
    if payload.agency_id:
        agency = await db.get(Agency, payload.agency_id)
        if not agency:
            raise HTTPException(status_code=404, detail="Agency not found")

    existing = await db.execute(select(Subnet).where(Subnet.cidr == payload.cidr))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Subnet CIDR already exists")

    subnet = Subnet(**payload.model_dump())
    db.add(subnet)
    await db.commit()
    result = await db.execute(
        select(Subnet).options(selectinload(Subnet.agency)).where(Subnet.id == subnet.id)
    )
    subnet = result.scalar_one()
    return await _subnet_response(db, subnet)


@router.patch("/{subnet_id}", response_model=SubnetResponse)
async def update_subnet(
    subnet_id: int,
    payload: SubnetUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> SubnetResponse:
    result = await db.execute(
        select(Subnet).options(selectinload(Subnet.agency)).where(Subnet.id == subnet_id)
    )
    subnet = result.scalar_one_or_none()
    if not subnet:
        raise HTTPException(status_code=404, detail="Subnet not found")

    data = payload.model_dump(exclude_unset=True)
    if "agency_id" in data and data["agency_id"] is not None:
        agency = await db.get(Agency, data["agency_id"])
        if not agency:
            raise HTTPException(status_code=404, detail="Agency not found")

    if "cidr" in data:
        conflict = await db.execute(
            select(Subnet).where(Subnet.cidr == data["cidr"], Subnet.id != subnet_id)
        )
        if conflict.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Subnet CIDR already exists")

    for key, value in data.items():
        setattr(subnet, key, value)

    await db.commit()
    await db.refresh(subnet)
    return await _subnet_response(db, subnet)


@router.delete("/{subnet_id}", status_code=204)
async def delete_subnet(
    subnet_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    subnet = await db.get(Subnet, subnet_id)
    if not subnet:
        raise HTTPException(status_code=404, detail="Subnet not found")

    asset_count = (
        await db.execute(select(func.count()).select_from(Asset).where(Asset.subnet_id == subnet_id))
    ).scalar_one()
    if asset_count:
        raise HTTPException(status_code=409, detail="Subnet has assets; reassign them first")

    await db.delete(subnet)
    await db.commit()