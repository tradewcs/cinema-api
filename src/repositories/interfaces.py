from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, Optional

ModelType = TypeVar("ModelType")


class IRepository(ABC, Generic[ModelType]):
    """
    Generic repository interface for CRUD operations.
    To use it, derive a concrete repository for a specific model:

    Example:
        class Payment:
            def __init__(self, id: int, amount: float):
                self.id = id
                self.amount = amount

        class PaymentRepository(IRepository[Payment]):
            ...
    """

    @abstractmethod
    async def get_by_id(self, instance_id: int) -> Optional[ModelType]:
        """Get instance by id"""

    @abstractmethod
    async def get_all(self, **kwargs: Any) -> list[ModelType]:
        """Get all instances, optionally filtered"""

    @abstractmethod
    async def count(self) -> int:
        """Count all instances"""

    @abstractmethod
    async def create(self, **kwargs: Any) -> ModelType:
        """Create new instance"""

    @abstractmethod
    async def update(self, instance: ModelType, **kwargs: Any) -> ModelType:
        """Update instance"""

    @abstractmethod
    async def delete(self, instance: ModelType) -> None:
        """Delete instance"""
