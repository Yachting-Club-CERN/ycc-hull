from io import BytesIO
from unittest.mock import patch

import httpx
from sqlalchemy import inspect, select

from tests.api.conftest import client
from tests.api.helpers_test_utils import MEMBER_PUBLIC_INFO_KEYS, create_shift_task
from tests.test_main import FakeAuth
from ycc_hull.db.context import DatabaseContextHolder
from ycc_hull.db.entities import AttachmentEntity
from ycc_hull.utils import get_now

# Minimal 1x1 pixel PNG for upload tests
TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
    b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
    b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)

ATTACHMENT_METADATA_KEYS = {
    "id",
    "name",
    "mimeType",
    "sizeBytes",
    "owner",
    "created",
    "description",
}


def _upload(
    task_id: int,
    *,
    filename: str = "photo.png",
    content: bytes = TINY_PNG,
    description: str | None = None,
) -> httpx.Response:
    data: dict = {}
    if description is not None:
        data["description"] = description
    return client.post(
        f"/api/v1/helpers/tasks/{task_id}/attachments",
        files={"file": (filename, BytesIO(content), "image/png")},
        data=data,
    )


# ==============================================================================
# Upload tests
# ==============================================================================


def test_upload_attachment() -> None:
    FakeAuth.set_helpers_app_admin()
    task = create_shift_task(client)
    task_id = task["id"]

    response = _upload(task_id, description="A test photo")
    assert response.status_code == 200
    data = response.json()
    assert data.keys() == ATTACHMENT_METADATA_KEYS
    assert data["name"] == "photo.png"
    assert data["mimeType"] == "image/png"
    assert data["sizeBytes"] == len(TINY_PNG)
    assert data["owner"]["id"] == 1
    assert data["owner"].keys() == MEMBER_PUBLIC_INFO_KEYS
    assert data["description"] == "A test photo"


def test_upload_attachment_no_description() -> None:
    FakeAuth.set_helpers_app_admin()
    task = create_shift_task(client)
    task_id = task["id"]

    response = _upload(task_id)
    assert response.status_code == 200
    data = response.json()
    assert data["description"] is None


def test_upload_rejects_disallowed_extension() -> None:
    FakeAuth.set_helpers_app_admin()
    task = create_shift_task(client)
    task_id = task["id"]

    response = _upload(task_id, filename="malware.exe")
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "not allowed" in detail


def test_upload_rejects_file_too_large() -> None:
    FakeAuth.set_helpers_app_admin()
    task = create_shift_task(client)
    task_id = task["id"]

    # Patch the limit to 10 bytes so we do not need a huge payload
    target = "ycc_hull.controllers.helpers_controller.ATTACHMENT_MAX_FILE_SIZE_BYTES"
    with patch(target, 10):
        response = _upload(task_id, content=b"\x00" * 11)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "too large" in detail.lower()


def test_upload_allowed_for_regular_member() -> None:
    FakeAuth.set_helpers_app_admin()
    task = create_shift_task(client, published=True)
    task_id = task["id"]

    FakeAuth.set_member(member_id=100)
    response = _upload(task_id, description="Member upload")
    assert response.status_code == 200
    data = response.json()
    assert data["owner"]["id"] == 100
    assert data["description"] == "Member upload"


def test_upload_jpeg_extension() -> None:
    FakeAuth.set_helpers_app_admin()
    task = create_shift_task(client)
    task_id = task["id"]

    response = _upload(task_id, filename="photo.jpg")
    assert response.status_code == 200
    data = response.json()
    assert data["mimeType"] == "image/jpeg"


def test_upload_webp_extension() -> None:
    FakeAuth.set_helpers_app_admin()
    task = create_shift_task(client)
    task_id = task["id"]

    response = _upload(task_id, filename="photo.webp")
    assert response.status_code == 200
    data = response.json()
    assert data["mimeType"] == "image/webp"


# ==============================================================================
# List tests
# ==============================================================================


