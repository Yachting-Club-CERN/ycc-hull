"""
Helpers API endpoints.
"""
from collections.abc import Sequence
from typing import Optional

from fastapi import APIRouter, Depends
from ycc_hull.api.errors import create_http_exception_403

from ycc_hull.auth import User, auth
from ycc_hull.controllers.helpers_controller import HelpersController
from ycc_hull.models.helpers_dtos import (
    HelperTaskCategoryDto,
    HelperTaskCreationRequestDto,
    HelperTaskDto,
)

api_helpers = APIRouter(dependencies=[Depends(auth)])
controller = HelpersController()


def _published(user: User) -> Optional[bool]:
    return None if user.helpers_app_admin_or_editor else True


@api_helpers.get("/api/v0/helpers/task-categories")
async def helper_task_categories_get() -> Sequence[HelperTaskCategoryDto]:
    return await controller.find_all_task_categories()


@api_helpers.get("/api/v0/helpers/tasks")
async def helper_tasks_get(user: User = Depends(auth)) -> Sequence[HelperTaskDto]:
    return await controller.find_all_tasks(published=_published(user))


@api_helpers.get("/api/v0/helpers/tasks/{task_id}")
async def helper_tasks_get_by_id(
    task_id: int, user: User = Depends(auth)
) -> HelperTaskDto:
    return await controller.get_task_by_id(task_id, published=_published(user))


@api_helpers.post("/api/v0/helpers/tasks")
async def helper_tasks_create(
    task: HelperTaskCreationRequestDto, user: User = Depends(auth)
) -> HelperTaskDto:
    if not user.helpers_app_admin and not user.helpers_app_editor:
        raise create_http_exception_403(
            "You do not have permission to create helper tasks"
        )
    if user.helpers_app_editor and not task.contact_id == user.member_id:
        raise create_http_exception_403(
            "You have to be the contact for the tasks you create"
        )

    return await controller.create_task(task, user)


# TODO WIP
# @api.helpers.put("/api/v0/helpers/tasks/{task_id}")
# async def helper_tasks_update(
#     task_id: int, task: HelperTaskDto, user: User = Depends(auth)
# ) -> HelperTaskDto:
#     if not user.helpers_app_admin and not user.helpers_app_editor:
#         raise create_http_exception_403(
#             "You do not have permission to update helper tasks"
#         )

#     if (
#         user.helpers_app_editor
#         and controller.get_task_by_id(task_id, published=None).contact.id
#         != user.member_id
#     ):
#         raise create_http_exception_403(
#             "You do not have permission to update this helper task"
#         )

#     task = await controller.update ??? task(task, user)
#     return task


@api_helpers.post("/api/v0/helpers/tasks/{task_id}/subscribe-as-captain")
async def helper_tasks_subscribe_as_captain(
    task_id: int, user: User = Depends(auth)
) -> HelperTaskDto:
    await controller.subscribe_as_captain(task_id, user)
    return await controller.get_task_by_id(task_id, published=True)


@api_helpers.post("/api/v0/helpers/tasks/{task_id}/subscribe-as-helper")
async def helper_tasks_subscribe_as_helper(
    task_id: int, user: User = Depends(auth)
) -> HelperTaskDto:
    await controller.subscribe_as_helper(task_id, user)
    return await controller.get_task_by_id(task_id, published=True)
