from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import Base


ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository class with common CRUD operations."""

    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initialize repository with model class and database session.

        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db

    def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Get a single record by ID.

        Args:
            id: Record ID

        Returns:
            Model instance or None if not found
        """
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """
        Get all records with optional filtering and pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Dictionary of field:value pairs for filtering

        Returns:
            List of model instances
        """
        query = self.db.query(self.model)

        if filters:
            filter_conditions = [
                getattr(self.model, key) == value
                for key, value in filters.items()
                if hasattr(self.model, key)
            ]
            if filter_conditions:
                query = query.filter(and_(*filter_conditions))

        return query.offset(skip).limit(limit).all()

    def create(self, obj: ModelType) -> ModelType:
        """
        Create a new record.

        Args:
            obj: Model instance to create

        Returns:
            Created model instance
        """
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: ModelType) -> ModelType:
        """
        Update an existing record.

        Args:
            obj: Model instance to update

        Returns:
            Updated model instance
        """
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id: int) -> bool:
        """
        Delete a record by ID.

        Args:
            id: Record ID

        Returns:
            True if deleted, False if not found
        """
        obj = self.get_by_id(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filtering.

        Args:
            filters: Dictionary of field:value pairs for filtering

        Returns:
            Number of records
        """
        query = self.db.query(self.model)

        if filters:
            filter_conditions = [
                getattr(self.model, key) == value
                for key, value in filters.items()
                if hasattr(self.model, key)
            ]
            if filter_conditions:
                query = query.filter(and_(*filter_conditions))

        return query.count()
