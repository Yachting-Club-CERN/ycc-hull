"""Image processing utilities."""

import asyncio
import logging
from io import BytesIO

from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

from ycc_hull.constants import (
    TRANSCODE_JPEG_QUALITY,
    TRANSCODE_MAX_CONCURRENCY,
    TRANSCODE_MAX_DECODED_PIXELS,
    TRANSCODE_MAX_DIMENSION,
)

# HEIC/HEIF support
register_heif_opener()

# Defend against decompression bombs (PIL errors at 2x the value)
Image.MAX_IMAGE_PIXELS = TRANSCODE_MAX_DECODED_PIXELS // 2

# Hard cap on simultaneous transcodes to prevent OOM
_transcode_semaphore = asyncio.Semaphore(TRANSCODE_MAX_CONCURRENCY)

_logger = logging.getLogger(__name__)


class ImageTranscodeError(Exception):
    """Raised when image transcoding fails."""


async def transcode_to_jpeg(data: bytes) -> bytes:
    """Convert image bytes to JPEG bytes.

    Applies orientation from EXIF, resizes and compresses the image.
    """
    if _transcode_semaphore.locked():
        _logger.info("Transcode semaphore saturated; request queued")
    async with _transcode_semaphore:
        return await asyncio.to_thread(_transcode_to_jpeg, data)


def _transcode_to_jpeg(data: bytes) -> bytes:
    try:
        with Image.open(BytesIO(data)) as img:
            ImageOps.exif_transpose(img, in_place=True)
            # 2026-03: It looks like it simply drops alpha, good enough for now
            rgb = img.convert("RGB")

            try:
                rgb.thumbnail(
                    (TRANSCODE_MAX_DIMENSION, TRANSCODE_MAX_DIMENSION),
                    Image.Resampling.LANCZOS,
                )
                out = BytesIO()
                rgb.save(
                    out,
                    format="JPEG",
                    quality=TRANSCODE_JPEG_QUALITY,
                    optimize=True,
                    progressive=True,
                )
                return out.getvalue()
            finally:
                rgb.close()
    except Image.DecompressionBombError as exc:
        msg = "Image is too large"
        _logger.exception(msg)
        raise ImageTranscodeError(msg) from exc
    except Exception as exc:
        msg = "Failed to transcode image"
        _logger.exception(msg)
        raise ImageTranscodeError(msg) from exc
