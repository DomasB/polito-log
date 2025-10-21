from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.repositories.base import BaseRepository
from app.models.statement import Statement, StatementStatus


class StatementRepository(BaseRepository[Statement]):
    """Repository for Statement model with custom query methods."""

    def __init__(self, db: Session):
        """
        Initialize Statement repository.

        Args:
            db: Database session
        """
        super().__init__(Statement, db)

    def get_by_politician(
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
        return (
            self.db.query(Statement)
            .filter(Statement.politician_name == politician_name)
            .filter(Statement.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_party(
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
        return (
            self.db.query(Statement)
            .filter(Statement.party == party)
            .filter(Statement.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_status(
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
        return (
            self.db.query(Statement)
            .filter(Statement.status == status)
            .filter(Statement.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_statements(
        self,
        search_text: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Statement]:
        """
        Search statements by text in statement_text, politician_name, or party.

        Args:
            search_text: Text to search for
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Statement instances
        """
        search_pattern = f"%{search_text}%"
        return (
            self.db.query(Statement)
            .filter(
                and_(
                    Statement.is_active == True,
                    or_(
                        Statement.statement_text.ilike(search_pattern),
                        Statement.politician_name.ilike(search_pattern),
                        Statement.party.ilike(search_pattern)
                    )
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_active_statements(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Statement]:
        """
        Get all active statements.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Statement instances
        """
        return (
            self.db.query(Statement)
            .filter(Statement.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def soft_delete(self, id: int) -> Optional[Statement]:
        """
        Soft delete a statement by setting is_active to False.

        Args:
            id: Statement ID

        Returns:
            Updated Statement instance or None if not found
        """
        statement = self.get_by_id(id)
        if statement:
            statement.is_active = False
            return self.update(statement)
        return None
