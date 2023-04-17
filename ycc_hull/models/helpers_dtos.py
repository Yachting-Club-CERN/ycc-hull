"""
Helpers API DTO classes.
"""
from collections.abc import Sequence
from datetime import datetime
from typing import Optional

from pydantic import root_validator, validator

from ycc_hull.db.entities import (
    HelperTaskCategoryEntity,
    HelperTaskEntity,
    HelperTaskHelperEntity,
    MemberEntity,
)
from ycc_hull.models.base import (
    CamelisedBaseModelWithEntity,
    sanitise_html_input,
    sanitise_text_input,
)
from ycc_hull.models.dtos import LicenceInfoDto, MemberPublicInfoDto


class HelperTaskCategoryDto(CamelisedBaseModelWithEntity[HelperTaskCategoryEntity]):
    """
    DTO for a helper task category.
    """

    id: int
    title: str
    short_description: str
    long_description: Optional[str]

    @staticmethod
    def create(category: HelperTaskCategoryEntity) -> "HelperTaskCategoryDto":
        return HelperTaskCategoryDto(
            entity=category,
            id=category.id,
            title=category.title,
            short_description=category.short_description,
            long_description=category.long_description,
        )


class HelperTaskDto(CamelisedBaseModelWithEntity[HelperTaskEntity]):
    """
    DTO for a helper task.
    """

    id: int
    category: HelperTaskCategoryDto
    title: str
    short_description: str
    long_description: Optional[str]
    contact: MemberPublicInfoDto
    start: Optional[datetime]
    end: Optional[datetime]
    deadline: Optional[datetime]
    urgent: bool
    captain_required_licence_info: Optional[LicenceInfoDto]
    helpers_min_count: int
    helpers_max_count: int
    published: bool

    captain: Optional["HelperTaskHelperDto"]
    helpers: Sequence["HelperTaskHelperDto"]

    @staticmethod
    def create(task: HelperTaskEntity) -> "HelperTaskDto":
        captain = (
            HelperTaskHelperDto.create_from_member_entity(
                # Either both or none are present
                task.captain,
                task.captain_subscribed_at,  # type: ignore
            )
            if task.captain
            else None
        )
        helpers = [HelperTaskHelperDto.create(helper) for helper in task.helpers]

        return HelperTaskDto(
            entity=task,
            id=task.id,
            category=HelperTaskCategoryDto.create(task.category),
            title=task.title,
            short_description=task.short_description,
            long_description=task.long_description,
            contact=MemberPublicInfoDto.create(task.contact),
            start=task.start,
            end=task.end,
            deadline=task.deadline,
            urgent=task.urgent,
            captain_required_licence_info=LicenceInfoDto.create(
                task.captain_required_licence_info
            )
            if task.captain_required_licence_info
            else None,
            helpers_min_count=task.helpers_min_count,
            helpers_max_count=task.helpers_max_count,
            published=task.published,
            captain=captain,
            helpers=helpers,
        )


class HelperTaskMutationRequestDto(CamelisedBaseModelWithEntity):
    """
    Mutation request DTO for helper task.
    """

    category_id: int
    title: str
    short_description: str
    long_description: Optional[str]
    contact_id: int
    start: Optional[datetime]
    end: Optional[datetime]
    deadline: Optional[datetime]
    urgent: bool
    captain_required_licence_info_id: Optional[int]
    helpers_min_count: int
    helpers_max_count: int
    published: bool

    @validator("title", "short_description")
    def check_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field must not be blank")
        return value

    @root_validator
    def check_timing(cls, values: dict) -> dict:
        start: Optional[datetime] = values.get("start")
        end: Optional[datetime] = values.get("end")
        deadline: Optional[datetime] = values.get("deadline")

        valid_shift = start and end and not deadline and start < end
        valid_deadline = not start and not end and deadline

        if valid_shift or valid_deadline:
            return values
        raise ValueError("Invalid timing")

    @root_validator
    def check_helpers_min_max_count(cls, values: dict) -> dict:
        helpers_min_count: int = values.get("helpers_min_count")  # type: ignore
        helpers_max_count: int = values.get("helpers_max_count")  # type: ignore

        if 0 <= helpers_min_count <= helpers_max_count:
            return values
        raise ValueError("Invalid minimum/maximum helper count")

    @root_validator
    def sanitise_strings(cls, values: dict) -> dict:
        for key, value in values.items():
            if isinstance(value, str):
                if key == "long_description":
                    values[key] = sanitise_html_input(value)
                else:
                    values[key] = sanitise_text_input(value)
        return values


class HelperTaskHelperDto(CamelisedBaseModelWithEntity[HelperTaskHelperEntity]):
    """
    DTO for helper task helper.
    """

    member: MemberPublicInfoDto
    subscribed_at: datetime

    @staticmethod
    def create(
        helper: HelperTaskHelperEntity,
    ) -> "HelperTaskHelperDto":
        return HelperTaskHelperDto(
            entity=None,
            member=MemberPublicInfoDto.create(helper.member),
            subscribed_at=helper.subscribed_at,
        )

    @staticmethod
    def create_from_member_entity(
        member: MemberEntity, subscribed_at: datetime
    ) -> "HelperTaskHelperDto":
        return HelperTaskHelperDto(
            entity=None,
            member=MemberPublicInfoDto.create(member),
            subscribed_at=subscribed_at,
        )


HelperTaskCategoryDto.update_forward_refs()
HelperTaskDto.update_forward_refs()
HelperTaskMutationRequestDto.update_forward_refs()
HelperTaskHelperDto.update_forward_refs()
