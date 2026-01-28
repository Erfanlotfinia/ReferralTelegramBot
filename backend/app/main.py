from __future__ import annotations

import logging

if __package__ in (None, ""):
    from pathlib import Path
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.logging import set_request_id, setup_logging
from app.usecases.errors import DatabaseConnectionError

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Referral API", version="0.1.0")
app.include_router(router)


@app.exception_handler(DatabaseConnectionError)
async def database_connection_error_handler(
    request: Request, exc: DatabaseConnectionError
) -> JSONResponse:
    logger.warning("Database connection error", extra={"path": request.url.path})
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": str(exc)},
    )


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = set_request_id(request.headers.get("X-Request-ID"))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
