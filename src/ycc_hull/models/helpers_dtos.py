"""Helpers API DTO classes."""

from collections.abc import Sequence
from enum import StrEnum

from pydantic import (
    AwareDatetime,
    Field,
    NonNegativeInt,
    field_validator,
    model_validator,
)

from ycc_hull.db.entities import (
    AttachmentEntity,
    HelpersAppPermissionEntity,
    HelperTaskCategoryEntity,
    HelperTaskEntity,
    HelperTaskHelperEntity,
    MemberEntity,
)
from ycc_hull.models.base import CamelisedBaseModel, CamelisedBaseModelWithEntity
from ycc_hull.models.dtos import LicenceInfoDto, MemberPublicInfoDto


class AttachmentMetadataDto(CamelisedBaseModel):
    """DTO for attachment metadata (excludes binary content)."""

    id: int
    name: str
    description: str | None
    mime_type: str
    size_bytes: int
    owner: MemberPublicInfoDto
    created: AwareDatetime

    @staticmethod
    async def create(attachment: AttachmentEntity) -> "AttachmentMetadataDto":
        """Create a DTO from an attachment entity."""
        return AttachmentMetadataDto(
            id=attachment.id,
            name=attachment.name,
            description=attachment.description,
            mime_type=attachment.mime_type,
            size_bytes=attachment.size_bytes,
            owner=await MemberPublicInfoDto.create(
                await attachment.awaitable_attrs.owner
            ),
            created=attachment.created,
        )


class HelperTaskType(StrEnum):
    """Helper task type enumeration."""

    SHIFT = "Shift"
    DEADLINE = "Deadline"
    UNKNOWN = "Unknown"


class HelperTaskState(StrEnum):
    """Helper task state enumeration."""

    PENDING = "Pending"
    DONE = "Done"
    VALIDATED = "Validated"


class HelpersAppPermissionDto(CamelisedBaseModelWithEntity[HelpersAppPermissionEntity]):
    """DTO for Helpers App permission."""

    member: MemberPublicInfoDto
    permission: str
    note: str | None

    @staticmethod
    async def create(
        permission: HelpersAppPermissionEntity,
    ) -> "HelpersAppPermissionDto":
        """Create a DTO from a permission entity."""
        return HelpersAppPermissionDto(
            entity=permission,
            member=await MemberPublicInfoDto.create(
                await permission.awaitable_attrs.member
            ),
            permission=permission.permission,
            note=permission.note,
        )


class HelpersAppPermissionGrantRequestDto(CamelisedBaseModel):
    """DTO for Helpers App permission grant request."""

    member_id: int
    permission: str
    note: str | None


class HelpersAppPermissionUpdateRequestDto(CamelisedBaseModel):
    """DTO for Helpers App permission update request."""

    note: str | None


class HelperTaskCategoryDto(CamelisedBaseModelWithEntity[HelperTaskCategoryEntity]):
    """DTO for a helper task category."""

    id: int
    title: str
    short_description: str
    long_description: str | None = Field(json_schema_extra={"html": True})

    @staticmethod
    async def create(category: HelperTaskCategoryEntity) -> "HelperTaskCategoryDto":
        """Create a DTO from a category entity."""
        return HelperTaskCategoryDto(
            entity=category,
            id=category.id,
            title=category.title,
            short_description=category.short_description,
            long_description=await category.awaitable_attrs.long_description,
        )


class HelperTaskDto(CamelisedBaseModelWithEntity[HelperTaskEntity]):
    """DTO for a helper task."""

    id: int
    category: HelperTaskCategoryDto
    title: str
    short_description: str
    long_description: str | None = Field(json_schema_extra={"html": True})
    contact: MemberPublicInfoDto
    starts_at: AwareDatetime | None
    ends_at: AwareDatetime | None
    deadline: AwareDatetime | None
    urgent: bool
    captain_required_licence_info: LicenceInfoDto | None
    helper_min_count: NonNegativeInt
    helper_max_count: NonNegativeInt
    published: bool

    captain: "HelperTaskHelperDto | None"
    helpers: Sequence["HelperTaskHelperDto"]

    marked_as_done_at: AwareDatetime | None
    marked_as_done_by: MemberPublicInfoDto | None
    marked_as_done_comment: str | None = Field(json_schema_extra={"html": True})
    validated_at: AwareDatetime | None
    validated_by: MemberPublicInfoDto | None
    validation_comment: str | None = Field(json_schema_extra={"html": True})

    @property
    def year(self) -> int:
        """Return the year of the task."""
        return get_task_year(self)

    @property
    def type(self) -> HelperTaskType:
        """Return the type of the task."""
        if self.starts_at and self.ends_at and not self.deadline:
            return HelperTaskType.SHIFT
        if not self.starts_at and not self.ends_at and self.deadline:
            return HelperTaskType.DEADLINE
        return HelperTaskType.UNKNOWN

    @property
    def state(self) -> HelperTaskState:
        """Return the state of the task."""
        if self.validated_at:
            return HelperTaskState.VALIDATED
        if self.marked_as_done_at:
            return HelperTaskState.DONE
        return HelperTaskState.PENDING

    @classmethod
    async def create(cls, task: HelperTaskEntity) -> "HelperTaskDto":
        """Create a DTO from a task entity."""
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
        """Create a DTO without large text fields."""
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
                    task.captain_signed_up_at,  # ty: ignore[invalid-argument-type]
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