def test_list_attachments() -> None:
    FakeAuth.set_helpers_app_admin()
    task = create_shift_task(client)
    task_id = task["id"]

    _upload(task_id, filename="first.png", description="First")
    _upload(task_id, filename="second.png", description="Second")

    response = client.get(f"/api/v1/helpers/tasks/{task_id}/attachments")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Ordered by creation
    assert data[0]["name"] == "first.png"
    assert data[0]["description"] == "First"
    assert data[0].keys() == ATTACHMENT_METADATA_KEYS

    assert data[1]["name"] == "second.png"
    assert data[1]["description"] == "Second"
    assert data[1].keys() == ATTACHMENT_METADATA_KEYS


def test_list_attachments_empty() -> None:
    FakeAuth.set_helpers_app_admin()
    task = create_shift_task(client)
    task_id = task["id"]

    response = client.get(f"/api/v1/helpers/tasks/{task_id}/attachments")
    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_list_excludes_blob_content() -> None:
    FakeAuth.set_helpers_app_admin()
    task = create_shift_task(client)
    task_id = task["id"]
    _upload(task_id, description="BLOB test")

    # Verify the API response does not contain content/thumbnail keys
    response = client.get(f"/api/v1/helpers/tasks/{task_id}/attachments")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "content" not in data[0]
    assert "thumbnail" not in data[0]
    assert data[0].keys() == ATTACHMENT_METADATA_KEYS

    # Verify at SQLAlchemy level that the entity loaded via defer() does not have
    # content/thumbnail in its loaded state
    from sqlalchemy.orm import defer

    with DatabaseContextHolder.context.session() as session:
        entity = session.scalars(
            select(AttachmentEntity)
            .options(defer(AttachmentEntity.content), defer(AttachmentEntity.thumbnail))
            .where(AttachmentEntity.ref_id == task_id)
        ).first()
        assert entity is not None
        # inspect() shows which attributes are loaded vs deferred
        state = inspect(entity)
        # content and thumbnail should bot be in the loaded set
        assert "content" not in state.dict
        assert "thumbnail" not in state.dict
        # But other fields should be loaded
        assert "name" in state.dict
        assert "mime_type" in state.dict


def test_list_viewable_by_regular_member() -> None:
    FakeAuth.set_helpers_app_admin()
    task = create_shift_task(client, published=True)
    task_id = task["id"]
    _upload(task_id, description="Visible to all")

    FakeAuth.set_member(member_id=100)
    response = client.get(f"/api/v1/helpers/tasks/{task_id}/attachments")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["description"] == "Visible to all"


# ==============================================================================
# Download tests
# ==============================================================================


def test_download_attachment() -> None:
    FakeAuth.set_helpers_app_admin()
    task = create_shift_task(client)
    task_id = task["id"]

    upload_response = _upload(task_id, filename="download_me.png")
    assert upload_response.status_code == 200
    attachment_id = upload_response.json()["id"]

    response = client.get(
        f"/api/v1/helpers/tasks/{task_id}/attachments/{attachment_id}"
    )
    assert response.status_code == 200
    assert response.content == TINY_PNG
    assert response.headers["content-type"] == "image/png"
    assert 'filename="download_me.png"' in response.headers["content-disposition"]


def test_download_not_found() -> None:
    FakeAuth.set_helpers_app_admin()
    task = create_shift_task(client)
    task_id = task["id"]

    response = client.get(f"/api/v1/helpers/tasks/{task_id}/attachments/999999")
    assert response.status_code == 404


def test_download_wrong_task_id() -> None:
    FakeAuth.set_helpers_app_admin()
    task_a = create_shift_task(client)
    task_b = create_shift_task(client)

    upload_response = _upload(task_a["id"], filename="task_a_only.png")
    assert upload_response.status_code == 200
    attachment_id = upload_response.json()["id"]

    response = client.get(
        f"/api/v1/helpers/tasks/{task_b['id']}/attachments/{attachment_id}"
    )
    assert response.status_code == 404


