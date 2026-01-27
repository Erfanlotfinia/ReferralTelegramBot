from __future__ import annotations


class ValidationError(Exception):
    pass


class ConflictError(Exception):
    pass


class NotFoundError(Exception):
    pass
