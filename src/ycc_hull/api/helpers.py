"""Helpers API endpoints."""

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status

from ycc_hull.api.errors import create_http_error_403
from ycc_hull.app_controllers import get_helpers_controller
from ycc_hull.auth import User, auth
from ycc_hull.controllers.helpers_controller import HelpersController
from ycc_hull.models.helpers_dtos import (
    AttachmentMetadataDto,
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
from ycc_hull.utils import get_now

api_helpers = APIRouter(dependencies=[Depends(auth)])


@api_helpers.get("/api/v1/helpers/permissions")
async def helpers_permissions_get(
    user: Annotated[User, Depends(auth)],
    controller: Annotated[HelpersController, Depends(get_helpers_controller)],
) -> Sequence[HelpersAppPermissionDto]:
    """List all helpers app permissions."""
    _check_can_manage_permissions(user)

    return await controller.find_all_permissions()


@api_helpers.post("/api/v1/helpers/permissions")
async def helpers_permissions_grant(
    request: HelpersAppPermissionGrantRequestDto,
    user: Annotated[User, Depends(auth)],
    controller: Annotated[HelpersController, Depends(get_helpers_controller)],
) -> HelpersAppPermissionDto:
    """Grant a helpers app permission."""
    _check_can_manage_permissions(user)

    return await controller.grant_permission(request, user)


@api_helpers.put("/api/v1/helpers/permissions/{member_id}")
async def helpers_permissions_update(
    member_id: int,
    request: HelpersAppPermissionUpdateRequestDto,
    user: Annotated[User, Depends(auth)],
    controller: Annotated[HelpersController, Depends(get_helpers_controller)],
) -> HelpersAppPermissionDto:
    """Update a helpers app permission."""
    _check_can_manage_permissions(user)

    return await controller.update_permission(member_id, request, user)


@api_helpers.delete("/api/v1/helpers/permissions/{member_id}")
async def helpers_permissions_revoke(
    member_id: int,
    user: Annotated[User, Depends(auth)],
    controller: Annotated[HelpersController, Depends(get_helpers_controller)],
) -> Response:
    """Revoke a helpers app permission."""
    _check_can_manage_permissions(user)

    await controller.revoke_permission(member_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@api_helpers.get("/api/v1/helpers/task-categories")
async def helper_task_categories_get(
    controller: Annotated[HelpersController, Depends(get_helpers_controller)],
) -> Sequence[HelperTaskCategoryDto]:
    """List all helper task categories."""
    return await controller.find_all_task_categories()


@api_helpers.get("/api/v1/helpers/tasks")
async def helper_tasks_get(
    user: Annotated[User, Depends(auth)],
    controller: Annotated[HelpersController, Depends(get_helpers_controller)],
    year: int | None = None,
) -> Sequence[HelperTaskDto]:
    """List helper tasks, optionally filtered by year."""
    if not _can_access_year(year, user):
        error_message = (
            f"You do not have permission to list tasks for {year}"
            if year
            else "You do not have permission to list all tasks"
        )
        raise create_http_error_403(error_message)

    return await controller.find_all_tasks(year=year, published=_published(user))


@api_helpers.get("/api/v1/helpers/tasks/{task_id}")
async def helper_tasks_get_by_id(
    task_id: int,
    user: Annotated[User, Depends(auth)],
    controller: Annotated[HelpersController, Depends(get_helpers_controller)],
) -> HelperTaskDto:
    """Get a helper task by ID."""
    task = await controller.get_task_by_id(task_id, published=_published(user))

    if not _can_access_year(task.year, user):
        msg = "You do not have permission to view this task"
        raise create_http_error_403(msg)

    return task


@api_helpers.post("/api/v1/helpers/tasks")
async def helper_tasks_create(
    request: HelperTaskCreationRequestDto,
    user: Annotated[User, Depends(auth)],
    controller: Annotated[HelpersController, Depends(get_helpers_controller)],
) -> HelperTaskDto:
    """Create a new helper task."""
    if not user.helpers_app_admin and not user.helpers_app_editor:
        msg = "You do not have permission to create helper tasks"
        raise create_http_error_403(msg)
    if not user.helpers_app_admin and request.contact_id != user.member_id:
        msg = "You have to be the contact for the tasks you create"
        raise create_http_error_403(msg)

    return await controller.create_task(request, user)


@api_helpers.put("/api/v1/helpers/tasks/{task_id}")
async def helper_tasks_update(
    task_id: int,
    request: HelperTaskUpdateRequestDto,
    user: Annotated[User, Depends(auth)],
    controller: Annotated[HelpersController, Depends(get_helpers_controller)],
) -> HelperTaskDto:
    """Update an existing helper task."""
    await _check_can_update_task(
        task_id, contact_id=request.contact_id, user=user, controller=controller
    )

    existing_task = await helper_tasks_get_by_id(task_id, user, controller)

    if user.helpers_app_editor and (
        request.contact_id != user.member_id
        or existing_task.contact.id != user.member_id
    ):
        msg = "You have to be the contact for the tasks you update"
        raise create_http_error_403(msg)

    return await controller.update_task(task_id, request, user)


@api_helpers.put("/api/v1/helpers/tasks/{task_id}/captain/{member_id}")
async def helper_tasks_captain_set(
    task_id: int,
    member_id: int,
    user: Annotated[User, Depends(auth)],
    controller: Annotated[HelpersController, Depends(get_helpers_controller)],
) -> HelperTaskDto:
    """Set the captain for a helper task."""
    await _check_can_update_task(
        task_id, contact_id=user.member_id, user=user, controller=controller
    )

    return await controller.set_captain(task_id, member_id, user)


@api_helpers.delete("/api/v1/helpers/tasks/{task_id}/captain")
async def helper_tasks_captain_remove(
    task_id: int,
    user: Annotated[User, Depends(auth)],
    controller: Annotated[HelpersController, Depends(get_helpers_controller)],
) -> HelperTaskDto:
    """Remove the captain from a helper task."""
    await _check_can_update_task(
        task_id, contact_id=user.member_id, user=user, controller=controller
    )

    return await controller.remove_captain(task_id, user)


@api_helpers.put("/api/v1/helpers/tasks/{task_id}/helpers/{member_id}")
async def helper_tasks_helper_add(
    task_id: int,
    member_id: int,
    user: Annotated[User, Depends(auth)],
    controller: Annotated[HelpersController, Depends(get_helpers_controller)],
) -> HelperTaskDto:
    """Add a helper to a task."""
    await _check_can_update_task(
        task_id, contact_id=user.member_id, user=user, controller=controller
    )

    return await controller.add_helper(task_id, member_id, user)


@api_helpers.delete("/api/v1/helpers/tasks/{task_id}/helpers/{member_id}")
async def helper_tasks_helper_remove(
    task_id: int,
    member_id: int,
    user: Annotated[User, Depends(auth)],
    controller: Annotated[HelpersController, Depends(get_helpers_controller)],
) -> HelperTaskDto:
    """Remove a helper from a task."""
    await _check_can_update_task(
        task_id, contact_id=user.member_id, user=user, controller=controller
    )

    return await controller.remove_helper(task_id, member_id, user)


@api_helpers.post("/api/v1/helpers/tasks/{task_id}/sign-up-as-captain")
async def helper_tasks_sign_up_as_captain(
    task_id: int,
    user: Annotated[User, Depends(auth)],
    controller: Annotated[HelpersController, Depends(get_helpers_controller)],
) -> HelperTaskDto:
    """Sign up as captain for a task."""
    return await controller.sign_up_as_captain(task_id, user)


@api_helpers.post("/api/v1/helpers/tasks/{task_id}/sign-up-as-helper")
async def helper_tasks_sign_up_as_helper(
    task_id: int,
    user: Annotated[User, Depends(auth)],
    controller: Annotated[HelpersController, Depends(get_helpers_controller)],
) -> HelperTaskDto:
    """Sign up as helper for a task."""
    return await controller.sign_up_as_helper(task_id, user)


@api_helpers.post("/api/v1/helpers/tasks/{task_id}/mark-as-done")
async def helper_tasks_mark_as_done(
    task_id: int,
    request: HelperTaskMarkAsDoneRequestDto,
    user: Annotated[User, Depends(auth)],
    controller: Annotated[HelpersController, Depends(get_helpers_controller)],
) -> HelperTaskDto:
    """Mark a helper task as done."""
    if not user.helpers_app_admin:
        task = await helper_tasks_get_by_id(task_id, user, controller)
        if not (
            task.contact.id == user.member_id
            or (task.captain and task.captain.member.id == user.member_id)
        ):
            msg = "You do not have permission to mark this task as done"
            raise create_http_error_403(msg)

    await controller.mark_as_done(task_id, request, user)
    return await controller.get_task_by_id(task_id, published=True)


@api_helpers.post("/api/v1/helpers/tasks/{task_id}/validate")
async def helper_tasks_validate(
    task_id: int,
    request: HelperTaskValidationRequestDto,
    user: Annotated[User, Depends(auth)],
    controller: Annotated[HelpersController, Depends(get_helpers_controller)],
) -> HelperTaskDto:
    """Validate a completed helper task."""
    if not user.helpers_app_admin:
        task = await helper_tasks_get_by_id(task_id, user, controller)
        if task.contact.id != user.member_id:
            msg = "You do not have permission to validate this task"
            raise create_http_error_403(msg)

    await controller.validate(task_id, request, user)
    return await controller.get_task_by_id(task_id, published=True)


@api_helpers.get("/api/v1/helpers/tasks/{task_id}/attachments")
async def helper_task_attachments_list(
    task_id: int,
    user: Annotated[User, Depends(auth)],
    controller: Annotated[HelpersController, Depends(get_helpers_controller)],
) -> Sequence[AttachmentMetadataDto]:
    """List attachment metadata for a helper task."""
    await _verify_task_accessible(task_id, user, controller)
    return await controller.find_attachments_for_task(task_id)


@api_helpers.get("/api/v1/helpers/tasks/{task_id}/attachments/{attachment_id}")
async def helper_task_attachment_download(
    task_id: int,
    attachment_id: int,
    user: Annotated[User, Depends(auth)],
    controller: Annotated[HelpersController, Depends(get_helpers_controller)],
) -> Response:
    """Download an attachment."""
    await _verify_task_accessible(task_id, user, controller)
    attachment = await controller.get_attachment_with_content(task_id, attachment_id)
    return Response(
        content=attachment.content,
        media_type=attachment.mime_type,
        headers={
            # inline so the frontend can render images directly in the browser
            "Content-Disposition": f'inline; filename="{attachment.name}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@api_helpers.post("/api/v1/helpers/tasks/{task_id}/attachments")
async def helper_task_attachment_upload(
    task_id: int,
    file: Annotated[UploadFile, File()],
    user: Annotated[User, Depends(auth)],
    controller: Annotated[HelpersController, Depends(get_helpers_controller)],
    description: Annotated[str | None, Form()] = None,
) -> AttachmentMetadataDto:
    """Upload an attachment to a helper task. Any authenticated member can upload."""
    await _verify_task_accessible(task_id, user, controller)
    return await controller.upload_attachment(task_id, file, description, user)


@api_helpers.post("/api/v1/helpers/attachments/transcode")
async def helper_attachment_transcode(
    file: Annotated[UploadFile, File()],
    user: Annotated[User, Depends(auth)],  # noqa: ARG001 (require auth)
    controller: Annotated[HelpersController, Depends(get_helpers_controller)],
) -> Response:
    """Transcode an uploaded HEIC/HEIF image to JPEG and return the bytes.

    Stateless utility for the frontend - no database writes. Used so that HEIC/HEIF
    images can be previewed in browsers (e.g. Mac + Firefox) that cannot decode them
    natively. The frontend uploads the resulting JPEG via the regular upload endpoint
    when the user finalises.
    """
    jpeg = await controller.transcode_image_to_jpeg(file)
    return Response(
        content=jpeg,
        media_type="image/jpeg",
        headers={"X-Content-Type-Options": "nosniff"},
    )


@api_helpers.delete("/api/v1/helpers/tasks/{task_id}/attachments/{attachment_id}")
async def helper_task_attachment_delete(
    task_id: int,
    attachment_id: int,
    user: Annotated[User, Depends(auth)],
    controller: Annotated[HelpersController, Depends(get_helpers_controller)],
) -> Response:
    """Delete an attachment from a helper task.

    Allowed for the uploader (owner) of the attachment, or anyone with task
    edit permissions (admin, editor who is contact).
    """
    await _verify_task_accessible(task_id, user, controller)
    owner_id = await controller.get_attachment_owner_id(task_id, attachment_id)
    if owner_id != user.member_id:
        await _check_can_update_task(
            task_id, contact_id=user.member_id, user=user, controller=controller
        )
    await controller.delete_attachment(task_id, attachment_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _check_can_manage_permissions(user: User) -> None:
    if not user.helpers_app_admin:
        msg = "Forbidden"
        raise create_http_error_403(msg)


async def _verify_task_accessible(
    task_id: int, user: User, controller: HelpersController
) -> None:
    """Verify the task exists and the user can view it."""
    await controller.get_task_by_id(task_id, published=_published(user))


def _published(user: User) -> bool | None:
    return None if user.helpers_app_admin_or_editor else True


def _can_access_year(year: int | None, user: User) -> bool:
    current_year = get_now().year

    return (
        year == current_year
        or user.admin
        or user.committee_member
        or user.helpers_app_admin
        or user.helpers_app_editor
    )


async def _check_can_update_task(
    task_id: int, *, contact_id: int, user: User, controller: HelpersController
) -> None:
    if not user.helpers_app_admin and not user.helpers_app_editor:
        msg = "You do not have permission to update helper tasks"
        raise create_http_error_403(msg)

    existing_task = await helper_tasks_get_by_id(task_id, user, controller)

    if user.helpers_app_editor and (
        contact_id != user.member_id or existing_task.contact.id != user.member_id
    ):
        msg = "You have to be the contact for the tasks you update"
        raise create_http_error_403(msg)
