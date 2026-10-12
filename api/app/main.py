import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import agencies, assets, auth, discovery, health, routers, snmp_profiles, subnets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("InfoDB API starting with INFO logging enabled")

settings = get_settings()

app = FastAPI(
    title="InfoDB API",
    description="Network asset inventory and discovery",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(assets.router, prefix="/api/v1")
app.include_router(agencies.router, prefix="/api/v1")
app.include_router(subnets.router, prefix="/api/v1")
app.include_router(routers.router, prefix="/api/v1")
app.include_router(snmp_profiles.router, prefix="/api/v1")
app.include_router(discovery.router, prefix="/api/v1")