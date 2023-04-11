"""
Helper API endpoints.
"""
from typing import Sequence

from fastapi import APIRouter, Depends

from ycc_hull.auth import AuthInfo, auth
from ycc_hull.controllers.helpers_controller import HelpersController
from ycc_hull.models.helpers_dtos import HelperTaskCategoryDto, HelperTaskDto

api_helpers = APIRouter(dependencies=[Depends(auth)])


@api_helpers.get("/api/v0/helpers/task-categories")
async def helper_task_categories_get() -> Sequence[HelperTaskCategoryDto]:
    return await HelpersController.find_all_task_categories()


@api_helpers.get("/api/v0/helpers/tasks")
async def helper_tasks_get() -> Sequence[HelperTaskDto]:
    return await HelpersController.find_all_tasks(published=True)


@api_helpers.get("/api/v0/helpers/tasks/{task_id}")
async def helper_tasks_get_by_id(task_id: int) -> HelperTaskDto:
    return await HelpersController.get_task_by_id(task_id, published=True)


@api_helpers.post("/api/v0/helpers/tasks/{task_id}/subscribe-as-captain")
async def helper_tasks_subscribe_as_captain(
    task_id: int, auth_info: AuthInfo = Depends(auth)
) -> HelperTaskDto:
    await HelpersController.subscribe_as_captain(
        task_id, auth_info.member_id, auth_info.roles
    )
    return await HelpersController.get_task_by_id(task_id, published=True)


@api_helpers.post("/api/v0/helpers/tasks/{task_id}/subscribe-as-helper")
async def helper_tasks_subscribe_as_helper(
    task_id: int, auth_info: AuthInfo = Depends(auth)
) -> HelperTaskDto:
    await HelpersController.subscribe_as_helper(task_id, auth_info.member_id)
    return await HelpersController.get_task_by_id(task_id, published=True)
