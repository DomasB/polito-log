from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.services.statement import StatementPermissionError


async def statement_permission_error_handler(
    request: Request, error: StatementPermissionError
) -> JSONResponse:
    """Answer a role-gated status read or write with 403 and the error's message."""
    return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": str(error)})


def register_exception_handlers(app: FastAPI) -> None:
    """Map domain exceptions raised below the routers to HTTP responses."""
    app.add_exception_handler(StatementPermissionError, statement_permission_error_handler)
