"""Helpers controller."""

from collections.abc import Sequence
from datetime import date, datetime, timedelta

from fastapi import UploadFile
from sqlalchemy import ColumnElement, and_, func, or_, select
from sqlalchemy.orm import Session, defer

from ycc_hull.config import CONFIG
from ycc_hull.constants import (
    ATTACHMENT_MAX_DESCRIPTION_LENGTH,
    ATTACHMENT_MAX_FILE_SIZE_BYTES,
    ATTACHMENT_MAX_PER_TASK,
    ATTACHMENT_REF_CLASS_ID,
    HEIC_HEIF_EXTENSIONS,
    SURVEILLANCE_SIGN_UP_LIMIT_DAY,
    SURVEILLANCE_SIGN_UP_LIMIT_MONTH,
    SURVEILLANCE_SIGN_UP_LIMIT_STR,
    SURVEILLANCE_TASK_PREFIX,
)
from ycc_hull.controllers.base_controller import BaseController
from ycc_hull.controllers.errors import (
    ControllerBadRequestError,
    ControllerConflictError,
    ControllerNotFoundError,
)
from ycc_hull.controllers.notifications.helpers_notifications_controller import (
    HelpersNotificationsController,
)
from ycc_hull.db.entities import (
    AttachmentEntity,
    HelpersAppPermissionEntity,
    HelperTaskCategoryEntity,
    HelperTaskEntity,
    HelperTaskHelperEntity,
    LicenceEntity,
    MemberEntity,
)
from ycc_hull.image_processing import convert_heic_to_jpeg
from ycc_hull.models.dtos import MemberPublicInfoDto
from ycc_hull.models.helpers_dtos import (
    AttachmentMetadataDto,
    HelpersAppPermissionDto,
    HelpersAppPermissionGrantRequestDto,
    HelpersAppPermissionUpdateRequestDto,
    HelperTaskCategoryDto,
    HelperTaskCreationRequestDto,
    HelperTaskDto,
    HelperTaskMarkAsDoneRequestDto,
    HelperTaskState,
    HelperTaskType,
    HelperTaskUpdateRequestDto,
    HelperTaskValidationRequestDto,
)
from ycc_hull.models.user import User
from ycc_hull.utils import (
    deep_diff,
    get_now,
    resolve_attachment_mime_type,
    sanitise_filename,
)

_ATTACHMENT_WITHOUT_BLOBS = (
    defer(AttachmentEntity.content),
    defer(AttachmentEntity.thumbnail),
)


