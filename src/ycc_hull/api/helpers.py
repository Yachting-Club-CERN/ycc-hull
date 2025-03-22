"""
Helpers API endpoints.
"""

from collections.abc import Sequence
from datetime import date

from fastapi import APIRouter, Depends

from ycc_hull.api.errors import create_http_exception_403
from ycc_hull.auth import User, auth
from ycc_hull.controllers.helpers_controller import HelpersController
from ycc_hull.models.helpers_dtos import (HelperTaskCategoryDto, HelperTaskDto,
                                          HelperTaskMarkAsDoneRequestDto,
                                          HelperTaskMutationRequestDto,
                                          HelperTaskValidationRequestDto)

api_helpers = APIRouter(dependencies=[Depends(auth)])
controller = HelpersController()


@api_helpers.get("/api/v1/helpers/task-categories")
async def helper_task_categories_get() -> Sequence[HelperTaskCategoryDto]:
    return await controller.find_all_task_categories()


@api_helpers.get("/api/v1/helpers/tasks")
async def helper_tasks_get(
    year: int | None = None, user: User = Depends(auth)
) -> Sequence[HelperTaskDto]:
    if not _can_access_year(year, user):
        error_message = (
            f"You do not have permission to list tasks for {year}"
            if year
            else "You do not have permission to list all tasks"
        )
        raise create_http_exception_403(error_message)

    return await controller.find_all_tasks(year=year, published=_published(user))


@api_helpers.get("/api/v1/helpers/tasks/{task_id}")
async def helper_tasks_get_by_id(
    task_id: int, user: User = Depends(auth)
) -> HelperTaskDto:
    task = await controller.get_task_by_id(task_id, published=_published(user))

    if not _can_access_year(task.year, user):
        raise create_http_exception_403("You do not have permission to view this task")

    return task


@api_helpers.post("/api/v1/helpers/tasks")
async def helper_tasks_create(
    request: HelperTaskMutationRequestDto, user: User = Depends(auth)
) -> HelperTaskDto:
    if not user.helpers_app_admin and not user.helpers_app_editor:
        raise create_http_exception_403(
            "You do not have permission to create helper tasks"
        )
    if not user.helpers_app_admin and request.contact_id != user.member_id:
        raise create_http_exception_403(
            "You have to be the contact for the tasks you create"
        )

    return await controller.create_task(request, user)


@api_helpers.put("/api/v1/helpers/tasks/{task_id}")
async def helper_tasks_update(
    task_id: int,
    request: HelperTaskMutationRequestDto,
    user: User = Depends(auth),
) -> HelperTaskDto:
    if not user.helpers_app_admin and not user.helpers_app_editor:
        raise create_http_exception_403(
            "You do not have permission to update helper tasks"
        )

    existing_task = await helper_tasks_get_by_id(task_id, user)

    if user.helpers_app_editor and (
        request.contact_id != user.member_id
        or existing_task.contact.id != user.member_id
    ):
        raise create_http_exception_403(
            "You have to be the contact for the tasks you update"
        )

    return await controller.update_task(task_id, request, user)


@api_helpers.post("/api/v1/helpers/tasks/{task_id}/sign-up-as-captain")
async def helper_tasks_sign_up_as_captain(
    task_id: int, user: User = Depends(auth)
) -> HelperTaskDto:
    await controller.sign_up_as_captain(task_id, user)
    return await controller.get_task_by_id(task_id, published=True)


@api_helpers.post("/api/v1/helpers/tasks/{task_id}/sign-up-as-helper")
async def helper_tasks_sign_up_as_helper(
    task_id: int, user: User = Depends(auth)
) -> HelperTaskDto:
    await controller.sign_up_as_helper(task_id, user)
    return await controller.get_task_by_id(task_id, published=True)


@api_helpers.post("/api/v1/helpers/tasks/{task_id}/mark-as-done")
async def helper_tasks_mark_as_done(
    task_id: int, request: HelperTaskMarkAsDoneRequestDto, user: User = Depends(auth)
) -> HelperTaskDto:
    if not user.helpers_app_admin:
        task = await helper_tasks_get_by_id(task_id, user)
        if not (
            task.contact.id == user.member_id
            or (task.captain and task.captain.member.id == user.member_id)
        ):
            raise create_http_exception_403(
                "You do not have permission to mark this task as done"
            )

    await controller.mark_as_done(task_id, request, user)
    return await controller.get_task_by_id(task_id, published=True)


@api_helpers.post("/api/v1/helpers/tasks/{task_id}/validate")
async def helper_tasks_validate(
    task_id: int, request: HelperTaskValidationRequestDto, user: User = Depends(auth)
) -> HelperTaskDto:
    if not user.helpers_app_admin:
        task = await helper_tasks_get_by_id(task_id, user)
        if task.contact.id != user.member_id:
            raise create_http_exception_403(
                "You do not have permission to validate this task"
            )

    await controller.validate(task_id, request, user)
    return await controller.get_task_by_id(task_id, published=True)


def _published(user: User) -> bool | None:
    return None if user.helpers_app_admin_or_editor else True


def _can_access_year(year: int | None, user: User) -> bool:
    current_year = date.today().year

    return (
        year == current_year
        or user.admin
        or user.committee_member
        or user.helpers_app_admin
        or user.helpers_app_editor
    )
