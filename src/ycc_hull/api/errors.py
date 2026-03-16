"""Common API error handling."""


from fastapi import HTTPException


def create_http_exception(status_code: int, detail: str) -> HTTPException:
    """Create an HTTP exception with a status code."""
    return HTTPException(
        status_code=status_code,
        detail=detail,
    )


def create_http_exception_400(detail: str) -> HTTPException:
    """Create a 400 Bad Request exception."""
    return create_http_exception(400, detail)


def create_http_exception_401(detail: str) -> HTTPException:
    """Create a 401 Unauthorized exception."""
    return create_http_exception(401, detail)


def create_http_exception_403(detail: str) -> HTTPException:
    """Create a 403 Forbidden exception."""
    return create_http_exception(403, detail)


def create_http_exception_404(detail: str) -> HTTPException:
    """Create a 404 Not Found exception."""
    return create_http_exception(404, detail)


def create_http_exception_409(detail: str) -> HTTPException:
    """Create a 409 Conflict exception."""
    return create_http_exception(409, detail)
