from datetime import datetime

from pydantic import BaseModel, Field


class AgencyBase(BaseModel):
    name: str = Field(max_length=50)
    description: str | None = None


class AgencyCreate(AgencyBase):
    pass


class AgencyUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=50)
    description: str | None = None


class AgencyResponse(AgencyBase):
    id: int
    subnet_count: int = 0

    model_config = {"from_attributes": True}


class SubnetBase(BaseModel):
    cidr: str = Field(max_length=18)
    description: str | None = Field(default=None, max_length=100)
    agency_id: int | None = None


class SubnetCreate(SubnetBase):
    pass


class SubnetUpdate(BaseModel):
    cidr: str | None = Field(default=None, max_length=18)
    description: str | None = Field(default=None, max_length=100)
    agency_id: int | None = None


class AgencyBrief(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class SubnetResponse(SubnetBase):
    id: int
    agency: AgencyBrief | None = None
    asset_count: int = 0

    model_config = {"from_attributes": True}


class SnmpProfileBase(BaseModel):
    name: str = Field(max_length=50)
    version: str = Field(default="v3", max_length=10)
    community: str | None = Field(default=None, max_length=64)
    username: str | None = Field(default=None, max_length=64)
    auth_protocol: str | None = Field(default=None, max_length=20)
    auth_password: str | None = None
    priv_protocol: str | None = Field(default=None, max_length=20)
    priv_password: str | None = None


class SnmpProfileCreate(SnmpProfileBase):
    pass


class SnmpProfileUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=50)
    version: str | None = Field(default=None, max_length=10)
    community: str | None = Field(default=None, max_length=64)
    username: str | None = Field(default=None, max_length=64)
    auth_protocol: str | None = Field(default=None, max_length=20)
    auth_password: str | None = None
    priv_protocol: str | None = Field(default=None, max_length=20)
    priv_password: str | None = None


class SnmpProfileResponse(BaseModel):
    id: int
    name: str
    version: str
    community: str | None
    username: str | None
    auth_protocol: str | None
    priv_protocol: str | None
    created_at: datetime
    router_count: int = 0

    model_config = {"from_attributes": True}


class RouterBase(BaseModel):
    name: str = Field(max_length=50)
    ip_address: str = Field(max_length=45)
    description: str | None = Field(default=None, max_length=100)
    snmp_profile_id: int | None = None
    is_active: bool = True


class RouterCreate(RouterBase):
    pass


class RouterUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=50)
    ip_address: str | None = Field(default=None, max_length=45)
    description: str | None = Field(default=None, max_length=100)
    snmp_profile_id: int | None = None
    is_active: bool | None = None


class SnmpProfileBrief(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class RouterResponse(RouterBase):
    id: int
    created_at: datetime
    snmp_profile: SnmpProfileBrief | None = None

    model_config = {"from_attributes": True}


class DiscoveryRunCreate(BaseModel):
    router_id: int | None = None  # None = all active routers


class DiscoveryRunResponse(BaseModel):
    id: int
    run_type: str
    status: str
    router_id: int | None
    router_name: str | None = None
    assets_found: int
    assets_updated: int
    assets_new: int
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DiscoveryRunListResponse(BaseModel):
    items: list[DiscoveryRunResponse]
    total: int