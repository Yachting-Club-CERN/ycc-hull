"""
Helpers API endpoints.
"""

from collections.abc import Sequence
from datetime import date

from fastapi import APIRouter, Depends, Response, status

from ycc_hull.api.errors import create_http_exception_403
from ycc_hull.app_controllers import get_helpers_controller
from ycc_hull.auth import User, auth
from ycc_hull.controllers.helpers_controller import HelpersController
from ycc_hull.models.helpers_dtos import (
    HelpersAppPermissionDto,
    HelpersAppPermissionGrantRequestDto,
    HelpersAppPermissionUpdateRequestDto,
    HelperTaskCategoryDto,
    HelperTaskCreationRequestDto,
    HelperTaskDto,
    HelperTaskMarkAsDoneRequestDto,
    HelperTaskUpdateRequestDto,
    HelperTaskValidationRequestDto,
)

api_helpers = APIRouter(dependencies=[Depends(auth)])


@api_helpers.get("/api/v1/helpers/permissions")
async def helpers_permissions_get(
    user: User = Depends(auth),
    controller: HelpersController = Depends(get_helpers_controller),
) -> Sequence[HelpersAppPermissionDto]:
    _check_can_manage_permissions(user)

    return await controller.find_all_permissions()


@api_helpers.post("/api/v1/helpers/permissions")
async def helpers_permissions_grant(
    request: HelpersAppPermissionGrantRequestDto,
    user: User = Depends(auth),
    controller: HelpersController = Depends(get_helpers_controller),
) -> HelpersAppPermissionDto:
    _check_can_manage_permissions(user)

    return await controller.grant_permission(request, user)


@api_helpers.put("/api/v1/helpers/permissions/{member_id}")
async def helpers_permissions_update(
    member_id: int,
    request: HelpersAppPermissionUpdateRequestDto,
    user: User = Depends(auth),
    controller: HelpersController = Depends(get_helpers_controller),
) -> HelpersAppPermissionDto:
    _check_can_manage_permissions(user)

    return await controller.update_permission(member_id, request, user)