class HelperTaskMutationRequestBaseDto(CamelisedBaseModel):
    """Base DTO for helper task mutation requests."""

    category_id: int
    title: str
    short_description: str
    long_description: str | None = Field(json_schema_extra={"html": True})
    contact_id: int
    starts_at: AwareDatetime | None
    ends_at: AwareDatetime | None
    deadline: AwareDatetime | None
    urgent: bool
    captain_required_licence_info_id: int | None
    helper_min_count: NonNegativeInt
    helper_max_count: NonNegativeInt
    published: bool

    @property
    def year(self) -> int:
        """Return the year of the task."""
        return get_task_year(self)

    @field_validator("title", "short_description")
    @classmethod
    def check_not_blank(cls, value: str) -> str:
        """Validate that the field is not blank."""
        if not value.strip():
            msg = "Field must not be blank"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def check_timing(self) -> "HelperTaskMutationRequestBaseDto":
        """Validate task timing fields are consistent."""
        if self.starts_at and self.ends_at and not self.deadline:
            # Shifts have extra conditions
            if self.starts_at >= self.ends_at:
                msg = "Invalid timing: start time must be before end time"
                raise ValueError(msg)
            if self.starts_at.year != self.ends_at.year:
                msg = "Invalid timing: start and end time must be in the same year"
                raise ValueError(msg)
        elif not self.starts_at and not self.ends_at and self.deadline:
            # Nothing more to validate on one value
            pass
        else:
            msg = (
                "Invalid timing: either specify both start and end time for a shift "
                "or a deadline for a task"
            )
            raise ValueError(msg)

        return self

    @model_validator(mode="after")
    def check_helper_min_max_count(self) -> "HelperTaskMutationRequestBaseDto":
        """Validate helper min/max count."""
        if self.helper_min_count <= self.helper_max_count:
            return self
        msg = "Invalid minimum/maximum helper count"
        raise ValueError(msg)


class HelperTaskCreationRequestDto(HelperTaskMutationRequestBaseDto):
    """Creation request DTO for helper task."""


class HelperTaskUpdateRequestDto(HelperTaskMutationRequestBaseDto):
    """Update request DTO for helper task."""

    notify_signed_up_members: bool = Field(
        description="Notify signed up members about the update"
    )


class HelperTaskMarkAsDoneRequestDto(CamelisedBaseModel):
    """Mark as done request DTO for helper task."""

    comment: str | None = Field(json_schema_extra={"html": True})


class HelperTaskValidationRequestDto(CamelisedBaseModel):
    """Validation request DTO for helper task."""

    comment: str | None = Field(json_schema_extra={"html": True})


class HelperTaskHelperDto(CamelisedBaseModelWithEntity[HelperTaskHelperEntity]):
    """DTO for helper task helper."""

    member: MemberPublicInfoDto
    signed_up_at: AwareDatetime

    @staticmethod
    async def create(
        helper: HelperTaskHelperEntity,
    ) -> "HelperTaskHelperDto":
        """Create a DTO from a helper entity."""
        return HelperTaskHelperDto(
            entity=None,
            member=await MemberPublicInfoDto.create(helper.member),
            signed_up_at=helper.signed_up_at,
        )

    @staticmethod
    async def create_from_member_entity(
        member: MemberEntity, signed_up_at: AwareDatetime
    ) -> "HelperTaskHelperDto":
        """Create a DTO from a member entity."""
        return HelperTaskHelperDto(
            entity=None,
            member=await MemberPublicInfoDto.create(member),
            signed_up_at=signed_up_at,
        )


def get_task_year(task: HelperTaskDto | HelperTaskMutationRequestBaseDto) -> int:
    """Return the year of a task from its timing fields."""
    if task.starts_at:
        return task.starts_at.year
    if task.ends_at:
        return task.ends_at.year
    if task.deadline:
        return task.deadline.year
    msg = "Missing timing"
    raise ValueError(msg)


AttachmentMetadataDto.model_rebuild()
HelpersAppPermissionDto.model_rebuild()
HelpersAppPermissionGrantRequestDto.model_rebuild()
HelpersAppPermissionUpdateRequestDto.model_rebuild()
HelperTaskCategoryDto.model_rebuild()
HelperTaskDto.model_rebuild()
HelperTaskCreationRequestDto.model_rebuild()
HelperTaskUpdateRequestDto.model_rebuild()
HelperTaskHelperDto.model_rebuild()
