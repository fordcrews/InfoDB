from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """Abstract repository — swap SQLAlchemy for another backend by subclassing."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @abstractmethod
    async def get_by_id(self, entity_id: int) -> T | None:
        raise NotImplementedError