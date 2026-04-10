import asyncio
import threading
from io import BytesIO
from unittest.mock import patch

import pytest
from PIL import Image

from tests.image_helpers import JPEG_START_OF_IMAGE_MARKER, make_heic_bytes
from ycc_hull.constants import TRANSCODE_MAX_CONCURRENCY
from ycc_hull.image_processing import (
    ImageTranscodeError,
    _transcode_to_jpeg,
    transcode_to_jpeg,
)


@pytest.mark.parametrize(
    ("input_size", "expected_size"),
    [
        ((100, 100), (100, 100)),
        ((200, 200), (200, 200)),
        ((640, 480), (640, 480)),
        ((800, 600), (800, 600)),
        ((2000, 2001), (1999, 2000)),
        ((2001, 2000), (2000, 1999)),
        ((3000, 4000), (1500, 2000)),
        ((4000, 3000), (2000, 1500)),
    ],
)
def test_transcode_to_jpeg_with_heic(
    input_size: tuple[int, int], expected_size: tuple[int, int]
) -> None:
    heic = make_heic_bytes(*input_size)

    jpeg = _transcode_to_jpeg(heic)

    assert jpeg[:3] == JPEG_START_OF_IMAGE_MARKER
    decoded = Image.open(BytesIO(jpeg))
    assert decoded.format == "JPEG"
    assert decoded.size == expected_size
    assert decoded.info.get("exif") is None
    assert decoded.info.get("progressive") == 1


def test_transcode_to_jpeg_raises_on_decompression_bomb() -> None:
    heic = make_heic_bytes(100, 100)
    original = Image.MAX_IMAGE_PIXELS
    try:
        Image.MAX_IMAGE_PIXELS = 10
        with pytest.raises(ImageTranscodeError, match="Image is too large"):
            _transcode_to_jpeg(heic)
    finally:
        Image.MAX_IMAGE_PIXELS = original


def test_transcode_to_jpeg_applies_exif_orientation() -> None:
    """A 100x200 image with EXIF Orientation=6 (90° CW) should become 200x100."""
    # Orientation tag = 0x0112, type SHORT, value 6 = 90° CW
    orientation_6_exif = (
        b"Exif\x00\x00"  # Exif header
        b"MM"  # Big-endian
        b"\x00\x2a"  # TIFF magic
        b"\x00\x00\x00\x08"  # Offset to IFD0
        b"\x00\x01"  # 1 entry in IFD0
        b"\x01\x12"  # Tag: Orientation (0x0112)
        b"\x00\x03"  # Type: SHORT
        b"\x00\x00\x00\x01"  # Count: 1
        b"\x00\x06\x00\x00"  # Value: 6 (90° CW)
        b"\x00\x00\x00\x00"  # Next IFD offset: none
    )

    img = Image.new("RGB", (100, 200), color=(255, 0, 0))
    buf = BytesIO()
    img.save(buf, format="JPEG", exif=orientation_6_exif)
    rotated_jpeg = buf.getvalue()

    result = _transcode_to_jpeg(rotated_jpeg)

    decoded = Image.open(BytesIO(result))
    assert decoded.size == (200, 100)
    assert decoded.info.get("exif") is None


def test_transcode_to_jpeg_drops_alpha_channel() -> None:
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    buf = BytesIO()
    img.save(buf, format="PNG")
    rgba_png = buf.getvalue()

    result = _transcode_to_jpeg(rgba_png)

    decoded = Image.open(BytesIO(result))
    assert decoded.format == "JPEG"
    assert decoded.mode == "RGB"
    assert decoded.size == (100, 100)


def test_transcode_to_jpeg_raises_on_garbage_input() -> None:
    with pytest.raises(ImageTranscodeError, match="Failed to transcode image"):
        _transcode_to_jpeg(b"this is definitely not a heic file")


def test_transcode_to_jpeg_raises_on_empty_input() -> None:
    with pytest.raises(ImageTranscodeError, match="Failed to transcode image"):
        _transcode_to_jpeg(b"")


# ==============================================================================
# Async wrapper: bounded concurrency
# ==============================================================================


@pytest.mark.asyncio
async def test_transcode_to_jpeg_caps_concurrency() -> None:
    in_flight = 0
    peak_in_flight = 0
    lock = threading.Lock()

    def fake_convert(_: bytes) -> bytes:
        nonlocal in_flight, peak_in_flight
        with lock:
            in_flight += 1
            peak_in_flight = max(peak_in_flight, in_flight)

        # Let the scheduler start every task
        threading.Event().wait(0.5)
        with lock:
            in_flight -= 1
        return JPEG_START_OF_IMAGE_MARKER

    with patch("ycc_hull.image_processing._transcode_to_jpeg", fake_convert):
        results = await asyncio.gather(*(transcode_to_jpeg(b"x") for _ in range(20)))

    assert len(results) == 20
    assert all(r == b"\xff\xd8\xff" for r in results)
    assert peak_in_flight <= TRANSCODE_MAX_CONCURRENCY
    # Sanity check: this should have been hit
    assert peak_in_flight == TRANSCODE_MAX_CONCURRENCY


@pytest.mark.asyncio
async def test_transcode_to_jpeg_async_round_trip() -> None:
    img = Image.new("RGB", (320, 240), color=(10, 120, 200))
    buf = BytesIO()
    img.save(buf, format="HEIF")
    heic = buf.getvalue()

    jpeg = await transcode_to_jpeg(heic)

    assert jpeg[:3] == JPEG_START_OF_IMAGE_MARKER
    decoded = Image.open(BytesIO(jpeg))
    assert decoded.format == "JPEG"
    assert decoded.size == (320, 240)


@pytest.mark.asyncio
async def test_transcode_to_jpeg_async_propagates_error() -> None:
    with pytest.raises(ImageTranscodeError, match="Failed to transcode image"):
        await transcode_to_jpeg(b"definitely not heic")
