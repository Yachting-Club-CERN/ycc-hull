"""
Common API error handling.
"""

from typing import Any

from fastapi import HTTPException


def create_http_exception(status_code: int, detail: Any) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=detail,
    )


def create_http_exception_400(detail: Any) -> HTTPException:
    return create_http_exception(400, detail)


def create_http_exception_401(detail: Any) -> HTTPException:
    return create_http_exception(401, detail)


def create_http_exception_403(detail: Any) -> HTTPException:
    return create_http_exception(403, detail)


def create_http_exception_404(detail: Any) -> HTTPException:
    return create_http_exception(404, detail)


def create_http_exception_409(detail: Any) -> HTTPException:
    return create_http_exception(409, detail)
