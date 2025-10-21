from typing import List, Optional
from sqlalchemy.orm import Session

from app.repositories.statement import StatementRepository
from app.models.statement import Statement, StatementStatus
from app.schemas.statement import StatementCreate, StatementUpdate


class StatementService:
    """Service layer for Statement business logic."""

    def __init__(self, db: Session):
        """
        Initialize Statement service.

        Args:
            db: Database session
        """
        self.repository = StatementRepository(db)
        self.db = db

    def create_statement(self, statement_data: StatementCreate) -> Statement:
        """
        Create a new statement.

        Args:
            statement_data: Statement creation data

        Returns:
            Created Statement instance
        """
        statement = Statement(**statement_data.model_dump())
        return self.repository.create(statement)

    def get_statement_by_id(self, statement_id: int) -> Optional[Statement]:
        """
        Get statement by ID.

        Args:
            statement_id: Statement ID

        Returns:
            Statement instance or None if not found
        """
        return self.repository.get_by_id(statement_id)

    def get_all_statements(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Statement]:
        """
        Get all statements with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: If True, return only active statements

        Returns:
            List of Statement instances
        """
        if active_only:
            return self.repository.get_active_statements(skip=skip, limit=limit)
        return self.repository.get_all(skip=skip, limit=limit)

    def update_statement(
        self,
        statement_id: int,
        statement_data: StatementUpdate
    ) -> Optional[Statement]:
        """
        Update an existing statement.

        Args:
            statement_id: Statement ID
            statement_data: Statement update data

        Returns:
            Updated Statement instance or None if not found
        """
        statement = self.repository.get_by_id(statement_id)
        if not statement:
            return None

        update_data = statement_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(statement, field, value)

        return self.repository.update(statement)

    def delete_statement(self, statement_id: int, soft_delete: bool = True) -> bool:
        """
        Delete a statement (soft or hard delete).

        Args:
            statement_id: Statement ID
            soft_delete: If True, perform soft delete (set is_active=False)

        Returns:
            True if deleted successfully, False otherwise
        """
        if soft_delete:
            result = self.repository.soft_delete(statement_id)
            return result is not None
        return self.repository.delete(statement_id)

    def get_statements_by_politician(
        self,
        politician_name: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Statement]:
        """
        Get statements by politician name.

        Args:
            politician_name: Name of the politician
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Statement instances
        """
        return self.repository.get_by_politician(politician_name, skip, limit)

    def get_statements_by_party(
        self,
        party: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Statement]:
        """
        Get statements by party.

        Args:
            party: Name of the party
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Statement instances
        """
        return self.repository.get_by_party(party, skip, limit)

    def get_statements_by_status(
        self,
        status: StatementStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[Statement]:
        """
        Get statements by verification status.

        Args:
            status: Statement status
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Statement instances
        """
        return self.repository.get_by_status(status, skip, limit)

    def search_statements(
        self,
        search_text: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Statement]:
        """
        Search statements by text.

        Args:
            search_text: Text to search for
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Statement instances
        """
        return self.repository.search_statements(search_text, skip, limit)

    def count_statements(self, active_only: bool = True) -> int:
        """
        Count total statements.

        Args:
            active_only: If True, count only active statements

        Returns:
            Number of statements
        """
        if active_only:
            return self.repository.count({"is_active": True})
        return self.repository.count()
