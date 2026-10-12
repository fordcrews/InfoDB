from datetime import datetime

from pydantic import BaseModel, Field


class SubnetBrief(BaseModel):
    id: int
    cidr: str

    model_config = {"from_attributes": True}


class AssetResponse(BaseModel):
    id: int
    mac_address: str
    ip_address: str
    hostname: str | None
    os_name: str | None
    sys_descr: str | None
    device_type: str | None
    subnet: SubnetBrief | None
    first_seen: datetime
    last_seen: datetime

    model_config = {"from_attributes": True}


class AssetUpdate(BaseModel):
    hostname: str | None = Field(default=None, max_length=255)
    os_name: str | None = Field(default=None, max_length=100)
    sys_descr: str | None = None
    device_type: str | None = Field(default=None, max_length=50)
    subnet_id: int | None = None


class AssetListResponse(BaseModel):
    items: list[AssetResponse]
    total: int
    page: int
    page_size: int


class AgencyOsCount(BaseModel):
    agency_name: str
    os_name: str
    count: int


class DashboardStats(BaseModel):
    total_assets: int
    assets_seen_24h: int
    router_count: int
    subnet_count: int
    last_discovery_at: datetime | None = None
    last_discovery_status: str | None = None
    agency_os_counts: list[AgencyOsCount] = []