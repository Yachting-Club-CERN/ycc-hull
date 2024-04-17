"""
Helpers API DTO classes.
"""

from collections.abc import Sequence
from datetime import datetime
from enum import Enum

from pydantic import Field, field_validator, model_validator

from ycc_hull.config import CONFIG
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


class HelperTaskType(str, Enum):
    """
    Helper task type enumeration.
    """

    SHIFT = "Shift"
    DEADLINE = "Deadline"
    UNKNOWN = "Unknown"


class HelperTaskState(str, Enum):
    """
    Helper task state enumeration.
    """

    PENDING = "Pending"
    DONE = "Done"
    VALIDATED = "Validated"


class HelperTaskCategoryDto(CamelisedBaseModelWithEntity[HelperTaskCategoryEntity]):
    """
    DTO for a helper task category.
    """

    id: int
    title: str
    short_description: str
    long_description: str | None = Field(json_schema_extra={"html": True})

    @staticmethod
    async def create(category: HelperTaskCategoryEntity) -> "HelperTaskCategoryDto":
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
    long_description: str | None = Field(json_schema_extra={"html": True})
    contact: MemberPublicInfoDto
    starts_at: datetime | None
    ends_at: datetime | None
    deadline: datetime | None
    urgent: bool
    captain_required_licence_info: LicenceInfoDto | None
    helper_min_count: int
    helper_max_count: int
    published: bool

    captain: "HelperTaskHelperDto | None"
    helpers: Sequence["HelperTaskHelperDto"]

    marked_as_done_at: datetime | None
    marked_as_done_by: MemberPublicInfoDto | None
    marked_as_done_comment: str | None
    validated_at: datetime | None
    validated_by: MemberPublicInfoDto | None
    validation_comment: str | None

    @property
    def year(self) -> int:
        if self.starts_at:
            return self.starts_at.year
        if self.ends_at:
            return self.ends_at.year
        if self.deadline:
            return self.deadline.year
        raise ValueError("Missing timing")

    @property
    def type(self) -> HelperTaskType:
        if self.starts_at and self.ends_at and not self.deadline:
            return HelperTaskType.SHIFT
        if not self.starts_at and not self.ends_at and self.deadline:
            return HelperTaskType.DEADLINE
        return HelperTaskType.UNKNOWN

    @property
    def state(self) -> HelperTaskState:
        if self.validated_at:
            return HelperTaskState.VALIDATED
        if self.marked_as_done_at:
            return HelperTaskState.DONE
        return HelperTaskState.PENDING

    @classmethod
    async def create(cls, task: HelperTaskEntity) -> "HelperTaskDto":
        return await cls._create(
            task,
            long_description=await task.awaitable_attrs.long_description,
            marked_as_done_comment=await task.awaitable_attrs.marked_as_done_comment,
            validation_comment=await task.awaitable_attrs.validation_comment,
        )

    @classmethod
    async def create_without_large_fields(
        cls, task: HelperTaskEntity
    ) -> "HelperTaskDto":
        return await cls._create(
            task,
            long_description=None,
            marked_as_done_comment=None,
            validation_comment=None,
        )

    @staticmethod
    async def _create(
        task: HelperTaskEntity,
        *,
        long_description: str | None,
        marked_as_done_comment: str | None,
        validation_comment: str | None,
    ) -> "HelperTaskDto":
        captain = await task.awaitable_attrs.captain
        captain_required_licence_info = (
            await task.awaitable_attrs.captain_required_licence_info
        )
        marked_as_done_by = await task.awaitable_attrs.marked_as_done_by
        validated_by = await task.awaitable_attrs.validated_by

        return HelperTaskDto(
            entity=task,
            id=task.id,
            category=await HelperTaskCategoryDto.create(
                await task.awaitable_attrs.category
            ),
            title=task.title,
            short_description=task.short_description,
            long_description=long_description,
            contact=await MemberPublicInfoDto.create(
                await task.awaitable_attrs.contact
            ),
            starts_at=task.starts_at,
            ends_at=task.ends_at,
            deadline=task.deadline,
            urgent=task.urgent,
            captain_required_licence_info=(
                await LicenceInfoDto.create(captain_required_licence_info)
                if captain_required_licence_info
                else None
            ),
            helper_min_count=task.helper_min_count,
            helper_max_count=task.helper_max_count,
            published=task.published,
            captain=(
                await HelperTaskHelperDto.create_from_member_entity(
                    # Either both or none are present
                    captain,
                    task.captain_signed_up_at,  # type: ignore
                )
                if task.captain
                else None
            ),
            helpers=[
                await HelperTaskHelperDto.create(helper)
                for helper in await task.awaitable_attrs.helpers
            ],
            marked_as_done_at=task.marked_as_done_at,
            marked_as_done_by=(
                await MemberPublicInfoDto.create(marked_as_done_by)
                if marked_as_done_by
                else None
            ),
            marked_as_done_comment=marked_as_done_comment,
            validated_at=task.validated_at,
            validated_by=(
                await MemberPublicInfoDto.create(validated_by) if validated_by else None
            ),
            validation_comment=validation_comment,
        )


