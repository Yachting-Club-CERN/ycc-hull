from io import BytesIO

from PIL import Image

JPEG_START_OF_IMAGE_MARKER = b"\xff\xd8\xff"


def make_heic_bytes(
    width: int = 320,
    height: int = 240,
    *,
    color: tuple[int, int, int] = (10, 120, 200),
) -> bytes:
    import ycc_hull.image_processing  # noqa: F401 - registers HEIF opener

    img = Image.new("RGB", (width, height), color=color)
    buf = BytesIO()
    img.save(buf, format="HEIF")
    return buf.getvalue()
