import pytest

from ycc_hull.utils import resolve_attachment_mime_type


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("IMAGE.PNG", "image/png"),
        ("MiXedCaSe.JpG", "image/jpeg"),
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
        "animation.gif",
        "file.GIF",
        # These should be transcoded instead (no general browser support)
        "photo.avif",
        "PHOTO.AVIF",
        "photo.heic",
        "PHOTO.HEIC",
        "photo.heif",
        "Photo.Heif",
        # Abominations
        ".hidden",
        "",
        "photo. jpg",
        "photo._jpg",
        "photo.-jpg",
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
