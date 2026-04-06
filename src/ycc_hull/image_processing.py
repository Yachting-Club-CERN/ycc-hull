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

# Done once at import time so the controller never has to think about it.
register_heif_opener()

# Defend against decompression bombs
Image.MAX_IMAGE_PIXELS = TRANSCODE_MAX_DECODED_PIXELS

# Hard cap on simultaneous transcodes. Excess requests await this semaphore
# (FIFO queue, no timeout) so memory and CPU stay bounded under bursty load
_transcode_semaphore = asyncio.Semaphore(TRANSCODE_MAX_CONCURRENCY)


async def convert_heic_to_jpeg(data: bytes) -> bytes:
    """Convert HEIC/HEIF bytes to JPEG bytes."""
    async with _transcode_semaphore:
        return await asyncio.to_thread(_convert_heic_to_jpeg, data)


def _convert_heic_to_jpeg(data: bytes) -> bytes:
    """Convert HEIC/HEIF bytes to JPEG bytes."""
    try:
        with Image.open(BytesIO(data)) as img:
            oriented = ImageOps.exif_transpose(img) or img
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
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        msg = "Image is too large to decode safely"
        raise ValueError(msg) from exc
    except Exception as exc:
        msg = "Failed to decode HEIC/HEIF image"
        raise ValueError(msg) from exc
