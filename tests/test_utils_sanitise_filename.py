import pytest

from ycc_hull.utils import sanitise_filename


@pytest.mark.parametrize(
    ("original", "expected"),
    [
        # Already safe - no change
        ("photo.jpg", "photo.jpg"),
        ("my-file.png", "my-file.png"),
        ("image_001.jpeg", "image_001.jpeg"),
        # .tar.XYZ
        ("archive.tar", "archive.tar"),
        ("archive.tar.gz", "archive.tar.gz"),
        ("guitar.gz", "guitar.gz"),
        ("archive.TaR.WHATevER", "archive.tar.whatever"),
        ("archive.tar.bz2", "archive.tar.bz2"),
        ("archive.tar.xz", "archive.tar.xz"),
        ("archive.tar.zst", "archive.tar.zst"),
        # Very long filenames
        ("a" * 250 + ".jpg", "a" * 46 + ".jpg"),
        # Spaces become underscores
        ("my photo.jpg", "my_photo.jpg"),
        ("my  photo.jpg", "my_photo.jpg"),
        ("hello world test.png", "hello_world_test.png"),
        # French accents
        ("café.jpg", "cafe.jpg"),
        ("résumé.png", "resume.png"),
        ("château.jpg", "chateau.jpg"),
        ("Noël.png", "noel.png"),
        ("crème brûlée.jpg", "creme_brulee.jpg"),
        ("garçon.jpg", "garcon.jpg"),
        ("français.png", "francais.png"),
        # Hungarian accents
        ("kávé.jpg", "kave.jpg"),
        ("tükör.png", "tukor.png"),
        ("főnök.jpg", "fonok.jpg"),
        ("ülés.png", "ules.png"),
        ("Győr.jpg", "gyor.jpg"),
        ("Ők.png", "ok.png"),
        ("Űrhajó.jpg", "urhajo.jpg"),
        # Hungarian - all accented vowels
        ("áéíóöőúüű.jpg", "aeiooouuu.jpg"),
        ("ÁÉÍÓÖŐÚÜŰ.jpg", "aeiooouuu.jpg"),
        ("Árvíztűrő tükörfúrógép.jpg", "arvizturo_tukorfurogep.jpg"),
        # German
        ("Straße.jpg", "strasse.jpg"),
        ("Ärger.png", "arger.png"),
        ("über.jpg", "uber.jpg"),
        ("Höhe.png", "hohe.png"),
        # Polish
        ("łódź.jpg", "lodz.jpg"),
        ("Łódź.png", "lodz.png"),
        # Scandinavian
        ("Ørsted.jpg", "orsted.jpg"),
        ("fjørd.png", "fjord.png"),
        # Special characters stripped
        ("photo (1).jpg", "photo_1.jpg"),
        ("file [copy].png", "file_copy.png"),
        ("hello@world.jpg", "helloworld.jpg"),
        ("test#file.png", "testfile.png"),
        ("a&b.jpg", "ab.jpg"),
        # HTML injection attempt - neutralised
        ('<img src=x onerror="alert(1)">.jpg', "img_srcx_onerroralert1.jpg"),
        ("<script>alert('xss')</script>.png", "script.png"),
        # Consecutive same-separators collapsed
        ("a___b.jpg", "a_b.jpg"),
        ("a---b.jpg", "a-b.jpg"),
        ("a_-_b.jpg", "a_-_b.jpg"),
        # Leading/trailing underscores stripped
        ("_photo.jpg", "photo.jpg"),
        ("photo_.jpg", "photo.jpg"),
        ("__photo__.jpg", "photo.jpg"),
        # Multiple dots - preserved (last one is extension)
        ("my.file.name.jpg", "my.file.name.jpg"),
        # Unicode quotation marks and smart quotes
        ("\u201cphoto\u201d.jpg", "photo.jpg"),
        # Emoji stripped
        ("photo\U0001f4f8.jpg", "photo.jpg"),
        # Chinese/Japanese/Korean - stripped, fallback stem
        ("写真.jpg", "file.jpg"),
        # Mixed: accented + spaces + special chars
        ("Réunion d'équipe (été 2026).jpg", "reunion_dequipe_ete_2026.jpg"),
        # Extension case normalisation
        ("PHOTO.JPG", "photo.jpg"),
        ("Photo.JPG", "photo.jpg"),
        ("!!!.JPG", "file.jpg"),
        # Edge cases: no abominations
        ("", "file"),
        (".jpg", "file.jpg"),
        ("  ", "file"),
        (".", "file"),
        ("Photo. JPG", "photo._jpg"),
        ("Photo._JPG", "photo._jpg"),
        ("Photo.-JPG", "photo.-jpg"),
        ("README", "readme"),
        ("README.", "readme"),
        ("README..", "readme"),
        ("README...", "readme"),
        ("README. ", "readme"),
        ("..jpg", "file.jpg"),
        ("...jpg", "file.jpg"),
        ("-...jpg", "file.jpg"),
        ("__...jpg", "file.jpg"),
        ("..foo.jpg", "foo.jpg"),
        ("a..jpg", "a.jpg"),
        ("a...jpg", "a.jpg"),
        ("a...b.jpg", "a.b.jpg"),
        ("a.--__--_.-..b.jpg", "a.-_-_.-.b.jpg"),
        (r"C:\Users\docs\file-x.jpg", "file-x.jpg"),
        ("path/to/file-x.jpg", "file-x.jpg"),
        ("test\x00fi\x01\x02\x03le.j\x00p\x01\x02\x03g", "testfile.jpg"),
        # Extension longer than max length - truncated, stem keeps 1 char
        ("x." + "a" * 60, "x." + "a" * 48),
        # Extension exactly at max length - stem gets 1 char
        ("hello." + "a" * 49, "h." + "a" * 48),
        # Long chained extensions within budget - stem truncated normally
        ("report.p7m.p7m.p7m.pdf", "report.p7m.p7m.p7m.pdf"),
        # Long chained extensions exceeding budget - stem (with inner dots) truncated
        ("a" * 50 + ".p7m.p7m.p7m.pdf", "a" * 46 + ".pdf"),
        # No room for stem at all - ext truncated to limit-1
        ("ab." + "z" * 100, "a." + "z" * 48),
    ],
)
def test_sanitise_filename(original: str, expected: str) -> None:
    assert sanitise_filename(original) == expected


def test_sanitise_filename_never_exceeds_max_length() -> None:
    from ycc_hull.utils import _SANITISED_FILENAME_MAX_LENGTH

    cases = [
        "x." + "a" * 200,
        "." + "b" * 200,
        "a" * 200 + "." + "c" * 200,
        "hello." + "p7m." * 30 + "pdf",
        "a" * 200 + ".tar." + "z" * 200,
    ]
    for original in cases:
        result = sanitise_filename(original)
        assert len(result) <= _SANITISED_FILENAME_MAX_LENGTH, (
            f"sanitise_filename({original!r}) = {result!r} "
            f"(len {len(result)} > {_SANITISED_FILENAME_MAX_LENGTH})"
        )
        assert len(result) >= 1
