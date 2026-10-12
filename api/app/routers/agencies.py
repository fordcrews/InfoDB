from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_admin
from app.database import get_db
from app.models.agency import Agency
from app.models.subnet import Subnet
from app.models.user import User
from app.schemas.network import AgencyCreate, AgencyResponse, AgencyUpdate

router = APIRouter(prefix="/agencies", tags=["agencies"])


async def _agency_response(db: AsyncSession, agency: Agency) -> AgencyResponse:
    count = (
        await db.execute(select(func.count()).select_from(Subnet).where(Subnet.agency_id == agency.id))
    ).scalar_one()
    return AgencyResponse(
        id=agency.id,
        name=agency.name,
        description=agency.description,
        subnet_count=count,
    )


@router.get("", response_model=list[AgencyResponse])
async def list_agencies(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[AgencyResponse]:
    result = await db.execute(select(Agency).order_by(Agency.name))
    agencies = result.scalars().all()
    return [await _agency_response(db, agency) for agency in agencies]


@router.post("", response_model=AgencyResponse, status_code=201)
async def create_agency(
    payload: AgencyCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> AgencyResponse:
    existing = await db.execute(select(Agency).where(Agency.name == payload.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Agency name already exists")

    agency = Agency(name=payload.name, description=payload.description)
    db.add(agency)
    await db.commit()
    await db.refresh(agency)
    return await _agency_response(db, agency)


@router.patch("/{agency_id}", response_model=AgencyResponse)
async def update_agency(
    agency_id: int,
    payload: AgencyUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> AgencyResponse:
    agency = await db.get(Agency, agency_id)
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")

    data = payload.model_dump(exclude_unset=True)
    if "name" in data:
        conflict = await db.execute(
            select(Agency).where(Agency.name == data["name"], Agency.id != agency_id)
        )
        if conflict.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Agency name already exists")

    for key, value in data.items():
        setattr(agency, key, value)

    await db.commit()
    await db.refresh(agency)
    return await _agency_response(db, agency)


@router.delete("/{agency_id}", status_code=204)
async def delete_agency(
    agency_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    agency = await db.get(Agency, agency_id)
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")

    subnet_count = (
        await db.execute(select(func.count()).select_from(Subnet).where(Subnet.agency_id == agency_id))
    ).scalar_one()
    if subnet_count:
        raise HTTPException(status_code=409, detail="Agency has subnets; reassign them first")

    await db.delete(agency)
    await db.commit()