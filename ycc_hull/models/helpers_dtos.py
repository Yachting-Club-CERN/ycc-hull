"""
Helpers API DTO classes.
"""
from collections.abc import Sequence
from datetime import datetime
from typing import Optional

from pydantic import Field, field_validator, model_validator

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
    long_description: Optional[str] = Field(json_schema_extra={"html": True})

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
    long_description: Optional[str] = Field(json_schema_extra={"html": True})
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

    @classmethod
    def create(cls, task: HelperTaskEntity) -> "HelperTaskDto":
        return cls._create(task, task.long_description)

    @classmethod
    def create_without_long_description(cls, task: HelperTaskEntity) -> "HelperTaskDto":
        return cls._create(task, None)

    @staticmethod
    def _create(
        task: HelperTaskEntity, long_description: Optional[str]
    ) -> "HelperTaskDto":
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
            long_description=long_description,
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
    long_description: Optional[str] = Field(json_schema_extra={"html": True})
    contact_id: int
    starts_at: Optional[datetime]
    ends_at: Optional[datetime]
    deadline: Optional[datetime]
    urgent: bool
    captain_required_licence_info_id: Optional[int]
    helper_min_count: int
    helper_max_count: int
    published: bool

    @field_validator("title", "short_description")
    @classmethod
    def check_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field must not be blank")
        return value

    @model_validator(mode="after")
    def check_timing(self) -> "HelperTaskMutationRequestDto":
        valid_shift = (
            self.starts_at
            and self.ends_at
            and not self.deadline
            and self.starts_at < self.ends_at
        )
        valid_deadline = not self.starts_at and not self.ends_at and self.deadline

        if valid_shift or valid_deadline:
            return self
        raise ValueError("Invalid timing")

    @model_validator(mode="after")
    def check_helper_min_max_count(self) -> "HelperTaskMutationRequestDto":
        if 0 <= self.helper_min_count <= self.helper_max_count:
            return self
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


HelperTaskCategoryDto.model_rebuild()
HelperTaskDto.model_rebuild()
HelperTaskMutationRequestDto.model_rebuild()
HelperTaskHelperDto.model_rebuild()
