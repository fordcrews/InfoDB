from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SnmpProfile(Base):
    """SNMP credentials stored separately from routers for rotation and encryption."""

    __tablename__ = "snmp_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    version: Mapped[str] = mapped_column(String(10), default="v3")
    community: Mapped[str | None] = mapped_column(String(64), nullable=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    auth_protocol: Mapped[str | None] = mapped_column(String(20), nullable=True)
    auth_password_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    priv_protocol: Mapped[str | None] = mapped_column(String(20), nullable=True)
    priv_password_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    routers: Mapped[list["Router"]] = relationship(back_populates="snmp_profile")


class Router(Base):
    __tablename__ = "routers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    ip_address: Mapped[str] = mapped_column(String(45), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(100), nullable=True)
    snmp_profile_id: Mapped[int | None] = mapped_column(ForeignKey("snmp_profiles.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    snmp_profile: Mapped["SnmpProfile | None"] = relationship(back_populates="routers")