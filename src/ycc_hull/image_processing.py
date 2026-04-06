"""Server-side image processing for uploaded attachments."""

from io import BytesIO

from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

from ycc_hull.constants import (
    TRANSCODE_JPEG_QUALITY,
    TRANSCODE_MAX_DECODED_PIXELS,
    TRANSCODE_MAX_DIMENSION,
)

# Done once at import time so the controller never has to think about it.
register_heif_opener()

# Defend against decompression bombs
Image.MAX_IMAGE_PIXELS = TRANSCODE_MAX_DECODED_PIXELS


def convert_heic_to_jpeg(data: bytes) -> bytes:
    """Decode HEIC/HEIF bytes and re-encode as a stripped, downscaled JPEG."""
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
