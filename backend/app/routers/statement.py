from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.statement import StatementService
from app.schemas.statement import (
    StatementCreate,
    StatementUpdate,
    StatementResponse
)
from app.models.statement import StatementStatus
from app.models.user import User
from app.core.dependencies import get_current_user


router = APIRouter(
    prefix="/statements",
    tags=["statements"]
)


def get_statement_service(db: Session = Depends(get_db)) -> StatementService:
    """Dependency for getting StatementService instance."""
    return StatementService(db)


@router.post(
    "/",
    response_model=StatementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new statement",
    responses={401: {"description": "Not authenticated"}}
)
def create_statement(
    statement: StatementCreate,
    service: StatementService = Depends(get_statement_service),
    current_user: User = Depends(get_current_user)
) -> StatementResponse:
    """
    Create a new political statement.
    Requires authentication.

    Args:
        statement: Statement data
        service: Statement service instance
        current_user: Authenticated user

    Returns:
        Created statement
    """
    return service.create_statement(statement)


@router.get(
    "/",
    response_model=List[StatementResponse],
    summary="Get all statements"
)
def get_statements(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    active_only: bool = Query(True, description="Return only active statements"),
    service: StatementService = Depends(get_statement_service)
) -> List[StatementResponse]:
    """
    Get all statements with pagination.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        active_only: If True, return only active statements
        service: Statement service instance

    Returns:
        List of statements
    """
    return service.get_all_statements(skip=skip, limit=limit, active_only=active_only)


@router.get(
    "/{statement_id}",
    response_model=StatementResponse,
    summary="Get statement by ID"
)
def get_statement(
    statement_id: int,
    service: StatementService = Depends(get_statement_service)
) -> StatementResponse:
    """
    Get a specific statement by ID.

    Args:
        statement_id: Statement ID
        service: Statement service instance

    Returns:
        Statement data

    Raises:
        HTTPException: 404 if statement not found
    """
    statement = service.get_statement_by_id(statement_id)
    if not statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Statement with id {statement_id} not found"
        )
    return statement


@router.put(
    "/{statement_id}",
    response_model=StatementResponse,
    summary="Update statement",
    responses={401: {"description": "Not authenticated"}, 404: {"description": "Statement not found"}}
)
def update_statement(
    statement_id: int,
    statement_data: StatementUpdate,
    service: StatementService = Depends(get_statement_service),
    current_user: User = Depends(get_current_user)
) -> StatementResponse:
    """
    Update an existing statement.
    Requires authentication.

    Args:
        statement_id: Statement ID
        statement_data: Updated statement data
        service: Statement service instance
        current_user: Authenticated user

    Returns:
        Updated statement

    Raises:
        HTTPException: 404 if statement not found
    """
    statement = service.update_statement(statement_id, statement_data)
    if not statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Statement with id {statement_id} not found"
        )
    return statement


@router.delete(
    "/{statement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete statement",
    responses={401: {"description": "Not authenticated"}, 404: {"description": "Statement not found"}}
)
def delete_statement(
    statement_id: int,
    soft_delete: bool = Query(True, description="If True, perform soft delete"),
    service: StatementService = Depends(get_statement_service),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a statement (soft or hard delete).
    Requires authentication.

    Args:
        statement_id: Statement ID
        soft_delete: If True, perform soft delete (set is_active=False)
        service: Statement service instance
        current_user: Authenticated user

    Raises:
        HTTPException: 404 if statement not found
    """
    success = service.delete_statement(statement_id, soft_delete=soft_delete)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Statement with id {statement_id} not found"
        )


@router.get(
    "/politician/{politician_name}",
    response_model=List[StatementResponse],
    summary="Get statements by politician"
)
def get_statements_by_politician(
    politician_name: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: StatementService = Depends(get_statement_service)
) -> List[StatementResponse]:
    """
    Get all statements by a specific politician.

    Args:
        politician_name: Name of the politician
        skip: Number of records to skip
        limit: Maximum number of records to return
        service: Statement service instance

    Returns:
        List of statements
    """
    return service.get_statements_by_politician(politician_name, skip, limit)


@router.get(
    "/party/{party}",
    response_model=List[StatementResponse],
    summary="Get statements by party"
)
def get_statements_by_party(
    party: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: StatementService = Depends(get_statement_service)
) -> List[StatementResponse]:
    """
    Get all statements by a specific party.

    Args:
        party: Name of the party
        skip: Number of records to skip
        limit: Maximum number of records to return
        service: Statement service instance

    Returns:
        List of statements
    """
    return service.get_statements_by_party(party, skip, limit)


@router.get(
    "/status/{status}",
    response_model=List[StatementResponse],
    summary="Get statements by status"
)
def get_statements_by_status(
    status: StatementStatus,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: StatementService = Depends(get_statement_service)
) -> List[StatementResponse]:
    """
    Get all statements by verification status.

    Args:
        status: Statement status (pending, verified, disputed, retracted)
        skip: Number of records to skip
        limit: Maximum number of records to return
        service: Statement service instance

    Returns:
        List of statements
    """
    return service.get_statements_by_status(status, skip, limit)


@router.get(
    "/search/",
    response_model=List[StatementResponse],
    summary="Search statements"
)
def search_statements(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: StatementService = Depends(get_statement_service)
) -> List[StatementResponse]:
    """
    Search statements by text in statement content, politician name, or party.

    Args:
        q: Search query
        skip: Number of records to skip
        limit: Maximum number of records to return
        service: Statement service instance

    Returns:
        List of matching statements
    """
    return service.search_statements(q, skip, limit)