class HelpersController(BaseController):
    """Helpers controller. Returns DTO objects."""

    def __init__(self) -> None:
        """Initialise the helpers controller."""
        super().__init__()

        self._notifications = HelpersNotificationsController()

    async def find_all_permissions(self) -> Sequence[HelpersAppPermissionDto]:
        """Return permissions."""
        return await self.database_context.query_all(
            select(HelpersAppPermissionEntity)
            .join(HelpersAppPermissionEntity.member)
            .order_by(MemberEntity.name, MemberEntity.firstname),
            async_transformer=HelpersAppPermissionDto.create,
        )

    async def grant_permission(
        self, request: HelpersAppPermissionGrantRequestDto, user: User
    ) -> HelpersAppPermissionDto:
        """Grant a permission to a member."""
        with self.database_action(
            action="Helpers / Grant Permission", user=user, details={"request": request}
        ) as session:
            permission_entity = HelpersAppPermissionEntity(**request.model_dump())
            session.add(permission_entity)
            session.commit()

            permission = await HelpersAppPermissionDto.create(permission_entity)
            self._logger.info(
                "Granted permission: %s, user: %s", permission, user.username
            )

            self._audit_log(
                session, user, "Helpers/Permissions/Grant", {"new": permission}
            )

            return permission

    async def update_permission(
        self, member_id: int, request: HelpersAppPermissionUpdateRequestDto, user: User
    ) -> HelpersAppPermissionDto:
        """Update a permission."""
        with self.database_action(
            action="Helpers / Update Permission",
            user=user,
            details={"member_id": member_id, "request": request},
        ) as session:
            original_permission = await self._get_permission_by_id(
                member_id, session=session
            )

            permission_entity = original_permission.get_entity()
            self._update_entity_from_dto(permission_entity, request)
            session.commit()

            updated_permission = await HelpersAppPermissionDto.create(permission_entity)
            self._logger.info(
                "Updated permission: %s, user: %s", updated_permission, user.username
            )

            self._audit_log(
                session,
                user,
                f"Helpers/Permissions/Update/{member_id}",
                {
                    "diff": deep_diff(original_permission, updated_permission),
                    "old": original_permission,
                    "new": updated_permission,
                },
            )

            return updated_permission

    async def revoke_permission(self, member_id: int, user: User) -> None:
        """Revoke a permission from a member."""
        if member_id == user.member_id:
            msg = "You cannot revoke your own permissions"
            raise ControllerConflictError(msg)

        with self.database_action(
            action="Helpers / Revoke Permission",
            user=user,
            details={"member_id": member_id},
        ) as session:
            permission = await self._get_permission_by_id(member_id, session=session)

            permission_entity = permission.get_entity()
            session.delete(permission_entity)
            session.commit()

            self._logger.info(
                "Revoked permission: %s, user: %s",
                permission,
                user.username,
            )

            self._audit_log(
                session,
                user,
                f"Helpers/Permissions/Revoke/{member_id}",
                {
                    "old": permission,
                },
            )

    async def _get_permission_by_id(
        self, member_id: int, *, session: Session
    ) -> HelpersAppPermissionDto:
        entries = await self.database_context.query_all(
            select(HelpersAppPermissionEntity).where(
                HelpersAppPermissionEntity.member_id == member_id
            ),
            async_transformer=HelpersAppPermissionDto.create,
            session=session,
        )

        if entries:
            return entries[0]

        msg = "Permission not found"
        raise ControllerNotFoundError(msg)

    async def find_all_task_categories(self) -> Sequence[HelperTaskCategoryDto]:
        """Return all helper task categories."""
        return await self.database_context.query_all(
            select(HelperTaskCategoryEntity).order_by(HelperTaskCategoryEntity.title),
            async_transformer=HelperTaskCategoryDto.create,
        )

    async def find_all_tasks(
        self, *, year: int | None = None, published: bool | None = None
    ) -> Sequence[HelperTaskDto]:
        """Return all helper tasks, optionally filtered."""
        return await self._find_tasks(year=year, task_id=None, published=published)

    async def find_task_by_id(
        self,
        task_id: int,
        *,
        published: bool | None = None,
        session: Session | None = None,
    ) -> HelperTaskDto | None:
        """Find a helper task by ID, or return None."""
        return await self._find_task_by_id(
            task_id, published=published, session=session
        )

    async def get_task_by_id(
        self,
        task_id: int,
        *,
        published: bool | None = None,
        session: Session | None = None,
    ) -> HelperTaskDto:
        """Get a helper task by ID, or raise not found."""
        task = await self.find_task_by_id(task_id, published=published, session=session)
        if task:
            return task
        msg = "Task not found"
        raise ControllerNotFoundError(msg)

    async def create_task(
        self, request: HelperTaskCreationRequestDto, user: User
    ) -> HelperTaskDto:
        """Create a new task."""
        with self.database_action(
            action="Helper Task / Create", user=user, details={"request": request}
        ) as session:
            task_entity = HelperTaskEntity(**request.model_dump())
            session.add(task_entity)
            session.commit()

            task = await HelperTaskDto.create(task_entity)
            self._logger.info("Created task: %s, user: %s", task.id, user.username)

            self._audit_log(session, user, "Helpers/Tasks/Create", {"new": task})

            return task

    async def update_task(
        self,
        task_id: int,
        request: HelperTaskUpdateRequestDto,
        user: User,
    ) -> HelperTaskDto:
        """Update an existing task."""
        with self.database_action(
            action="Helper Task / Update",
            user=user,
            details={"task_id": task_id, "request": request},
        ) as session:
            original_task = await self._get_task_by_id(task_id, session=session)

            await self._check_can_update_task(request, original_task)

            task_entity = original_task.get_entity()
            self._update_entity_from_dto(task_entity, request)
            if original_task.validated_by is not None:
                task_entity.urgent = False
            session.commit()

            updated_task = await HelperTaskDto.create(task_entity)
            self._logger.info(
                "Updated task: %s, user: %s", updated_task.id, user.username
            )

            # Calculate change
            diff = deep_diff(original_task, updated_task)

            self._audit_log(
                session,
                user,
                f"Helpers/Tasks/Update/{task_id}",
                {
                    "diff": diff,
                    "old": original_task,
                    "new": updated_task,
                    "notifySignedUpMembers": request.notify_signed_up_members,
                },
            )
            if request.notify_signed_up_members:
                self._logger.info(
                    "Notifying signed up members about the task update "
                    "(ID: %d), updated fields: %s",
                    task_id,
                    diff.keys(),
                )
                self._run_in_background(
                    self._notifications.on_update(
                        original_task, updated_task, diff, user
                    )
                )
            else:
                self._logger.info(
                    "NOT notifying signed up members about the task update "
                    "(ID: %d), updated fields: %s",
                    task_id,
                    diff.keys(),
                )

            return updated_task

    async def _check_can_update_task(
        self, request: HelperTaskUpdateRequestDto, original_task: HelperTaskDto
    ) -> None:
        anyone_signed_up = original_task.captain or original_task.helpers

        # Check: Cannot change the task year if anyone has signed up
        # Active Members change over year, but let's rather save the complicated check,
        # since this should not be a main use case
        if anyone_signed_up and original_task.year != request.year:
            msg = (
                "You cannot change the year of the task after anyone has signed up. "
                "Please create a new task instead."
            )
            raise ControllerConflictError(msg)

        if anyone_signed_up and not request.published:
            msg = "You must publish a task after anyone has signed up"
            raise ControllerConflictError(msg)

        # Check: If a captain has signed up then the new licence must be active for the
        # captain
        if (
            original_task.captain
            and request.captain_required_licence_info_id is not None
            and request.captain_required_licence_info_id
            != (
                original_task.captain_required_licence_info.id
                if original_task.captain_required_licence_info
                else None
            )
        ):
            captain_entity = original_task.captain.member.get_entity()
            if not any(
                licence_info_entity.infoid == request.captain_required_licence_info_id
                for licence_info_entity in captain_entity.active_licence_infos
            ):
                msg = (
                    "Cannot change captain required licence info because the signed "
                    "up captain does not have the newly specified licence"
                )
                raise ControllerConflictError(msg)

        # Check: Cannot set the maximum number of helpers below the number of already
        # signed up helpers
        signed_up_helper_count = len(original_task.helpers)
        if request.helper_max_count < signed_up_helper_count:
            msg = (
                "Cannot set the maximum number of helpers below the number of already "
                f"signed up helpers ({signed_up_helper_count})"
            )
            raise ControllerConflictError(msg)

    async def set_captain(
        self, task_id: int, member_id: int, user: User
    ) -> HelperTaskDto:
        """Set the captain for a task."""
        with self.database_action(
            action="Helper Task / Set Captain",
            user=user,
            details={"task_id": task_id, "member_id": member_id},
        ) as session:
            task = await self._get_task_by_id(task_id, published=True, session=session)
            await self._check_can_sign_up_as_captain(
                task=task, member_id=member_id, editor_action=True, session=session
            )

            task_entity = task.get_entity()
            task_entity.captain_id = member_id
            task_entity.captain_signed_up_at = get_now()
            session.commit()

            updated_task = await HelperTaskDto.create(task_entity)
            if not updated_task.captain:
                msg = (
                    f"Did set the captain to {member_id}, but it appears to be unset: "
                    f"{updated_task}"
                )
                raise RuntimeError(msg)

            self._logger.info(
                "Set captain for task: %s, captain: %s, user: %s",
                updated_task.id,
                updated_task.captain.member.username,
                user.username,
            )

            self._audit_log(
                session,
                user,
                f"Helpers/Tasks/SetCaptain/{task_id}/Captain/{member_id}",
            )
            self._run_in_background(
                self._notifications.on_add_helper(
                    updated_task, updated_task.captain.member, user
                )
            )

            return updated_task

    async def remove_captain(self, task_id: int, user: User) -> HelperTaskDto:
        """Remove the captain from a task."""
        with self.database_action(
            action="Helper Task / Remove Captain",
            user=user,
            details={"task_id": task_id},
        ) as session:
            original_task = await self._get_task_by_id(
                task_id, published=True, session=session
            )

            if not original_task.captain:
                msg = "Task has no captain"
                raise ControllerConflictError(msg)
            original_captain = original_task.captain.member

            task_entity = original_task.get_entity()
            task_entity.captain_id = None
            task_entity.captain_signed_up_at = None
            session.commit()

            updated_task = await HelperTaskDto.create(task_entity)
            self._logger.info(
                "Removed captain from task: %s, original captain: %s, user: %s",
                updated_task.id,
                original_captain.username,
                user.username,
            )

            self._audit_log(
                session,
                user,
                f"Helpers/Tasks/RemoveCaptain/{task_id}/Captain/{original_captain.id}",
            )
            self._run_in_background(
                self._notifications.on_remove_helper(
                    updated_task, original_captain, user
                )
            )

            return updated_task

    async def add_helper(
        self, task_id: int, member_id: int, user: User
    ) -> HelperTaskDto:
        """Add a helper to a task."""
        with self.database_action(
            action="Helper Task / Add Helper",
            user=user,
            details={"task_id": task_id, "member_id": member_id},
        ) as session:
            task = await self._get_task_by_id(task_id, published=True, session=session)
            await self._check_can_sign_up_as_helper(
                task=task, member_id=member_id, editor_action=True, session=session
            )

            helper_entity = HelperTaskHelperEntity(
                task_id=task.id, member_id=member_id, signed_up_at=get_now()
            )
            session.add(helper_entity)
            session.commit()

            updated_task = await self.get_task_by_id(
                task_id, published=True, session=session
            )
            helper = await MemberPublicInfoDto.create(
                await helper_entity.awaitable_attrs.member
            )

            self._logger.info(
                "Added helper to task: %s, helper: %s, user: %s",
                updated_task.id,
                helper.username,
                user.username,
            )
            self._audit_log(
                session,
                user,
                f"Helpers/Tasks/AddHelper/{task_id}/Helper/{member_id}",
            )
            self._run_in_background(
                self._notifications.on_add_helper(updated_task, helper, user)
            )

            return updated_task

    async def remove_helper(
        self, task_id: int, member_id: int, user: User
    ) -> HelperTaskDto:
        """Remove a helper from a task."""
        with self.database_action(
            action="Helper Task / Remove Helper",
            user=user,
            details={"task_id": task_id, "member_id": member_id},
        ) as session:
            original_task = await self._get_task_by_id(
                task_id, published=True, session=session
            )
            task_entity = original_task.get_entity()

            helper_entity_to_remove = next(
                (
                    helper_entity
                    for helper_entity in await task_entity.awaitable_attrs.helpers
                    if helper_entity.member_id == member_id
                ),
                None,
            )
            if not helper_entity_to_remove:
                msg = "Helper is not on the task"
                raise ControllerNotFoundError(msg)

            helper_to_remove = await MemberPublicInfoDto.create(
                await helper_entity_to_remove.awaitable_attrs.member
            )

            session.delete(helper_entity_to_remove)
            session.commit()

            updated_task = await HelperTaskDto.create(task_entity)
            self._logger.info(
                "Removed helper from task: %s, helper: %s, user: %s",
                updated_task.id,
                helper_to_remove.username,
                user.username,
            )

            self._audit_log(
                session,
                user,
                f"Helpers/Tasks/RemoveHelper/{task_id}/Helper/{member_id}",
            )
            self._run_in_background(
                self._notifications.on_remove_helper(
                    updated_task, helper_to_remove, user
                )
            )

            return updated_task

    async def sign_up_as_captain(self, task_id: int, user: User) -> HelperTaskDto:
        """Sign up the current user as captain for a task."""
        with self.database_action(
            action="Helper Task / Sign Up As Captain",
            user=user,
            details={"task_id": task_id},
        ) as session:
            task = await self._get_task_by_id(task_id, published=True, session=session)

            await self._check_can_sign_up_as_captain(
                task=task,
                member_id=user.member_id,
                editor_action=False,
                session=session,
            )
            task_entity = task.get_entity()
            task_entity.captain_id = user.member_id
            task_entity.captain_signed_up_at = get_now()
            session.commit()

            updated_task = await HelperTaskDto.create(task_entity)
            self._logger.info(
                "Signed up as captain for task: %s, user: %s",
                updated_task.id,
                user.username,
            )

            self._audit_log(session, user, f"Helpers/Tasks/SignUpAsCaptain/{task_id}")
            self._run_in_background(self._notifications.on_sign_up(updated_task, user))

            return updated_task

    async def sign_up_as_helper(self, task_id: int, user: User) -> HelperTaskDto:
        """Sign up the current user as helper for a task."""
        with self.database_action(
            action="Helper Task / Sign Up As Helper",
            user=user,
            details={"task_id": task_id},
        ) as session:
            task = await self.get_task_by_id(task_id, published=True, session=session)

            await self._check_can_sign_up_as_helper(
                task=task,
                member_id=user.member_id,
                editor_action=False,
                session=session,
            )

            helper_entity = HelperTaskHelperEntity(
                task_id=task.id, member_id=user.member_id, signed_up_at=get_now()
            )
            session.add(helper_entity)
            session.commit()

            updated_task = await self.get_task_by_id(
                task_id, published=True, session=session
            )
            self._logger.info(
                "Signed up as helper for task: %s, user: %s",
                updated_task.id,
                user.username,
            )

            self._audit_log(session, user, f"Helpers/Tasks/SignUpAsHelper/{task_id}")
            self._run_in_background(self._notifications.on_sign_up(updated_task, user))

            return updated_task

    async def mark_as_done(
        self, task_id: int, request: HelperTaskMarkAsDoneRequestDto, user: User
    ) -> HelperTaskDto:
        """Mark a task as done."""
        with self.database_action(
            action="Helper Task / Mark As Done",
            user=user,
            details={"task_id": task_id, "request": request},
        ) as session:
            task = await self._get_task_by_id(task_id, published=True, session=session)

            if task.state != HelperTaskState.PENDING:
                msg = "Task already marked as done"
                raise ControllerConflictError(msg)
            if self._starts_in_the_future(task):
                msg = "Cannot mark a task as done before it starts"
                raise ControllerConflictError(msg)

            task_entity = task.get_entity()
            task_entity.marked_as_done_at = get_now()
            task_entity.marked_as_done_by_id = user.member_id
            task_entity.marked_as_done_comment = request.comment
            session.commit()

            updated_task = await HelperTaskDto.create(task_entity)
            self._logger.info(
                "Marked task as done: %s, user: %s", updated_task.id, user.username
            )

            self._audit_log(session, user, f"Helpers/Tasks/MarkAsDone/{task_id}")
            self._run_in_background(
                self._notifications.on_mark_as_done(updated_task, user)
            )

            return updated_task

    async def validate(
        self, task_id: int, request: HelperTaskValidationRequestDto, user: User
    ) -> HelperTaskDto:
        """Validate a task."""
        with self.database_action(
            action="Helper Task / Validate",
            user=user,
            details={"task_id": task_id, "request": request},
        ) as session:
            task = await self._get_task_by_id(task_id, published=True, session=session)

            if task.state == HelperTaskState.VALIDATED:
                msg = "Task already validated"
                raise ControllerConflictError(msg)
            if self._starts_in_the_future(task):
                msg = "Cannot validate a task before it starts"
                raise ControllerConflictError(msg)

            task_entity = task.get_entity()
            now = get_now()

            if not task_entity.marked_as_done_at:
                task_entity.marked_as_done_at = now
                task_entity.marked_as_done_by_id = user.member_id

            task_entity.validated_at = now
            task_entity.validated_by_id = user.member_id
            task_entity.validation_comment = request.comment
            session.commit()

            updated_task = await HelperTaskDto.create(task_entity)
            self._logger.info(
                "Validated task: %s, user: %s",
                updated_task.id,
                user.username,
            )

            self._audit_log(
                session,
                user,
                f"Helpers/Tasks/Validate/{task_id}",
            )
            self._run_in_background(self._notifications.on_validate(updated_task, user))

            # Do it before the requests finishes, so the next request gets the updated
            # state
            await self._unset_urgent_for_validated_tasks(user=user, session=session)

            return updated_task

    async def _unset_urgent_for_validated_tasks(
        self, *, user: User, session: Session
    ) -> None:
        validated_urgent_tasks = (
            session.scalars(
                select(HelperTaskEntity).where(
                    HelperTaskEntity.validated_by_id.is_not(None),
                    # Need == 1 instead of True for Oracle
                    HelperTaskEntity.urgent == 1,
                )
            )
            .unique()
            .all()
        )

        for task in validated_urgent_tasks:
            task.urgent = False

        session.commit()

        self._logger.info(
            "Unset urgent for %d validated task(s)", len(validated_urgent_tasks)
        )

        for task in validated_urgent_tasks:
            self._audit_log(
                session, user, f"Helpers/Tasks/UnsetUrgentForValidatedTask/{task.id}"
            )

    async def send_daily_reminders(self) -> None:
        """Send daily reminders to task participants.

        Never send reminders for:
        - Tasks that are started and are not yet finished (especially multi-day shifts)
        - Tasks that are validated

        For upcoming tasks send reminders:
        - 2 weeks before
        - 3 days before
        - the day of the task

        Overdue tasks (not validated tasks in the past; to speed up task validation):
        - Reminders are sent per contact, not per task
        - Shifts (and invalid timing):
            - A reminder is sent every day to the contact 1 week after the shift is
              finished.
            - The delay gives a window for shift organisers to validate tasks (as
              shifts "just happen" anyway").
            - No immediate pressure on shift organisers, especially as the shifts often
              happen in batches (regattas, surveillance etc.)
        - Deadline tasks:
            - A reminder is sent every day to the contact the if the deadline has
              expired.
            - Deadline tasks are usually one-off maintenance tasks and in the past the
              experience was that they are often forgotten
            - After the deadline expires, it is either done (and should have been
              validated) or the deadline should be extended

        Notes:
        - Also send reminders for past years (avoid hanging tasks; tasks can have a
          deadline on 31 December)
        - Also send reminders for unpublished tasks (tasks with helpers should not be
          unpublished)

        """
        if not CONFIG.emails_enabled(self._logger):
            return

        def debug(task: HelperTaskDto, message: str) -> None:
            self._logger.debug(
                "Task %s (id=%d, starts_at=%s, ends_at=%s, deadline=%s): %s",
                task.title,
                task.id,
                task.starts_at,
                task.ends_at,
                task.deadline,
                message,
            )

        with self.database_action(
            action="Helpers / Send Daily Reminders",
            user=None,
            details=None,
        ) as session:
            # Query all relevant tasks
            now = get_now()

            # "Round" to the start of the day
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            one_week_ago = now - timedelta(days=7)

            # Using ranges to avoid persisting notification time in the database
            due_in_2_weeks_start = today_start + timedelta(days=14)
            due_in_2_weeks_end = today_end + timedelta(days=14)
            due_in_3_days_start = today_start + timedelta(days=3)
            due_in_3_days_end = today_end + timedelta(days=3)

            entity_timing_fields = [
                HelperTaskEntity.starts_at,
                HelperTaskEntity.ends_at,
                HelperTaskEntity.deadline,
            ]

            where = and_(
                HelperTaskEntity.validated_by_id.is_(None),
                or_(
                    # Note: BETWEEN is inclusive (uses <=, not <)
                    *[
                        field.between(due_in_2_weeks_start, due_in_2_weeks_end)
                        for field in entity_timing_fields
                    ],
                    *[
                        field.between(due_in_3_days_start, due_in_3_days_end)
                        for field in entity_timing_fields
                    ],
                    # Today or overdue
                    *[field <= today_end for field in entity_timing_fields],
                ),
            )

            tasks = await self._find_tasks(
                year=None,
                task_id=None,
                published=None,
                where=where,
                session=session,
            )

            # Split tasks how should be the reminders sent
            upcoming_tasks: list[HelperTaskDto] = []
            overdue_tasks: list[HelperTaskDto] = []

            for task in tasks:
                timings = [
                    t
                    for t in [task.starts_at, task.ends_at, task.deadline]
                    if t is not None
                ]

                if not timings:
                    # (Invalid) task has no timing information: no reminder
                    self._logger.warning("Task %s has no timing information", task.id)
                    continue

                timing_earliest = min(timings)
                timing_latest = max(timings)

                # Note that here we are actually comparing to now, not to the start
                # of the day
                task_upcoming = now < timing_earliest
                task_due = timing_latest < now

                if not task_upcoming and not task_due:
                    # Ongoing tasks: no reminder
                    debug(task, "Ongoing task")
                    continue

                if (
                    task_due
                    and task.type == HelperTaskType.SHIFT
                    and one_week_ago < timing_latest
                ):
                    # Shifts: skip reminder if timing_latest is more recent (greater)
                    # than one week ago
                    debug(task, "Overdue shift in grace period")
                    continue

                if task_due:
                    debug(task, "Overdue task")
                    overdue_tasks.append(task)
                else:
                    debug(task, "Upcoming task")
                    upcoming_tasks.append(task)

        self._logger.info(
            "Identified %d upcoming tasks and %d overdue tasks",
            len(upcoming_tasks),
            len(overdue_tasks),
        )
        await self._notifications.send_reminders(upcoming_tasks, overdue_tasks)

    async def _find_tasks(
        self,
        *,
        year: int | None,
        task_id: int | None,
        published: bool | None,
        where: ColumnElement[bool] | None = None,
        session: Session | None = None,
    ) -> Sequence[HelperTaskDto]:
        query = select(HelperTaskEntity)

        exclude_large_fields: bool = task_id is None

        if exclude_large_fields:
            query = query.options(
                defer(HelperTaskEntity.long_description, raiseload=True),
                defer(HelperTaskEntity.marked_as_done_comment, raiseload=True),
                defer(HelperTaskEntity.validation_comment, raiseload=True),
            )

        if year is not None:
            query = query.where(
                func.coalesce(
                    HelperTaskEntity.starts_at, HelperTaskEntity.deadline
                ).between(
                    datetime(year, 1, 1, 0, 0, 0, 0),  # noqa: DTZ001
                    datetime(year, 12, 31, 23, 59, 59, 0),  # noqa: DTZ001
                )
            )
        if task_id is not None:
            query = query.where(HelperTaskEntity.id == task_id)
        if published is not None:
            query = query.where(HelperTaskEntity.published == published)
        if where is not None:
            query = query.where(where)

        query = query.order_by(
            HelperTaskEntity.urgent.desc(),
            func.coalesce(HelperTaskEntity.starts_at, HelperTaskEntity.deadline).asc(),
        )

        return await self.database_context.query_all(
            query,
            async_transformer=(
                HelperTaskDto.create_without_large_fields
                if exclude_large_fields
                else HelperTaskDto.create
            ),
            unique=True,
            session=session,
        )

    async def _find_task_by_id(
        self,
        task_id: int,
        *,
        published: bool | None,
        session: Session | None = None,
    ) -> HelperTaskDto | None:
        tasks = await self._find_tasks(
            year=None, task_id=task_id, published=published, session=session
        )
        return tasks[0] if tasks else None

    async def _get_task_by_id(
        self,
        task_id: int,
        *,
        published: bool | None = None,
        session: Session | None = None,
    ) -> HelperTaskDto:
        task = await self._find_task_by_id(
            task_id, published=published, session=session
        )
        if task:
            return task
        raise ControllerNotFoundError(
            "Task not found or not published" if published else "Task not found"
        )

    async def _check_can_sign_up_as_captain(
        self,
        *,
        task: HelperTaskDto,
        member_id: int,
        editor_action: bool,
        session: Session,
    ) -> None:
        await self._check_can_sign_up(
            task=task, member_id=member_id, editor_action=editor_action
        )

        if task.captain:
            msg = "Task already has a captain"
            raise ControllerConflictError(msg)

        if task.captain_required_licence_info:
            has_licence = (
                session.scalar(
                    select(LicenceEntity).where(
                        LicenceEntity.member_id == member_id,
                        LicenceEntity.licence_id
                        == task.captain_required_licence_info.id,
                        LicenceEntity.status > 0,
                    )
                )
                is not None
            )

            if not has_licence:
                msg = (
                    "Task captain needs licence:"
                    f" {task.captain_required_licence_info.licence}"
                )
                raise ControllerConflictError(msg)

    async def _check_can_sign_up_as_helper(
        self,
        *,
        task: HelperTaskDto,
        member_id: int,
        editor_action: bool,
        session: Session,
    ) -> None:
        await self._check_can_sign_up(
            task=task, member_id=member_id, editor_action=editor_action
        )

        if len(task.helpers) >= task.helper_max_count:
            msg = "Task helper limit reached"
            raise ControllerConflictError(msg)

        if not editor_action:
            # Before the sign-up limit date, a member can only be helper on maximum one
            # surveillance shift:
            # 1. This allows more members completing one surveillance shift in the
            #    beginning of the season
            # 2. Members who want to do all their tasks early can still do maintenance
            #    tasks

            surveillance_task = task.category.title.lower().startswith(
                SURVEILLANCE_TASK_PREFIX.lower()
            )
            limit_date = date(
                task.year,
                SURVEILLANCE_SIGN_UP_LIMIT_MONTH,
                SURVEILLANCE_SIGN_UP_LIMIT_DAY,
            )

            if surveillance_task and get_now().date() < limit_date:
                # Check if the member has signed up for any other surveillance shift
                # before the limit date
                other_surveillance_tasks = await self._find_tasks(
                    year=task.year,
                    task_id=None,
                    published=None,
                    where=and_(
                        HelperTaskEntity.category.has(
                            HelperTaskCategoryEntity.title.istartswith(
                                SURVEILLANCE_TASK_PREFIX
                            )
                        ),
                        HelperTaskEntity.helpers.any(
                            HelperTaskHelperEntity.member_id == member_id
                        ),
                    ),
                    session=session,
                )
                if other_surveillance_tasks:
                    msg = (
                        "You cannot sign up for multiple surveillance shifts "
                        f"before {SURVEILLANCE_SIGN_UP_LIMIT_STR} - but you "
                        f"can still sign up for maintenance and other tasks! 😉"
                    )
                    raise ControllerConflictError(msg)

    async def _check_can_sign_up(
        self, *, task: HelperTaskDto, member_id: int, editor_action: bool
    ) -> None:
        if not task.published:
            msg = "Cannot sign up for an unpublished task"
            raise ControllerConflictError(msg)

        if not editor_action:
            if task.state == HelperTaskState.DONE:
                msg = "Cannot sign up for a task marked as done"
                raise ControllerConflictError(msg)
            if task.state == HelperTaskState.VALIDATED:
                msg = "Cannot sign up for a validated task"
                raise ControllerConflictError(msg)

            now = get_now()
            if (task.starts_at and task.starts_at < now) or (
                task.deadline and task.deadline < now
            ):
                msg = "Cannot sign up for a task in the past"
                raise ControllerConflictError(msg)

        if task.captain and task.captain.member.id == member_id:
            msg = "Already signed up as captain"
            raise ControllerConflictError(msg)
        if any(helper.member.id == member_id for helper in task.helpers):
            msg = "Already signed up as helper"
            raise ControllerConflictError(msg)

    def _starts_in_the_future(self, task: HelperTaskDto) -> bool:
        return bool(task.starts_at and task.starts_at > get_now())

    async def find_attachments_for_task(
        self, task_id: int
    ) -> Sequence[AttachmentMetadataDto]:
        """Return attachment metadata for a helper task (no BLOB content)."""
        return await self.database_context.query_all(
            select(AttachmentEntity)
            .options(*_ATTACHMENT_WITHOUT_BLOBS)
            .where(
                AttachmentEntity.ref_id == task_id,
                AttachmentEntity.ref_class_id == ATTACHMENT_REF_CLASS_ID,
            )
            .order_by(AttachmentEntity.created, AttachmentEntity.id),
            async_transformer=AttachmentMetadataDto.create,
        )

    async def get_attachment_with_content(
        self, task_id: int, attachment_id: int
    ) -> AttachmentEntity:
        """Return a single attachment with content for download."""
        with self.database_context.session() as session:
            entity = session.scalars(
                select(AttachmentEntity)
                .options(defer(AttachmentEntity.thumbnail))
                .where(
                    AttachmentEntity.id == attachment_id,
                    AttachmentEntity.ref_id == task_id,
                    AttachmentEntity.ref_class_id == ATTACHMENT_REF_CLASS_ID,
                )
            ).first()
            if entity is None:
                msg = "Attachment not found"
                raise ControllerNotFoundError(msg)
            return entity

    async def get_attachment_owner_id(self, task_id: int, attachment_id: int) -> int:
        """Return the owner_id of an attachment (without loading BLOBs)."""
        with self.database_context.session() as session:
            owner_id = session.execute(
                select(AttachmentEntity.owner_id).where(
                    AttachmentEntity.id == attachment_id,
                    AttachmentEntity.ref_id == task_id,
                    AttachmentEntity.ref_class_id == ATTACHMENT_REF_CLASS_ID,
                )
            ).scalar_one_or_none()
            if owner_id is None:
                msg = "Attachment not found"
                raise ControllerNotFoundError(msg)
            return owner_id

    async def upload_attachment(
        self,
        task_id: int,
        file: UploadFile,
        description: str | None,
        user: User,
    ) -> AttachmentMetadataDto:
        """Upload an attachment for a helper task."""
        if not file.filename:
            msg = "Filename is required"
            raise ControllerBadRequestError(msg)
        filename = sanitise_filename(file.filename)
        try:
            mime_type = resolve_attachment_mime_type(filename)
        except ValueError as exc:
            msg = f"File type not allowed: {filename}"
            raise ControllerBadRequestError(msg) from exc

        if description and len(description) > ATTACHMENT_MAX_DESCRIPTION_LENGTH:
            msg = (
                "Description too long "
                f"(max {ATTACHMENT_MAX_DESCRIPTION_LENGTH} characters)"
            )
            raise ControllerBadRequestError(msg)

        content = await self._read_upload_with_size_limit(
            file=file,
            max_size_bytes=ATTACHMENT_MAX_FILE_SIZE_BYTES,
        )

        with self.database_action(
            action="Helpers / Upload Attachment",
            user=user,
            details={"task_id": task_id, "filename": filename},
        ) as session:
            # Lock the parent task row so concurrent uploads for the same task serialise
            # on this lock, preventing the limit from being exceeded.
            # We lock the task row (which always exists) rather than attachment rows,
            # because FOR UPDATE on an empty result set acquires no locks.
            session.execute(
                select(HelperTaskEntity.id)
                .where(HelperTaskEntity.id == task_id)
                .with_for_update()
            ).one()
            count = session.execute(
                select(func.count()).where(
                    AttachmentEntity.ref_id == task_id,
                    AttachmentEntity.ref_class_id == ATTACHMENT_REF_CLASS_ID,
                )
            ).scalar_one()
            if count >= ATTACHMENT_MAX_PER_TASK:
                msg = (
                    f"Task already has {ATTACHMENT_MAX_PER_TASK} attachments (maximum)"
                )
                raise ControllerBadRequestError(msg)

            entity = AttachmentEntity(
                name=filename,
                content=bytes(content),
                description=description,
                mime_type=mime_type,
                size_bytes=len(content),
                owner_id=user.member_id,
                created=get_now(),
                thumbnail=None,
                ref_id=task_id,
                ref_class_id=ATTACHMENT_REF_CLASS_ID,
            )
            session.add(entity)
            session.commit()
            session.refresh(entity, ["id"])

            self._audit_log(
                session,
                user,
                f"Helpers/Tasks/UploadAttachment/{task_id}",
                {
                    "attachment_id": entity.id,
                    "filename": filename,
                    "description": description,
                    "mime_type": mime_type,
                    "size_bytes": len(content),
                },
            )

            result = await AttachmentMetadataDto.create(entity)

        task = await self.get_task_by_id(task_id, published=None)
        self._run_in_background(
            self._notifications.on_attachment_upload(task, filename, user)
        )

        return result

    async def delete_attachment(
        self, task_id: int, attachment_id: int, user: User
    ) -> None:
        """Delete an attachment."""
        with self.database_action(
            action="Helpers / Delete Attachment",
            user=user,
            details={"task_id": task_id, "attachment_id": attachment_id},
        ) as session:
            entity = session.scalars(
                select(AttachmentEntity)
                .options(
                    defer(AttachmentEntity.content),
                    defer(AttachmentEntity.thumbnail),
                )
                .where(
                    AttachmentEntity.id == attachment_id,
                    AttachmentEntity.ref_id == task_id,
                    AttachmentEntity.ref_class_id == ATTACHMENT_REF_CLASS_ID,
                )
            ).first()
            if entity is None:
                msg = "Attachment not found"
                raise ControllerNotFoundError(msg)

            deleted_filename = entity.name
            audit_data = {
                "attachment_id": attachment_id,
                "filename": entity.name,
                "description": entity.description,
                "mime_type": entity.mime_type,
                "size_bytes": entity.size_bytes,
            }

            session.delete(entity)
            session.commit()

            self._audit_log(
                session,
                user,
                f"Helpers/Tasks/DeleteAttachment/{task_id}",
                audit_data,
            )

        task = await self.get_task_by_id(task_id, published=None)
        self._run_in_background(
            self._notifications.on_attachment_delete(task, deleted_filename, user)
        )

    async def transcode_image_to_jpeg(
        self,
        file: UploadFile,
    ) -> bytes:
        """Transcode an uploaded HEIC/HEIF image to JPEG bytes."""
        if not file.filename:
            msg = "Filename is required"
            raise ControllerBadRequestError(msg)

        filename = sanitise_filename(file.filename)
        ext = filename[filename.rfind(".") :].lower() if "." in filename else ""
        if ext not in HEIC_HEIF_EXTENSIONS:
            msg = f"Only HEIC/HEIF files can be transcoded, not {file.filename}"
            raise ControllerBadRequestError(msg)

        content = await self._read_upload_with_size_limit(
            file=file,
            max_size_bytes=ATTACHMENT_MAX_FILE_SIZE_BYTES,
        )

        try:
            return convert_heic_to_jpeg(bytes(content))
        except ValueError as exc:
            msg = f"Invalid HEIC/HEIF image: {file.filename}"
            raise ControllerBadRequestError(msg) from exc
