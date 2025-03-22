"""
User model.
"""

from pydantic import ConfigDict

from ycc_hull.models.base import CamelisedBaseModel

_YCC_ADMIN_ROLE = "ycc-admin"

_YCC_ACTIVE_MEMBER_ROLE = "ycc-member-active"
_YCC_COMMITTEE_MEMBER_ROLE = "ycc-member-committee"
_YCC_LICENCE_ROLE_PREFIX = "ycc-licence-"

_YCC_HELPERS_APP_ADMIN_ROLE = "ycc-helpers-app-admin"
_YCC_HELPERS_APP_EDITOR_ROLE = "ycc-helpers-app-editor"


def _get_licence_role(licence: str) -> str:
    """
    Get the role name for the given licence type.
    """
    return f"{_YCC_LICENCE_ROLE_PREFIX}{licence.lower()}"


class User(CamelisedBaseModel):
    """
    User model.
    """

    model_config = ConfigDict(frozen=True)

    member_id: int
    username: str
    groups: tuple[str, ...]
    roles: tuple[str, ...]

    @property
    def active_member(self) -> bool:
        return _YCC_ACTIVE_MEMBER_ROLE in self.roles

    @property
    def admin(self) -> bool:
        return _YCC_ADMIN_ROLE in self.roles

    @property
    def committee_member(self) -> bool:
        return _YCC_COMMITTEE_MEMBER_ROLE in self.roles

    @property
    def helpers_app_admin(self) -> bool:
        return f"{_YCC_HELPERS_APP_ADMIN_ROLE}" in self.roles

    @property
    def helpers_app_editor(self) -> bool:
        return f"{_YCC_HELPERS_APP_EDITOR_ROLE}" in self.roles

    @property
    def helpers_app_admin_or_editor(self) -> bool:
        return self.helpers_app_admin or self.helpers_app_editor

    def has_licence(self, licence: str) -> bool:
        return _get_licence_role(licence) in self.roles
