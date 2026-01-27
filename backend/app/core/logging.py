from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar
from typing import Optional

request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx_var.get()
        return True


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [request_id=%(request_id)s] %(name)s: %(message)s",
    )
    logging.getLogger().addFilter(RequestIdFilter())


def set_request_id(value: Optional[str]) -> str:
    request_id = value or str(uuid.uuid4())
    request_id_ctx_var.set(request_id)
    return request_id
