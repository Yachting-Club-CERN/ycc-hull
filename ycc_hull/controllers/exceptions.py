"""
Controller exceptions.
"""


class ControllerException(Exception):
    """
    General exception for controllers.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ControllerBadRequestException(ControllerException):
    """
    This exception is raised when a controller receives a bad request.
    """


class ControllerNotFoundException(ControllerException):
    """
    This exception is raised when a controller cannot find a resource.
    """


class ControllerConflictException(ControllerException):
    """
    This exception is raised when a conflict is detected in a controller.
    """