def test_download_viewable_by_regular_member() -> None:
    FakeAuth.set_helpers_app_admin()
    task = create_shift_task(client, published=True)
    task_id = task["id"]

    upload_response = _upload(task_id, filename="public.png")
    assert upload_response.status_code == 200
    attachment_id = upload_response.json()["id"]

    FakeAuth.set_member(member_id=100)
    response = client.get(
        f"/api/v1/helpers/tasks/{task_id}/attachments/{attachment_id}"
    )
    assert response.status_code == 200
    assert response.content == TINY_PNG


# ==============================================================================
# Delete tests
# ==============================================================================


def test_delete_attachment() -> None:
    FakeAuth.set_helpers_app_admin()
    task = create_shift_task(client)
    task_id = task["id"]

    upload_response = _upload(task_id, filename="to_delete.png")
    assert upload_response.status_code == 200
    attachment_id = upload_response.json()["id"]

    response = client.delete(
        f"/api/v1/helpers/tasks/{task_id}/attachments/{attachment_id}"
    )
    assert response.status_code == 204

    list_response = client.get(f"/api/v1/helpers/tasks/{task_id}/attachments")
    assert list_response.status_code == 200
    assert list_response.json() == []


def test_delete_not_found() -> None:
    FakeAuth.set_helpers_app_admin()
    task = create_shift_task(client)
    task_id = task["id"]

    response = client.delete(f"/api/v1/helpers/tasks/{task_id}/attachments/999999")
    assert response.status_code == 404


def test_delete_forbidden_for_non_owner_regular_member() -> None:
    FakeAuth.set_helpers_app_admin()
    task = create_shift_task(client)
    task_id = task["id"]

    # Admin uploads the attachment (owner_id=1)
    upload_response = _upload(task_id, filename="no_delete.png")
    assert upload_response.status_code == 200
    attachment_id = upload_response.json()["id"]

    # Different member (id=100) tries to delete - forbidden
    FakeAuth.set_member(member_id=100)
    response = client.delete(
        f"/api/v1/helpers/tasks/{task_id}/attachments/{attachment_id}"
    )
    assert response.status_code == 403


def test_delete_allowed_for_owner() -> None:
    # Create a published task as admin
    FakeAuth.set_helpers_app_admin()
    task = create_shift_task(client, published=True)
    task_id = task["id"]

    # Upload as regular member 100 (anyone can upload)
    FakeAuth.set_member(member_id=100)
    upload_response = _upload(task_id, filename="my_photo.png")
    assert upload_response.status_code == 200
    attachment_id = upload_response.json()["id"]
    assert upload_response.json()["owner"]["id"] == 100

    # Same regular member 100 deletes their own attachment
    response = client.delete(
        f"/api/v1/helpers/tasks/{task_id}/attachments/{attachment_id}"
    )
    assert response.status_code == 204

    # Verify it is gone
    list_response = client.get(f"/api/v1/helpers/tasks/{task_id}/attachments")
    assert list_response.status_code == 200
    assert list_response.json() == []


def test_delete_wrong_ref_class_id() -> None:
    FakeAuth.set_helpers_app_admin()
    task = create_shift_task(client)
    task_id = task["id"]

    # Insert an attachment directly with a bogus ref_class_id
    with DatabaseContextHolder.context.session() as session:
        entity = AttachmentEntity(
            name="bogus.png",
            content=TINY_PNG,
            mime_type="image/png",
            size_bytes=len(TINY_PNG),
            owner_id=1,
            created=get_now(),
            description=None,
            thumbnail=None,
            ref_id=task_id,
            ref_class_id=9999,  # Not a valid ref_class_id
        )
        session.add(entity)
        session.commit()
        session.refresh(entity)
        bogus_id = entity.id

    # Should not appear in the list (filtered by ref_class_id)
    list_response = client.get(f"/api/v1/helpers/tasks/{task_id}/attachments")
    assert list_response.status_code == 200
    assert all(item["id"] != bogus_id for item in list_response.json())

    # Download should return 404
    response = client.get(f"/api/v1/helpers/tasks/{task_id}/attachments/{bogus_id}")
    assert response.status_code == 404

    # Delete should return 404
    response = client.delete(f"/api/v1/helpers/tasks/{task_id}/attachments/{bogus_id}")
    assert response.status_code == 404
