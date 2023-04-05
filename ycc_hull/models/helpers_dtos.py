"""
Helpers API DTO classes.
"""
from datetime import datetime
from typing import Optional, Sequence

from ycc_hull.db.entities import (
    HelperTaskCategoryEntity,
    HelperTaskEntity,
    HelperTaskHelperEntity,
    MemberEntity,
)
from ycc_hull.models.base import CamelisedBaseModel
from ycc_hull.models.dtos import MemberPublicInfoDto


class HelperTaskCategoryDto(CamelisedBaseModel):
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
            id=category.id,
            title=category.title,
            short_description=category.short_description,
            long_description=category.long_description,
        )


class HelperTaskDto(CamelisedBaseModel):
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
    captain_required_licence: Optional[str]
    helpers_min_count: int
    helpers_max_count: int
    published: bool

    captain: Optional["HelperTaskHelperDto"]
    helpers: Sequence["HelperTaskHelperDto"]

    @staticmethod
    def create(task: HelperTaskEntity) -> "HelperTaskDto":
        captain = (
            HelperTaskHelperDto.create_from_member_entity(
                task.captain, task.captain_subscribed_at
            )
            if task.captain
            else None
        )
        helpers = [HelperTaskHelperDto.create(helper) for helper in task.helpers]

        return HelperTaskDto(
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
            captain_required_licence=task.captain_required_licence,
            helpers_min_count=task.helpers_min_count,
            helpers_max_count=task.helpers_max_count,
            published=task.published,
            captain=captain,
            helpers=helpers,
        )


class HelperTaskHelperDto(CamelisedBaseModel):
    """
    DTO for helper task helper.
    """

    member: MemberPublicInfoDto
    subscribed_at: datetime

    @staticmethod
    def create(
        helper: HelperTaskHelperEntity,
    ) -> "HelperTaskHelperDto":
        return HelperTaskHelperDto.create_from_member_entity(
            helper.member, helper.subscribed_at
        )

    @staticmethod
    def create_from_member_entity(
        member: MemberEntity, subscribed_at: datetime
    ) -> "HelperTaskHelperDto":
        return HelperTaskHelperDto(
            member=MemberPublicInfoDto.create(member),
            subscribed_at=subscribed_at,
        )


HelperTaskCategoryDto.update_forward_refs()
HelperTaskDto.update_forward_refs()
HelperTaskHelperDto.update_forward_refs()

# TODO On request DTO objects make sure to add validators (also validate the task timing fields)