class HelperTaskMutationRequestDto(CamelisedBaseModel):
    """
    Mutation request DTO for helper task.
    """

    category_id: int
    title: str
    short_description: str
    long_description: str | None = Field(json_schema_extra={"html": True})
    contact_id: int
    starts_at: datetime | None
    ends_at: datetime | None
    deadline: datetime | None
    urgent: bool
    captain_required_licence_info_id: int | None
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
        if self.starts_at and self.ends_at and not self.deadline:
            # Shifts have extra conditions
            if self.starts_at >= self.ends_at:
                raise ValueError("Invalid timing: start time must be before end time")
            if self.starts_at.year != self.ends_at.year:
                raise ValueError(
                    "Invalid timing: start and end time must be in the same year"
                )
        elif not self.starts_at and not self.ends_at and self.deadline:
            # Nothing more to validate on one value
            pass
        else:
            raise ValueError(
                "Invalid timing: either specify both start and end time for a shift or a deadline for a task"
            )

        return self

    @model_validator(mode="after")
    def check_helper_min_max_count(self) -> "HelperTaskMutationRequestDto":
        if 0 <= self.helper_min_count <= self.helper_max_count:
            return self
        raise ValueError("Invalid minimum/maximum helper count")


class HelperTaskMarkAsDoneRequestDto(CamelisedBaseModel):
    """
    Mark as done request DTO for helper task.
    """

    comment: str | None


class HelperTaskValidationRequestDto(CamelisedBaseModel):
    """
    Validation request DTO for helper task.
    """

    helpers_to_validate: list["HelperTaskHelperDto"] = Field(
        description="List of helpers to validate"
    )
    helpers_to_remove: list["HelperTaskHelperDto"] = Field(
        description="List of helpers to remove (e.g., no show)"
    )
    comment: str | None


class HelperTaskHelperDto(CamelisedBaseModelWithEntity[HelperTaskHelperEntity]):
    """
    DTO for helper task helper.
    """

    member: MemberPublicInfoDto
    signed_up_at: datetime

    @staticmethod
    async def create(
        helper: HelperTaskHelperEntity,
    ) -> "HelperTaskHelperDto":
        return HelperTaskHelperDto(
            entity=None,
            member=await MemberPublicInfoDto.create(helper.member),
            signed_up_at=helper.signed_up_at,
        )

    @staticmethod
    async def create_from_member_entity(
        member: MemberEntity, signed_up_at: datetime
    ) -> "HelperTaskHelperDto":
        return HelperTaskHelperDto(
            entity=None,
            member=await MemberPublicInfoDto.create(member),
            signed_up_at=signed_up_at,
        )


HelperTaskCategoryDto.model_rebuild()
HelperTaskDto.model_rebuild()
HelperTaskMutationRequestDto.model_rebuild()
HelperTaskHelperDto.model_rebuild()