@api_helpers.delete("/api/v1/helpers/permissions/{member_id}")
async def helpers_permissions_revoke(
    member_id: int,
    user: User = Depends(auth),
    controller: HelpersController = Depends(get_helpers_controller),
) -> Response:
    _check_can_manage_permissions(user)

    await controller.revoke_permission(member_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@api_helpers.get("/api/v1/helpers/task-categories")
async def helper_task_categories_get(
    controller: HelpersController = Depends(get_helpers_controller),
) -> Sequence[HelperTaskCategoryDto]:
    return await controller.find_all_task_categories()


@api_helpers.get("/api/v1/helpers/tasks")
async def helper_tasks_get(
    year: int | None = None,
    user: User = Depends(auth),
    controller: HelpersController = Depends(get_helpers_controller),
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
    task_id: int,
    user: User = Depends(auth),
    controller: HelpersController = Depends(get_helpers_controller),
) -> HelperTaskDto:
    task = await controller.get_task_by_id(task_id, published=_published(user))

    if not _can_access_year(task.year, user):
        raise create_http_exception_403("You do not have permission to view this task")

    return task


@api_helpers.post("/api/v1/helpers/tasks")
async def helper_tasks_create(
    request: HelperTaskCreationRequestDto,
    user: User = Depends(auth),
    controller: HelpersController = Depends(get_helpers_controller),
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
    request: HelperTaskUpdateRequestDto,
    user: User = Depends(auth),
    controller: HelpersController = Depends(get_helpers_controller),
) -> HelperTaskDto:
    await _check_can_update(
        task_id, contact_id=request.contact_id, user=user, controller=controller
    )

    existing_task = await helper_tasks_get_by_id(task_id, user, controller)

    if user.helpers_app_editor and (
        request.contact_id != user.member_id
        or existing_task.contact.id != user.member_id
    ):
        raise create_http_exception_403(
            "You have to be the contact for the tasks you update"
        )

    return await controller.update_task(task_id, request, user)


@api_helpers.put("/api/v1/helpers/tasks/{task_id}/captain/{member_id}")
async def helper_tasks_captain_set(
    task_id: int,
    member_id: int,
    user: User = Depends(auth),
    controller: HelpersController = Depends(get_helpers_controller),
) -> HelperTaskDto:
    await _check_can_update(
        task_id, contact_id=user.member_id, user=user, controller=controller
    )

    return await controller.set_captain(task_id, member_id, user)


@api_helpers.delete("/api/v1/helpers/tasks/{task_id}/captain")
async def helper_tasks_captain_remove(
    task_id: int,
    user: User = Depends(auth),
    controller: HelpersController = Depends(get_helpers_controller),
) -> HelperTaskDto:
    await _check_can_update(
        task_id, contact_id=user.member_id, user=user, controller=controller
    )

    return await controller.remove_captain(task_id, user)


@api_helpers.put("/api/v1/helpers/tasks/{task_id}/helpers/{member_id}")
async def helper_tasks_helper_add(
    task_id: int,
    member_id: int,
    user: User = Depends(auth),
    controller: HelpersController = Depends(get_helpers_controller),
) -> HelperTaskDto:
    await _check_can_update(
        task_id, contact_id=user.member_id, user=user, controller=controller
    )

    return await controller.add_helper(task_id, member_id, user)


@api_helpers.delete("/api/v1/helpers/tasks/{task_id}/helpers/{member_id}")
async def helper_tasks_helper_remove(
    task_id: int,
    member_id: int,
    user: User = Depends(auth),
    controller: HelpersController = Depends(get_helpers_controller),
) -> HelperTaskDto:
    await _check_can_update(
        task_id, contact_id=user.member_id, user=user, controller=controller
    )

    return await controller.remove_helper(task_id, member_id, user)


@api_helpers.post("/api/v1/helpers/tasks/{task_id}/sign-up-as-captain")
async def helper_tasks_sign_up_as_captain(
    task_id: int,
    user: User = Depends(auth),
    controller: HelpersController = Depends(get_helpers_controller),
) -> HelperTaskDto:
    return await controller.sign_up_as_captain(task_id, user)


@api_helpers.post("/api/v1/helpers/tasks/{task_id}/sign-up-as-helper")
async def helper_tasks_sign_up_as_helper(
    task_id: int,
    user: User = Depends(auth),
    controller: HelpersController = Depends(get_helpers_controller),
) -> HelperTaskDto:
    return await controller.sign_up_as_helper(task_id, user)


@api_helpers.post("/api/v1/helpers/tasks/{task_id}/mark-as-done")
async def helper_tasks_mark_as_done(
    task_id: int,
    request: HelperTaskMarkAsDoneRequestDto,
    user: User = Depends(auth),
    controller: HelpersController = Depends(get_helpers_controller),
) -> HelperTaskDto:
    if not user.helpers_app_admin:
        task = await helper_tasks_get_by_id(task_id, user, controller)
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
    task_id: int,
    request: HelperTaskValidationRequestDto,
    user: User = Depends(auth),
    controller: HelpersController = Depends(get_helpers_controller),
) -> HelperTaskDto:
    if not user.helpers_app_admin:
        task = await helper_tasks_get_by_id(task_id, user, controller)
        if task.contact.id != user.member_id:
            raise create_http_exception_403(
                "You do not have permission to validate this task"
            )

    await controller.validate(task_id, request, user)
    return await controller.get_task_by_id(task_id, published=True)


def _check_can_manage_permissions(user: User) -> None:
    if not user.helpers_app_admin:
        raise create_http_exception_403("Forbidden")


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


async def _check_can_update(
    task_id: int, *, contact_id: int, user: User, controller: HelpersController
) -> None:
    if not user.helpers_app_admin and not user.helpers_app_editor:
        raise create_http_exception_403(
            "You do not have permission to update helper tasks"
        )

    existing_task = await helper_tasks_get_by_id(task_id, user, controller)

    if user.helpers_app_editor and (
        contact_id != user.member_id or existing_task.contact.id != user.member_id
    ):
        raise create_http_exception_403(
            "You have to be the contact for the tasks you update"
        )
