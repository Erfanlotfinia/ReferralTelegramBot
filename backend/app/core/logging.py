from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar
from typing import Optional

request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="-")
_original_record_factory = logging.getLogRecordFactory()


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx_var.get()
        return True


def _record_factory(*args: object, **kwargs: object) -> logging.LogRecord:
    record = _original_record_factory(*args, **kwargs)
    if not hasattr(record, "request_id"):
        record.request_id = request_id_ctx_var.get()
    return record


def setup_logging() -> None:
    logging.setLogRecordFactory(_record_factory)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [request_id=%(request_id)s] %(name)s: %(message)s",
    )
    root_logger = logging.getLogger()
    request_filter = RequestIdFilter()
    root_logger.addFilter(request_filter)
    for handler in root_logger.handlers:
        handler.addFilter(request_filter)


def set_request_id(value: Optional[str]) -> str:
    request_id = value or str(uuid.uuid4())
    request_id_ctx_var.set(request_id)
    return request_id
