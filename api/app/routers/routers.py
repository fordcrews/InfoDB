from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, require_admin
from app.core.encryption import decrypt_secret
from app.database import get_db
from app.models.router import Router, SnmpProfile
from app.models.user import User
from app.schemas.network import RouterCreate, RouterResponse, RouterUpdate
from app.services.snmp_client import SnmpCredentials, test_snmp

router = APIRouter(prefix="/routers", tags=["routers"])


@router.get("", response_model=list[RouterResponse])
async def list_routers(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[RouterResponse]:
    result = await db.execute(
        select(Router).options(selectinload(Router.snmp_profile)).order_by(Router.name)
    )
    return [RouterResponse.model_validate(item) for item in result.scalars().all()]


@router.post("", response_model=RouterResponse, status_code=201)
async def create_router(
    payload: RouterCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> RouterResponse:
    if payload.snmp_profile_id:
        profile = await db.get(SnmpProfile, payload.snmp_profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="SNMP profile not found")

    existing = await db.execute(select(Router).where(Router.ip_address == payload.ip_address))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Router IP already exists")

    router_obj = Router(**payload.model_dump())
    db.add(router_obj)
    await db.commit()
    result = await db.execute(
        select(Router).options(selectinload(Router.snmp_profile)).where(Router.id == router_obj.id)
    )
    return RouterResponse.model_validate(result.scalar_one())


@router.patch("/{router_id}", response_model=RouterResponse)
async def update_router(
    router_id: int,
    payload: RouterUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> RouterResponse:
    result = await db.execute(
        select(Router).options(selectinload(Router.snmp_profile)).where(Router.id == router_id)
    )
    router_obj = result.scalar_one_or_none()
    if not router_obj:
        raise HTTPException(status_code=404, detail="Router not found")

    data = payload.model_dump(exclude_unset=True)
    if "snmp_profile_id" in data and data["snmp_profile_id"] is not None:
        profile = await db.get(SnmpProfile, data["snmp_profile_id"])
        if not profile:
            raise HTTPException(status_code=404, detail="SNMP profile not found")

    if "ip_address" in data:
        conflict = await db.execute(
            select(Router).where(Router.ip_address == data["ip_address"], Router.id != router_id)
        )
        if conflict.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Router IP already exists")

    for key, value in data.items():
        setattr(router_obj, key, value)

    await db.commit()
    await db.refresh(router_obj)
    return RouterResponse.model_validate(router_obj)


@router.delete("/{router_id}", status_code=204)
async def delete_router(
    router_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    router_obj = await db.get(Router, router_id)
    if not router_obj:
        raise HTTPException(status_code=404, detail="Router not found")

    await db.delete(router_obj)
    await db.commit()


@router.post("/{router_id}/test")
async def test_router_snmp(
    router_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(
        select(Router).options(selectinload(Router.snmp_profile)).where(Router.id == router_id)
    )
    router_obj = result.scalar_one_or_none()
    if not router_obj:
        raise HTTPException(status_code=404, detail="Router not found")

    if not router_obj.snmp_profile:
        return {"success": False, "error": "No SNMP profile attached to this router"}

    profile = router_obj.snmp_profile
    creds = SnmpCredentials(
        version=profile.version,
        community=profile.community,
        username=profile.username,
        auth_protocol=profile.auth_protocol,
        auth_password=decrypt_secret(profile.auth_password_enc) if profile.auth_password_enc else None,
        priv_protocol=profile.priv_protocol,
        priv_password=decrypt_secret(profile.priv_password_enc) if profile.priv_password_enc else None,
    )

    return await test_snmp(router_obj.ip_address, creds)