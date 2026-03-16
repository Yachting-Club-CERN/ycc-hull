"""Controller exceptions."""


class ControllerError(Exception):
    """General exception for controllers."""

    def __init__(self, message: str) -> None:
        """Initialise with an error message."""
        super().__init__(message)
        self.message = message


class ControllerBadRequestError(ControllerError):
    """Raised when a controller receives a bad request."""


class ControllerNotFoundError(ControllerError):
    """Raised when a controller cannot find a resource."""


class ControllerConflictError(ControllerError):
    """Raised when a conflict is detected in a controller."""
