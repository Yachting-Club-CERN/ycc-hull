"""Server-side image processing for uploaded attachments."""

import asyncio
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

# Defend against decompression bombs (note: PIL fails at 2x the limit)
Image.MAX_IMAGE_PIXELS = TRANSCODE_MAX_DECODED_PIXELS

# Hard cap on simultaneous transcodes to prevent OOM
_transcode_semaphore = asyncio.Semaphore(TRANSCODE_MAX_CONCURRENCY)


class ImageTranscodeError(Exception):
    """Raised when image transcoding fails."""


async def transcode_to_jpeg(data: bytes) -> bytes:
    """Convert image bytes to JPEG bytes.

    Applies orientation from EXIF, resizes and compresses the image.
    """
    async with _transcode_semaphore:
        return await asyncio.to_thread(_transcode_to_jpeg, data)


def _transcode_to_jpeg(data: bytes) -> bytes:
    try:
        with Image.open(BytesIO(data)) as img:
            oriented = ImageOps.exif_transpose(img) or img
            # 2026-03: It looks like it simply drops alpha, good enough for now
            rgb = oriented.convert("RGB")

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
    except Image.DecompressionBombError as exc:
        msg = "Image is too large"
        raise ImageTranscodeError(msg) from exc
    except Exception as exc:
        msg = "Failed to transcode image"
        raise ImageTranscodeError(msg) from exc
