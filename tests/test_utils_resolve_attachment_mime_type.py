import pytest

from ycc_hull.utils import resolve_attachment_mime_type


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("animation.gif", "image/gif"),
        ("file.GIF", "image/gif"),
        ("IMAGE.PNG", "image/png"),
        ("MiXedCaSe.JpG", "image/jpeg"),
        ("photo.avif", "image/avif"),
        ("PHOTO.AVIF", "image/avif"),
        ("photo.heic", "image/heic"),
        ("PHOTO.HEIC", "image/heic"),
        ("photo.heif", "image/heif"),
        ("Photo.Heif", "image/heif"),
        ("photo.jpeg", "image/jpeg"),
        ("Photo.Jpeg", "image/jpeg"),
        ("photo.jpg", "image/jpeg"),
        ("PHOTO.JPG", "image/jpeg"),
        ("photo.webp", "image/webp"),
        ("PHOTO.WEBP", "image/webp"),
        ("screenshot.png", "image/png"),
        ("archive.backup.jpg", "image/jpeg"),
        ("my.file.name.png", "image/png"),
    ],
)
def test_resolve_attachment_mime_type(filename: str, expected: str) -> None:
    assert resolve_attachment_mime_type(filename) == expected


@pytest.mark.parametrize(
    "filename",
    [
        ".hidden",
        "",
        "noextension",
        "document.pdf",
        "file.xyz123",
        "virus.exe",
    ],
)
def test_resolve_attachment_mime_type_raises_for_unsupported(
    filename: str,
) -> None:
    with pytest.raises(ValueError, match="Unsupported attachment file type"):
        resolve_attachment_mime_type(filename)
