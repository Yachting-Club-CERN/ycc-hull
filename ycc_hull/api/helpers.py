"""
Helper API endpoints.
"""
from typing import Optional, Sequence

from fastapi import APIRouter, Depends, HTTPException
from ycc_hull.auth import AuthInfo, auth
from ycc_hull.controllers.helpers_controller import HelpersController

from ycc_hull.error import raise_401
from ycc_hull.models.helpers_dtos import (
    HelperTaskCategoryDto,
    HelperTaskDto,
)

api_helpers = APIRouter(dependencies=[Depends(auth)])


@api_helpers.get("/api/v0/helpers/task-categories")
async def helper_task_categories_get() -> Sequence[HelperTaskCategoryDto]:
    return await HelpersController.find_all_task_categories()


@api_helpers.get("/api/v0/helpers/tasks")
async def helper_tasks_get() -> Sequence[HelperTaskDto]:
    return await HelpersController.find_all_tasks()
