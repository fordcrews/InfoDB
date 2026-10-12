from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Subnet(Base):
    __tablename__ = "subnets"

    id: Mapped[int] = mapped_column(primary_key=True)
    cidr: Mapped[str] = mapped_column(String(18), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(100), nullable=True)
    agency_id: Mapped[int | None] = mapped_column(ForeignKey("agencies.id"), nullable=True)

    agency: Mapped["Agency | None"] = relationship(back_populates="subnets")
    assets: Mapped[list["Asset"]] = relationship(back_populates="subnet")