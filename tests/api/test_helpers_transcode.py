from io import BytesIO
from unittest.mock import patch

import httpx
from PIL import Image

from tests.api.conftest import client
from tests.test_main import FakeAuth

JPEG_START_OF_IMAGE_MARKER = b"\xff\xd8\xff"

TRANSCODE_URL = "/api/v1/helpers/attachments/transcode"


def _make_heic_bytes(width: int = 320, height: int = 240) -> bytes:
    # Importing image_processing registers the HEIF opener as a side effect
    import ycc_hull.image_processing  # noqa: F401

    img = Image.new("RGB", (width, height), color=(10, 120, 200))
    buf = BytesIO()
    img.save(buf, format="HEIF")
    return buf.getvalue()


def _post(filename: str, content: bytes) -> httpx.Response:
    return client.post(
        TRANSCODE_URL,
        files={"file": (filename, BytesIO(content), "image/heic")},
    )


def test_transcode_heic_returns_jpeg_bytes() -> None:
    FakeAuth.set_helpers_app_admin()
    heic = _make_heic_bytes()

    response = _post("iphone.heic", heic)

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.headers["x-content-type-options"] == "nosniff"
    body = response.content
    assert body[:3] == JPEG_START_OF_IMAGE_MARKER

    decoded = Image.open(BytesIO(body))
    assert decoded.format == "JPEG"
    assert decoded.size == (320, 240)


def test_transcode_heif_returns_jpeg_bytes() -> None:
    FakeAuth.set_helpers_app_admin()
    heic = _make_heic_bytes()

    response = _post("photo.heif", heic)

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.content[:3] == JPEG_START_OF_IMAGE_MARKER


def test_transcode_uppercase_extension() -> None:
    FakeAuth.set_helpers_app_admin()
    heic = _make_heic_bytes()

    response = _post("PHOTO.HEIC", heic)

    assert response.status_code == 200
    assert response.content[:3] == JPEG_START_OF_IMAGE_MARKER


def test_transcode_downscales_large_image() -> None:
    FakeAuth.set_helpers_app_admin()
    heic = _make_heic_bytes(4000, 3000)

    response = _post("big.heic", heic)

    assert response.status_code == 200
    decoded = Image.open(BytesIO(response.content))
    assert decoded.size == (2000, 1500)


def test_transcode_preserves_small_images() -> None:
    FakeAuth.set_helpers_app_admin()
    heic = _make_heic_bytes(800, 600)

    response = _post("small.heic", heic)

    assert response.status_code == 200
    decoded = Image.open(BytesIO(response.content))
    assert decoded.size == (800, 600)


def test_transcode_rejects_jpg() -> None:
    FakeAuth.set_helpers_app_admin()

    response = _post("photo.jpg", b"\x00" * 32)

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Unsupported file type for transcoding: photo.jpg (allowed: .heic, .heif)"
    )


def test_transcode_rejects_png() -> None:
    FakeAuth.set_helpers_app_admin()

    response = _post("photo.png", b"\x00" * 32)

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Unsupported file type for transcoding: photo.png (allowed: .heic, .heif)"
    )


def test_transcode_rejects_webp() -> None:
    FakeAuth.set_helpers_app_admin()

    response = _post("photo.webp", b"\x00" * 32)

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Unsupported file type for transcoding: photo.webp (allowed: .heic, .heif)"
    )


def test_transcode_rejects_unknown_extension() -> None:
    FakeAuth.set_helpers_app_admin()

    response = _post("malware.exe", b"\x00" * 32)

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Unsupported file type for transcoding: malware.exe (allowed: .heic, .heif)"
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
    assert "too large" in response.json()["detail"].lower()


def test_transcode_allowed_for_regular_member() -> None:
    FakeAuth.set_member(member_id=100)
    heic = _make_heic_bytes()

    response = _post("photo.heic", heic)

    assert response.status_code == 200
    assert response.content[:3] == JPEG_START_OF_IMAGE_MARKER
