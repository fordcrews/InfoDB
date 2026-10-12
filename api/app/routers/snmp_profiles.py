from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_admin
from app.core.encryption import encrypt_secret
from app.database import get_db
from app.models.router import Router, SnmpProfile
from app.models.user import User
from app.schemas.network import SnmpProfileCreate, SnmpProfileResponse, SnmpProfileUpdate

router = APIRouter(prefix="/snmp-profiles", tags=["snmp-profiles"])


def _profile_to_response(profile: SnmpProfile, router_count: int = 0) -> SnmpProfileResponse:
    return SnmpProfileResponse(
        id=profile.id,
        name=profile.name,
        version=profile.version,
        community=profile.community,
        username=profile.username,
        auth_protocol=profile.auth_protocol,
        priv_protocol=profile.priv_protocol,
        created_at=profile.created_at,
        router_count=router_count,
    )


def _apply_profile_fields(profile: SnmpProfile, data: dict) -> None:
    if "auth_password" in data:
        profile.auth_password_enc = encrypt_secret(data.pop("auth_password"))
    if "priv_password" in data:
        profile.priv_password_enc = encrypt_secret(data.pop("priv_password"))
    for key, value in data.items():
        setattr(profile, key, value)


@router.get("", response_model=list[SnmpProfileResponse])
async def list_snmp_profiles(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[SnmpProfileResponse]:
    result = await db.execute(select(SnmpProfile).order_by(SnmpProfile.name))
    profiles = result.scalars().all()
    responses: list[SnmpProfileResponse] = []
    for profile in profiles:
        count = (
            await db.execute(
                select(func.count()).select_from(Router).where(Router.snmp_profile_id == profile.id)
            )
        ).scalar_one()
        responses.append(_profile_to_response(profile, count))
    return responses


@router.post("", response_model=SnmpProfileResponse, status_code=201)
async def create_snmp_profile(
    payload: SnmpProfileCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> SnmpProfileResponse:
    existing = await db.execute(select(SnmpProfile).where(SnmpProfile.name == payload.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="SNMP profile name already exists")

    data = payload.model_dump()
    profile = SnmpProfile(
        name=data["name"],
        version=data["version"],
        community=data.get("community"),
        username=data.get("username"),
        auth_protocol=data.get("auth_protocol"),
        priv_protocol=data.get("priv_protocol"),
    )
    _apply_profile_fields(profile, data)
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return _profile_to_response(profile)


@router.patch("/{profile_id}", response_model=SnmpProfileResponse)
async def update_snmp_profile(
    profile_id: int,
    payload: SnmpProfileUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> SnmpProfileResponse:
    profile = await db.get(SnmpProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="SNMP profile not found")

    data = payload.model_dump(exclude_unset=True)
    if "name" in data:
        conflict = await db.execute(
            select(SnmpProfile).where(SnmpProfile.name == data["name"], SnmpProfile.id != profile_id)
        )
        if conflict.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="SNMP profile name already exists")

    _apply_profile_fields(profile, data)
    await db.commit()
    await db.refresh(profile)
    count = (
        await db.execute(
            select(func.count()).select_from(Router).where(Router.snmp_profile_id == profile.id)
        )
    ).scalar_one()
    return _profile_to_response(profile, count)


@router.delete("/{profile_id}", status_code=204)
async def delete_snmp_profile(
    profile_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    profile = await db.get(SnmpProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="SNMP profile not found")

    router_count = (
        await db.execute(
            select(func.count()).select_from(Router).where(Router.snmp_profile_id == profile_id)
        )
    ).scalar_one()
    if router_count:
        raise HTTPException(status_code=409, detail="SNMP profile is linked to routers")

    await db.delete(profile)
    await db.commit()