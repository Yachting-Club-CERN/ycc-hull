from dataclasses import dataclass

from fastapi import FastAPI, Request

from ycc_hull.controllers.boats_controller import BoatsController
from ycc_hull.controllers.helpers_controller import HelpersController
from ycc_hull.controllers.holidays_controller import HolidaysController
from ycc_hull.controllers.licences_controller import LicencesController
from ycc_hull.controllers.members_controller import MembersController


@dataclass(frozen=True)
class Controllers:
    """
    Holds the controllers for the application.
    """

    boats_controller: BoatsController
    helpers_controller: HelpersController
    holidays_controller: HolidaysController
    licences_controller: LicencesController
    members_controller: MembersController


def init_app_controllers(app: FastAPI) -> None:
    # Starlette's app.state is perfect to share this with the scheduler
    app.state.controllers = Controllers(
        boats_controller=BoatsController(),
        helpers_controller=HelpersController(),
        holidays_controller=HolidaysController(),
        licences_controller=LicencesController(),
        members_controller=MembersController(),
    )


def get_controllers(app_or_request: FastAPI | Request) -> Controllers:
    app = app_or_request.app if isinstance(app_or_request, Request) else app_or_request
    return app.state.controllers


def get_boats_controller(app_or_request: Request) -> BoatsController:
    return get_controllers(app_or_request).boats_controller


def get_helpers_controller(app_or_request: Request) -> HelpersController:
    return get_controllers(app_or_request).helpers_controller


def get_holidays_controller(app_or_request: Request) -> HolidaysController:
    return get_controllers(app_or_request).holidays_controller


def get_licences_controller(app_or_request: Request) -> LicencesController:
    return get_controllers(app_or_request).licences_controller


def get_members_controller(app_or_request: Request) -> MembersController:
    return get_controllers(app_or_request).members_controller
