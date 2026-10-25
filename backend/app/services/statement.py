from typing import List, Optional, Sequence
from sqlalchemy.orm import Session

from app.repositories.statement import StatementRepository
from app.models.enums import UserRole
from app.models.statement import Statement, StatementStatus
from app.models.user import User
from app.schemas.statement import StatementCreate, StatementUpdate


class StatementPermissionError(Exception):
    """The viewer's role does not allow the requested status read or write."""


def can_moderate(viewer: Optional[User]) -> bool:
    """Whether `viewer` may see and set every status (moderator or admin)."""
    return viewer is not None and viewer.role.at_least(UserRole.MODERATOR)


def _visible_statuses(viewer: Optional[User]) -> Optional[List[StatementStatus]]:
    """
    Statuses `viewer` may list: None (all) for moderators and admins,
    only verified for anonymous and default users.
    """
    return None if can_moderate(viewer) else [StatementStatus.VERIFIED]


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

    def create_statement(
        self, statement_data: StatementCreate, viewer: Optional[User] = None
    ) -> Statement:
        """
        Create a new statement. Unless `viewer` is a moderator or admin, the
        status is forced to pending whatever the payload says.

        Args:
            statement_data: Statement creation data
            viewer: User creating the statement

        Returns:
            Created Statement instance
        """
        data = statement_data.model_dump()
        if not can_moderate(viewer):
            data["status"] = StatementStatus.PENDING
        statement = Statement(**data)
        return self.repository.create(statement)

    def get_statement_by_id(self, statement_id: int) -> Optional[Statement]:
        """
        Get statement by ID, whatever its status.

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
        active_only: bool = True,
        viewer: Optional[User] = None
    ) -> List[Statement]:
        """
        Get all statements with pagination. Anonymous and default users only
        get verified statements.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: If True, return only active statements
            viewer: Requesting user, or None if anonymous

        Returns:
            List of Statement instances
        """
        statuses = _visible_statuses(viewer)
        if active_only:
            return self.repository.get_active_statements(
                skip=skip, limit=limit, statuses=statuses
            )
        return self.repository.get_all_statements(skip=skip, limit=limit, statuses=statuses)

    def update_statement(
        self,
        statement_id: int,
        statement_data: StatementUpdate,
        viewer: Optional[User] = None
    ) -> Optional[Statement]:
        """
        Update an existing statement. Only moderators and admins may set status.

        Args:
            statement_id: Statement ID
            statement_data: Statement update data
            viewer: User making the change

        Returns:
            Updated Statement instance or None if not found

        Raises:
            StatementPermissionError: If the payload sets status and `viewer`
                is not a moderator or admin
        """
        update_data = statement_data.model_dump(exclude_unset=True)
        if "status" in update_data and not can_moderate(viewer):
            raise StatementPermissionError("Setting 'status' requires the moderator role")

        statement = self.repository.get_by_id(statement_id)
        if not statement:
            return None

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
        limit: int = 100,
        viewer: Optional[User] = None
    ) -> List[Statement]:
        """
        Get statements by politician name. Anonymous and default users only
        get verified statements.

        Args:
            politician_name: Name of the politician
            skip: Number of records to skip
            limit: Maximum number of records to return
            viewer: Requesting user, or None if anonymous

        Returns:
            List of Statement instances
        """
        return self.repository.get_by_politician(
            politician_name, skip, limit, statuses=_visible_statuses(viewer)
        )

    def get_statements_by_party(
        self,
        party: str,
        skip: int = 0,
        limit: int = 100,
        viewer: Optional[User] = None
    ) -> List[Statement]:
        """
        Get statements by party. Anonymous and default users only get
        verified statements.

        Args:
            party: Name of the party
            skip: Number of records to skip
            limit: Maximum number of records to return
            viewer: Requesting user, or None if anonymous

        Returns:
            List of Statement instances
        """
        return self.repository.get_by_party(
            party, skip, limit, statuses=_visible_statuses(viewer)
        )

    def get_statements_by_status(
        self,
        status: StatementStatus,
        skip: int = 0,
        limit: int = 100,
        viewer: Optional[User] = None
    ) -> List[Statement]:
        """
        Get statements by verification status. Anonymous and default users
        may only ask for verified.

        Args:
            status: Statement status
            skip: Number of records to skip
            limit: Maximum number of records to return
            viewer: Requesting user, or None if anonymous

        Returns:
            List of Statement instances

        Raises:
            StatementPermissionError: If `status` is not verified and `viewer`
                is not a moderator or admin
        """
        if status != StatementStatus.VERIFIED and not can_moderate(viewer):
            raise StatementPermissionError(
                f"Listing '{status.value}' statements requires the moderator role"
            )
        return self.repository.get_by_status(status, skip, limit)

    def search_statements(
        self,
        search_text: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        *,
        statuses: Optional[Sequence[StatementStatus]] = None,
        statuses_not: Optional[Sequence[StatementStatus]] = None,
        politicians: Optional[Sequence[str]] = None,
        parties: Optional[Sequence[str]] = None,
        categories: Optional[Sequence[str]] = None,
        viewer: Optional[User] = None,
    ) -> List[Statement]:
        """
        Search statements by text and filters (see
        StatementRepository.search_statements for matching rules).

        Anonymous and default users only get verified statements and may not
        filter by status; moderators and admins get every status unless they
        filter.

        Args:
            search_text: Text to search for, or None
            skip: Number of records to skip
            limit: Maximum number of records to return
            statuses: Status is one of these
            statuses_not: Status is none of these
            politicians: Politician name matchers
            parties: Party matchers
            categories: Category matchers
            viewer: Requesting user, or None if anonymous

        Returns:
            List of Statement instances

        Raises:
            StatementPermissionError: If a non-moderator filters by status
        """
        if not can_moderate(viewer):
            for param, values in (("status", statuses), ("status_not", statuses_not)):
                if values:
                    raise StatementPermissionError(
                        f"Filtering by '{param}' requires the moderator role"
                    )
            statuses = _visible_statuses(viewer)
        return self.repository.search_statements(
            search_text,
            skip,
            limit,
            statuses=statuses or None,
            statuses_not=statuses_not,
            politicians=politicians,
            parties=parties,
            categories=categories,
        )

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
