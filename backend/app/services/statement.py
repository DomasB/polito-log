from typing import List, Optional
from sqlalchemy.orm import Session

from app.repositories.statement import StatementRepository
from app.models.enums import UserRole
from app.models.statement import Statement, StatementStatus
from app.models.user import User
from app.schemas.statement import StatementCreate, StatementSearchFilters, StatementUpdate


class StatementPermissionError(Exception):
    """The caller's role does not allow the requested status read or write."""


def can_moderate(current_user: Optional[User]) -> bool:
    """
    Whether `current_user` (the authenticated caller, or None if anonymous)
    may see and set every status, i.e. is a moderator or admin.
    """
    return current_user is not None and current_user.role.at_least(UserRole.MODERATOR)


def _visible_statuses(current_user: Optional[User]) -> Optional[List[StatementStatus]]:
    """
    Statuses `current_user` may list: None (all) for moderators and admins,
    only verified for anonymous and default users.
    """
    return None if can_moderate(current_user) else [StatementStatus.VERIFIED]


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
        self, statement_data: StatementCreate, current_user: Optional[User] = None
    ) -> Statement:
        """
        Create a new statement. Unless `current_user` is a moderator or admin, the
        status is forced to pending whatever the payload says.

        Args:
            statement_data: Statement creation data
            current_user: User creating the statement

        Returns:
            Created Statement instance
        """
        data = statement_data.model_dump()
        if not can_moderate(current_user):
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
        current_user: Optional[User] = None
    ) -> List[Statement]:
        """
        Get all statements with pagination. Anonymous and default users only
        get verified statements.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: If True, return only active statements
            current_user: Requesting user, or None if anonymous

        Returns:
            List of Statement instances
        """
        statuses = _visible_statuses(current_user)
        if active_only:
            return self.repository.get_active_statements(
                skip=skip, limit=limit, statuses=statuses
            )
        return self.repository.get_all_statements(skip=skip, limit=limit, statuses=statuses)

    def update_statement(
        self,
        statement_id: int,
        statement_data: StatementUpdate,
        current_user: Optional[User] = None
    ) -> Optional[Statement]:
        """
        Update an existing statement. Only moderators and admins may set status.

        Args:
            statement_id: Statement ID
            statement_data: Statement update data
            current_user: User making the change

        Returns:
            Updated Statement instance or None if not found

        Raises:
            StatementPermissionError: If the payload sets status and `current_user`
                is not a moderator or admin
        """
        update_data = statement_data.model_dump(exclude_unset=True)
        if "status" in update_data and not can_moderate(current_user):
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
        current_user: Optional[User] = None
    ) -> List[Statement]:
        """
        Get statements by politician name. Anonymous and default users only
        get verified statements.

        Args:
            politician_name: Name of the politician
            skip: Number of records to skip
            limit: Maximum number of records to return
            current_user: Requesting user, or None if anonymous

        Returns:
            List of Statement instances
        """
        return self.repository.get_by_politician(
            politician_name, skip, limit, statuses=_visible_statuses(current_user)
        )

    def get_statements_by_party(
        self,
        party: str,
        skip: int = 0,
        limit: int = 100,
        current_user: Optional[User] = None
    ) -> List[Statement]:
        """
        Get statements by party. Anonymous and default users only get
        verified statements.

        Args:
            party: Name of the party
            skip: Number of records to skip
            limit: Maximum number of records to return
            current_user: Requesting user, or None if anonymous

        Returns:
            List of Statement instances
        """
        return self.repository.get_by_party(
            party, skip, limit, statuses=_visible_statuses(current_user)
        )

    def get_statements_by_status(
        self,
        status: StatementStatus,
        skip: int = 0,
        limit: int = 100,
        current_user: Optional[User] = None
    ) -> List[Statement]:
        """
        Get statements by verification status. Anonymous and default users
        only get verified statements, so any other status gives them [].

        Args:
            status: Statement status
            skip: Number of records to skip
            limit: Maximum number of records to return
            current_user: Requesting user, or None if anonymous

        Returns:
            List of Statement instances
        """
        return self.repository.get_by_status(
            status, skip, limit, statuses=_visible_statuses(current_user)
        )

    def search_statements(
        self,
        filters: StatementSearchFilters,
        skip: int = 0,
        limit: int = 100,
        current_user: Optional[User] = None,
    ) -> List[Statement]:
        """
        Search statements by text and filters (see
        StatementRepository.search_statements for matching rules).

        Anonymous and default users only get verified statements and may not
        filter by status; moderators and admins get every status unless they
        filter.

        Args:
            filters: Text and field filters
            skip: Number of records to skip
            limit: Maximum number of records to return
            current_user: Requesting user, or None if anonymous

        Returns:
            List of Statement instances

        Raises:
            StatementPermissionError: If a non-moderator filters by status
        """
        if not can_moderate(current_user):
            for param in ("status", "status_not"):
                if getattr(filters, param):
                    raise StatementPermissionError(
                        f"Filtering by '{param}' requires the moderator role"
                    )
            filters = filters.model_copy(
                update={"status": _visible_statuses(current_user)}
            )
        return self.repository.search_statements(filters, skip, limit)

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
