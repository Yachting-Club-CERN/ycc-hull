"""Unit tests for ycc_hull.image_processing."""

from io import BytesIO

import pytest
from PIL import Image

from ycc_hull.image_processing import convert_heic_to_jpeg

JPEG_START_OF_IMAGE_MARKER = b"\xff\xd8\xff"


def _make_heic(
    width: int,
    height: int,
    *,
    color: tuple[int, int, int] = (200, 50, 50),
) -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    buf = BytesIO()
    img.save(buf, format="HEIF")
    return buf.getvalue()


def test_convert_heic_to_jpeg_returns_valid_jpeg() -> None:
    heic = _make_heic(640, 480)

    jpeg = convert_heic_to_jpeg(heic)

    assert jpeg[:3] == JPEG_START_OF_IMAGE_MARKER

    decoded = Image.open(BytesIO(jpeg))
    assert decoded.format == "JPEG"
    assert decoded.size == (640, 480)


def test_convert_heic_to_jpeg_downscales_to_max_dimension() -> None:
    heic = _make_heic(4000, 3000)

    jpeg = convert_heic_to_jpeg(heic)

    decoded = Image.open(BytesIO(jpeg))
    assert decoded.size == (2000, 1500)


def test_convert_heic_to_jpeg_preserves_small_images() -> None:
    heic = _make_heic(800, 600)

    jpeg = convert_heic_to_jpeg(heic)

    decoded = Image.open(BytesIO(jpeg))
    assert decoded.size == (800, 600)


def test_convert_heic_to_jpeg_strips_exif() -> None:
    heic = _make_heic(100, 100)

    jpeg = convert_heic_to_jpeg(heic)

    decoded = Image.open(BytesIO(jpeg))
    assert decoded.info.get("exif") is None


def test_convert_heic_to_jpeg_writes_progressive() -> None:
    heic = _make_heic(200, 200)

    jpeg = convert_heic_to_jpeg(heic)

    decoded = Image.open(BytesIO(jpeg))
    assert decoded.info.get("progressive") == 1


def test_convert_heic_to_jpeg_raises_on_garbage_input() -> None:
    with pytest.raises(ValueError, match="Failed to decode HEIC/HEIF image"):
        convert_heic_to_jpeg(b"this is definitely not a heic file")


def test_convert_heic_to_jpeg_raises_on_empty_input() -> None:
    with pytest.raises(ValueError, match="Failed to decode HEIC/HEIF image"):
        convert_heic_to_jpeg(b"")
