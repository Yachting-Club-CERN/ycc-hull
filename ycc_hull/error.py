"""
Common error handling.
"""
from typing import Any, Optional

from fastapi import HTTPException


def raise_400(detail: Any) -> HTTPException:
    """
    Raises a HTTP 400 Bad Request exception.

    Args:
        detail (str): exception detail

    Raises:
        HTTPException: exception
    """
    raise HTTPException(
        status_code=400,
        detail=detail,
    )


def raise_401(detail: Optional[Any] = None) -> HTTPException:
    """
    Raises a HTTP 401 Unauthorized exception.

    Raises:
        HTTPException: exception
    """
    raise HTTPException(
        status_code=401,
        detail=detail,
    )


def raise_403(detail: Optional[Any] = None) -> HTTPException:
    """
    Raises a HTTP 403 Forbidden exception.

    Raises:
        HTTPException: exception
    """
    raise HTTPException(
        status_code=403,
        detail=detail,
    )


def raise_404(detail: Optional[Any] = None) -> HTTPException:
    """
    Raises a HTTP 404 Not Found exception.

    Raises:
        HTTPException: exception
    """
    raise HTTPException(
        status_code=404,
        detail=detail,
    )
