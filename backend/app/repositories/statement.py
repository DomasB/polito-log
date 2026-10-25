from typing import List, Optional, Sequence
from sqlalchemy.orm import Query, Session
from sqlalchemy import or_
from sqlalchemy.sql.elements import ColumnElement

from app.repositories.base import BaseRepository
from app.models.statement import Statement, StatementStatus
from app.schemas.statement import StatementSearchFilters


def _escape_like(text: str) -> str:
    """Escape LIKE wildcards (with backslash as the escape character)."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _contains(column, text: str) -> ColumnElement:
    """Case-insensitive substring match; % and _ in `text` match literally."""
    return column.ilike(f"%{_escape_like(text)}%", escape="\\")


def _equals_ignore_case(column, text: str) -> ColumnElement:
    """Case-insensitive equality (ILIKE without wildcards, so it folds case like _contains)."""
    return column.ilike(_escape_like(text), escape="\\")


def _text_match(column, values: Sequence[str]) -> ColumnElement:
    """
    OR of one condition per value. A value wrapped in double quotes ("LSDP")
    matches the unquoted content exactly; any other value matches as a
    substring. Both are case-insensitive.
    """
    conditions = []
    for value in values:
        if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
            conditions.append(_equals_ignore_case(column, value[1:-1]))
        else:
            conditions.append(_contains(column, value))
    return or_(*conditions)


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
        limit: int = 100,
        statuses: Optional[Sequence[StatementStatus]] = None
    ) -> List[Statement]:
        """
        Get statements by politician name.

        Args:
            politician_name: Name of the politician
            skip: Number of records to skip
            limit: Maximum number of records to return
            statuses: If given, only statements with one of these statuses

        Returns:
            List of Statement instances
        """
        return (
            self._active(statuses)
            .filter(Statement.politician_name == politician_name)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_party(
        self,
        party: str,
        skip: int = 0,
        limit: int = 100,
        statuses: Optional[Sequence[StatementStatus]] = None
    ) -> List[Statement]:
        """
        Get statements by party.

        Args:
            party: Name of the party
            skip: Number of records to skip
            limit: Maximum number of records to return
            statuses: If given, only statements with one of these statuses

        Returns:
            List of Statement instances
        """
        return (
            self._active(statuses)
            .filter(Statement.party == party)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_status(
        self,
        status: StatementStatus,
        skip: int = 0,
        limit: int = 100,
        statuses: Optional[Sequence[StatementStatus]] = None
    ) -> List[Statement]:
        """
        Get statements by verification status.

        Args:
            status: Statement status
            skip: Number of records to skip
            limit: Maximum number of records to return
            statuses: If given, only statements with one of these statuses

        Returns:
            List of Statement instances
        """
        return (
            self._active(statuses)
            .filter(Statement.status == status)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_statements(
        self,
        filters: StatementSearchFilters,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Statement]:
        """
        Search active statements. Every given filter must hold (AND); the
        values of one list filter are alternatives (OR).

        Takes the request-shape schema directly: the one place a repository
        depends on app.schemas, to avoid restating six filters as kwargs.

        Args:
            filters: q is a substring of statement_text, politician_name or
                party (case-insensitive, % and _ literal); status is one of /
                status_not none of the given statuses; politician, party and
                category each match one of their values (see _text_match)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Statement instances
        """
        query = self._active(filters.status or None)
        if filters.q:
            query = query.filter(
                or_(
                    _contains(Statement.statement_text, filters.q),
                    _contains(Statement.politician_name, filters.q),
                    _contains(Statement.party, filters.q),
                )
            )
        if filters.status_not:
            query = query.filter(Statement.status.not_in(filters.status_not))
        if filters.politician:
            query = query.filter(_text_match(Statement.politician_name, filters.politician))
        if filters.party:
            query = query.filter(_text_match(Statement.party, filters.party))
        if filters.category:
            query = query.filter(_text_match(Statement.category, filters.category))
        return query.offset(skip).limit(limit).all()

    def get_active_statements(
        self,
        skip: int = 0,
        limit: int = 100,
        statuses: Optional[Sequence[StatementStatus]] = None
    ) -> List[Statement]:
        """
        Get all active statements.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            statuses: If given, only statements with one of these statuses

        Returns:
            List of Statement instances
        """
        return (
            self._active(statuses)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_all_statements(
        self,
        skip: int = 0,
        limit: int = 100,
        statuses: Optional[Sequence[StatementStatus]] = None
    ) -> List[Statement]:
        """
        Get statements, active or not.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            statuses: If given, only statements with one of these statuses

        Returns:
            List of Statement instances
        """
        return (
            self._with_statuses(self.db.query(Statement), statuses)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def _active(self, statuses: Optional[Sequence[StatementStatus]]) -> Query:
        """Active statements, restricted to `statuses` (None means all)."""
        return self._with_statuses(self.db.query(Statement), statuses).filter(
            Statement.is_active == True
        )

    @staticmethod
    def _with_statuses(
        query: Query, statuses: Optional[Sequence[StatementStatus]]
    ) -> Query:
        """Restrict `query` to the given statuses; None means no restriction."""
        if statuses is None:
            return query
        return query.filter(Statement.status.in_(statuses))

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
