"""Unit tests for ycc_hull.image_processing."""

import asyncio
import threading
from io import BytesIO
from unittest.mock import patch

import pytest
from PIL import Image

from ycc_hull.constants import TRANSCODE_MAX_CONCURRENCY
from ycc_hull.image_processing import _convert_heic_to_jpeg, convert_heic_to_jpeg

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

    jpeg = _convert_heic_to_jpeg(heic)

    assert jpeg[:3] == JPEG_START_OF_IMAGE_MARKER

    decoded = Image.open(BytesIO(jpeg))
    assert decoded.format == "JPEG"
    assert decoded.size == (640, 480)


def test_convert_heic_to_jpeg_downscales_to_max_dimension() -> None:
    heic = _make_heic(4000, 3000)

    jpeg = _convert_heic_to_jpeg(heic)

    decoded = Image.open(BytesIO(jpeg))
    assert decoded.size == (2000, 1500)


def test_convert_heic_to_jpeg_preserves_small_images() -> None:
    heic = _make_heic(800, 600)

    jpeg = _convert_heic_to_jpeg(heic)

    decoded = Image.open(BytesIO(jpeg))
    assert decoded.size == (800, 600)


def test_convert_heic_to_jpeg_strips_exif() -> None:
    heic = _make_heic(100, 100)

    jpeg = _convert_heic_to_jpeg(heic)

    decoded = Image.open(BytesIO(jpeg))
    assert decoded.info.get("exif") is None


def test_convert_heic_to_jpeg_writes_progressive() -> None:
    heic = _make_heic(200, 200)

    jpeg = _convert_heic_to_jpeg(heic)

    decoded = Image.open(BytesIO(jpeg))
    assert decoded.info.get("progressive") == 1


def test_convert_heic_to_jpeg_raises_on_garbage_input() -> None:
    with pytest.raises(ValueError, match="Failed to decode HEIC/HEIF image"):
        _convert_heic_to_jpeg(b"this is definitely not a heic file")


def test_convert_heic_to_jpeg_raises_on_empty_input() -> None:
    with pytest.raises(ValueError, match="Failed to decode HEIC/HEIF image"):
        _convert_heic_to_jpeg(b"")


# ==============================================================================
# Async wrapper: bounded concurrency
# ==============================================================================


@pytest.mark.asyncio
async def test_convert_heic_to_jpeg_caps_concurrency() -> None:
    in_flight = 0
    peak_in_flight = 0
    lock = threading.Lock()

    def fake_convert(_: bytes) -> bytes:
        nonlocal in_flight, peak_in_flight
        with lock:
            in_flight += 1
            peak_in_flight = max(peak_in_flight, in_flight)
        # Sleep long enough that the asyncio scheduler has time to start every
        # task that can possibly start, exposing the true peak.
        threading.Event().wait(0.05)
        with lock:
            in_flight -= 1
        return b"\xff\xd8\xff"  # JPEG magic, content irrelevant

    with patch("ycc_hull.image_processing._convert_heic_to_jpeg", fake_convert):
        results = await asyncio.gather(*(convert_heic_to_jpeg(b"x") for _ in range(12)))

    assert len(results) == 12
    assert all(r == b"\xff\xd8\xff" for r in results)
    assert peak_in_flight <= TRANSCODE_MAX_CONCURRENCY
    # Sanity: with 12 concurrent calls and a cap of 5, the cap must actually
    # have been hit at some point - otherwise the test would not be exercising
    # the semaphore at all.
    assert peak_in_flight == TRANSCODE_MAX_CONCURRENCY


@pytest.mark.asyncio
async def test_convert_heic_to_jpeg_async_round_trip() -> None:
    img = Image.new("RGB", (320, 240), color=(10, 120, 200))
    buf = BytesIO()
    img.save(buf, format="HEIF")
    heic = buf.getvalue()

    jpeg = await convert_heic_to_jpeg(heic)

    assert jpeg[:3] == JPEG_START_OF_IMAGE_MARKER
    decoded = Image.open(BytesIO(jpeg))
    assert decoded.format == "JPEG"
    assert decoded.size == (320, 240)


@pytest.mark.asyncio
async def test_convert_heic_to_jpeg_async_propagates_value_error() -> None:
    with pytest.raises(ValueError, match="Failed to decode HEIC/HEIF image"):
        await convert_heic_to_jpeg(b"definitely not heic")
