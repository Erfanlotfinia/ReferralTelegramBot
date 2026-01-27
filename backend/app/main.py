from __future__ import annotations

import logging

from fastapi import FastAPI, Request

from app.api.routes import router
from app.core.logging import set_request_id, setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Referral API", version="0.1.0")
app.include_router(router)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = set_request_id(request.headers.get("X-Request-ID"))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
