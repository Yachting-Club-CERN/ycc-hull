"""Common API error handling."""

from fastapi import HTTPException


def create_http_error(status_code: int, detail: str) -> HTTPException:
    """Create an HTTP exception with a status code."""
    return HTTPException(
        status_code=status_code,
        detail=detail,
    )


def create_http_error_400(detail: str) -> HTTPException:
    """Create a 400 Bad Request error."""
    return create_http_error(400, detail)


def create_http_error_401(detail: str) -> HTTPException:
    """Create a 401 Unauthorized error."""
    return create_http_error(401, detail)


def create_http_error_403(detail: str) -> HTTPException:
    """Create a 403 Forbidden error."""
    return create_http_error(403, detail)


def create_http_error_404(detail: str) -> HTTPException:
    """Create a 404 Not Found error."""
    return create_http_error(404, detail)


def create_http_error_409(detail: str) -> HTTPException:
    """Create a 409 Conflict error."""
    return create_http_error(409, detail)
