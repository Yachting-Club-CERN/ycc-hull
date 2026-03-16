"""User model."""

from pydantic import ConfigDict

from ycc_hull.models.base import CamelisedBaseModel

_YCC_ADMIN_ROLE = "ycc-admin"

_YCC_ACTIVE_MEMBER_ROLE = "ycc-member-active"
_YCC_COMMITTEE_MEMBER_ROLE = "ycc-member-committee"
_YCC_LICENCE_ROLE_PREFIX = "ycc-licence-"

_YCC_HELPERS_APP_ADMIN_ROLE = "ycc-helpers-app-admin"
_YCC_HELPERS_APP_EDITOR_ROLE = "ycc-helpers-app-editor"


def _get_licence_role(licence: str) -> str:
    """Get the role name for the given licence type."""
    return f"{_YCC_LICENCE_ROLE_PREFIX}{licence.lower()}"


class User(CamelisedBaseModel):
    """User model."""

    model_config = ConfigDict(frozen=True)

    member_id: int
    username: str
    email: str
    first_name: str
    last_name: str
    groups: tuple[str, ...]
    roles: tuple[str, ...]

    @property
    def full_name(self) -> str:
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def active_member(self) -> bool:
        """Check if user is an active member."""
        return _YCC_ACTIVE_MEMBER_ROLE in self.roles

    @property
    def admin(self) -> bool:
        """Check if user is an admin."""
        return _YCC_ADMIN_ROLE in self.roles

    @property
    def committee_member(self) -> bool:
        """Check if user is a committee member."""
        return _YCC_COMMITTEE_MEMBER_ROLE in self.roles

    @property
    def helpers_app_admin(self) -> bool:
        """Check if user is a helpers app admin."""
        return f"{_YCC_HELPERS_APP_ADMIN_ROLE}" in self.roles

    @property
    def helpers_app_editor(self) -> bool:
        """Check if user is a helpers app editor."""
        return f"{_YCC_HELPERS_APP_EDITOR_ROLE}" in self.roles

    @property
    def helpers_app_admin_or_editor(self) -> bool:
        """Check if user is a helpers app admin or editor."""
        return self.helpers_app_admin or self.helpers_app_editor

    def has_licence(self, licence: str) -> bool:
        """Check if user has the given licence."""
        return _get_licence_role(licence) in self.roles
