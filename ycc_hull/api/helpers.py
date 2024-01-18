"""
Helpers API endpoints.
"""
from collections.abc import Sequence

from fastapi import APIRouter, Depends
from ycc_hull.api.errors import create_http_exception_403

from ycc_hull.auth import User, auth
from ycc_hull.controllers.helpers_controller import HelpersController
from ycc_hull.models.helpers_dtos import (
    HelperTaskCategoryDto,
    HelperTaskMutationRequestDto,
    HelperTaskDto,
)

api_helpers = APIRouter(dependencies=[Depends(auth)])
controller = HelpersController()


def _published(user: User) -> bool | None:
    return None if user.helpers_app_admin_or_editor else True


@api_helpers.get("/api/v1/helpers/task-categories")
async def helper_task_categories_get() -> Sequence[HelperTaskCategoryDto]:
    return await controller.find_all_task_categories()


@api_helpers.get("/api/v1/helpers/tasks")
async def helper_tasks_get(user: User = Depends(auth)) -> Sequence[HelperTaskDto]:
    return await controller.find_all_tasks(published=_published(user))


@api_helpers.get("/api/v1/helpers/tasks/{task_id}")
async def helper_tasks_get_by_id(
    task_id: int, user: User = Depends(auth)
) -> HelperTaskDto:
    return await controller.get_task_by_id(task_id, published=_published(user))


@api_helpers.post("/api/v1/helpers/tasks")
async def helper_tasks_create(
    task_mutation_request: HelperTaskMutationRequestDto, user: User = Depends(auth)
) -> HelperTaskDto:
    if not user.helpers_app_admin and not user.helpers_app_editor:
        raise create_http_exception_403(
            "You do not have permission to create helper tasks"
        )
    if (
        not user.helpers_app_admin
        and task_mutation_request.contact_id != user.member_id
    ):
        raise create_http_exception_403(
            "You have to be the contact for the tasks you create"
        )

    return await controller.create_task(task_mutation_request, user)


@api_helpers.put("/api/v1/helpers/tasks/{task_id}")
async def helper_tasks_update(
    task_id: int,
    task_mutation_request: HelperTaskMutationRequestDto,
    user: User = Depends(auth),
) -> HelperTaskDto:
    if not user.helpers_app_admin and not user.helpers_app_editor:
        raise create_http_exception_403(
            "You do not have permission to update helper tasks"
        )

    existing_task = await helper_tasks_get_by_id(task_id, user)

    if user.helpers_app_editor and (
        task_mutation_request.contact_id != user.member_id
        or existing_task.contact.id != user.member_id
    ):
        raise create_http_exception_403(
            "You have to be the contact for the tasks you update"
        )

    return await controller.update_task(task_id, task_mutation_request, user)


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
