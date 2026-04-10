from io import BytesIO
from unittest.mock import patch

import httpx
import pytest
from PIL import Image

from tests.api.conftest import client
from tests.image_helpers import JPEG_START_OF_IMAGE_MARKER, make_heic_bytes
from tests.test_main import FakeAuth

TRANSCODE_URL = "/api/v1/helpers/attachments/transcode"


def _post(filename: str, content: bytes) -> httpx.Response:
    return client.post(
        TRANSCODE_URL,
        files={"file": (filename, BytesIO(content), "image/heic")},
    )


@pytest.mark.parametrize("filename", ["iphone.heic", "photo.heif"])
def test_transcode_returns_jpeg_bytes(filename: str) -> None:
    FakeAuth.set_helpers_app_admin()
    heic = make_heic_bytes()

    response = _post(filename, heic)

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.headers["x-content-type-options"] == "nosniff"
    body = response.content
    assert body[:3] == JPEG_START_OF_IMAGE_MARKER

    decoded = Image.open(BytesIO(body))
    assert decoded.format == "JPEG"
    assert decoded.size == (320, 240)


def test_transcode_uppercase_extension() -> None:
    FakeAuth.set_helpers_app_admin()
    heic = make_heic_bytes()

    response = _post("PHOTO.HEIC", heic)

    assert response.status_code == 200
    assert response.content[:3] == JPEG_START_OF_IMAGE_MARKER


def test_transcode_downscales_large_image() -> None:
    FakeAuth.set_helpers_app_admin()
    heic = make_heic_bytes(4000, 3000)

    response = _post("big.heic", heic)

    assert response.status_code == 200
    decoded = Image.open(BytesIO(response.content))
    assert decoded.size == (2000, 1500)


def test_transcode_preserves_small_images() -> None:
    FakeAuth.set_helpers_app_admin()
    heic = make_heic_bytes(800, 600)

    response = _post("small.heic", heic)

    assert response.status_code == 200
    decoded = Image.open(BytesIO(response.content))
    assert decoded.size == (800, 600)


@pytest.mark.parametrize(
    "filename",
    [
        "photo.jpg",
        "photo.png",
        "photo.webp",
        "malware.exe",
    ],
)
def test_transcode_rejects_non_heic_extensions(filename: str) -> None:
    FakeAuth.set_helpers_app_admin()

    response = _post(filename, b"\x00" * 32)

    assert response.status_code == 400
    assert response.json()["detail"] == (
        f"Unsupported file type for transcoding: {filename} (allowed: .heic, .heif)"
    )


def test_transcode_rejects_corrupt_heic() -> None:
    FakeAuth.set_helpers_app_admin()

    response = _post("broken.heic", b"this is definitely not a heic file")

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image: broken.heic"


def test_transcode_rejects_oversized_input_before_decoding() -> None:
    FakeAuth.set_helpers_app_admin()

    target = "ycc_hull.controllers.helpers_controller.ATTACHMENT_MAX_FILE_SIZE_BYTES"
    with patch(target, 10):
        response = _post("huge.heic", b"\x00" * 11)

    assert response.status_code == 400
    assert response.json()["detail"] == "File too large (max 10 bytes)"


def test_transcode_allowed_for_regular_member() -> None:
    FakeAuth.set_member(member_id=100)
    heic = make_heic_bytes()

    response = _post("photo.heic", heic)

    assert response.status_code == 200
    assert response.content[:3] == JPEG_START_OF_IMAGE_MARKER
