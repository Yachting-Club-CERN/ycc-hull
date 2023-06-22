"""
Helpers API DTO classes.
"""
from collections.abc import Sequence
from datetime import datetime
from typing import Optional

from pydantic import Field, root_validator, validator

from ycc_hull.db.entities import (
    HelperTaskCategoryEntity,
    HelperTaskEntity,
    HelperTaskHelperEntity,
    MemberEntity,
)
from ycc_hull.models.base import (
    CamelisedBaseModel,
    CamelisedBaseModelWithEntity,
)
from ycc_hull.models.dtos import LicenceInfoDto, MemberPublicInfoDto


class HelperTaskCategoryDto(CamelisedBaseModelWithEntity[HelperTaskCategoryEntity]):
    """
    DTO for a helper task category.
    """

    id: int
    title: str
    short_description: str
    long_description: Optional[str] = Field(html=True)

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
    long_description: Optional[str] = Field(html=True)
    contact: MemberPublicInfoDto
    starts_at: Optional[datetime]
    ends_at: Optional[datetime]
    deadline: Optional[datetime]
    urgent: bool
    captain_required_licence_info: Optional[LicenceInfoDto]
    helper_min_count: int
    helper_max_count: int
    published: bool

    captain: Optional["HelperTaskHelperDto"]
    helpers: Sequence["HelperTaskHelperDto"]

    @staticmethod
    def create(task: HelperTaskEntity) -> "HelperTaskDto":
        captain = (
            HelperTaskHelperDto.create_from_member_entity(
                # Either both or none are present
                task.captain,
                task.captain_signed_up_at,  # type: ignore
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
            starts_at=task.starts_at,
            ends_at=task.ends_at,
            deadline=task.deadline,
            urgent=task.urgent,
            captain_required_licence_info=LicenceInfoDto.create(
                task.captain_required_licence_info
            )
            if task.captain_required_licence_info
            else None,
            helper_min_count=task.helper_min_count,
            helper_max_count=task.helper_max_count,
            published=task.published,
            captain=captain,
            helpers=helpers,
        )


class HelperTaskMutationRequestDto(CamelisedBaseModel):
    """
    Mutation request DTO for helper task.
    """

    category_id: int
    title: str
    short_description: str
    long_description: Optional[str] = Field(html=True)
    contact_id: int
    starts_at: Optional[datetime]
    ends_at: Optional[datetime]
    deadline: Optional[datetime]
    urgent: bool
    captain_required_licence_info_id: Optional[int]
    helper_min_count: int
    helper_max_count: int
    published: bool

    @validator("title", "short_description")
    def check_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field must not be blank")
        return value

    @root_validator
    def check_timing(cls, values: dict) -> dict:
        starts_at: Optional[datetime] = values.get("starts_at")
        ends_at: Optional[datetime] = values.get("ends_at")
        deadline: Optional[datetime] = values.get("deadline")

        valid_shift = starts_at and ends_at and not deadline and starts_at < ends_at
        valid_deadline = not starts_at and not ends_at and deadline

        if valid_shift or valid_deadline:
            return values
        raise ValueError("Invalid timing")

    @root_validator
    def check_helper_min_max_count(cls, values: dict) -> dict:
        helper_min_count: int = values.get("helper_min_count")  # type: ignore
        helper_max_count: int = values.get("helper_max_count")  # type: ignore

        if 0 <= helper_min_count <= helper_max_count:
            return values
        raise ValueError("Invalid minimum/maximum helper count")


class HelperTaskHelperDto(CamelisedBaseModelWithEntity[HelperTaskHelperEntity]):
    """
    DTO for helper task helper.
    """

    member: MemberPublicInfoDto
    signed_up_at: datetime

    @staticmethod
    def create(
        helper: HelperTaskHelperEntity,
    ) -> "HelperTaskHelperDto":
        return HelperTaskHelperDto(
            entity=None,
            member=MemberPublicInfoDto.create(helper.member),
            signed_up_at=helper.signed_up_at,
        )

    @staticmethod
    def create_from_member_entity(
        member: MemberEntity, signed_up_at: datetime
    ) -> "HelperTaskHelperDto":
        return HelperTaskHelperDto(
            entity=None,
            member=MemberPublicInfoDto.create(member),
            signed_up_at=signed_up_at,
        )


HelperTaskCategoryDto.update_forward_refs()
HelperTaskDto.update_forward_refs()
HelperTaskMutationRequestDto.update_forward_refs()
HelperTaskHelperDto.update_forward_refs()
