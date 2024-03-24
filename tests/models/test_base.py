"""
Base DTO tests.
"""

import pytest

from ycc_hull.models.base import sanitise_html_input, sanitise_text_input


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, None),
        ("  ", None),
        (" my text ", "my text"),
        (" <h1> </h1> ", None),
        (" <h1> Hello, World! </h1> ", "Hello, World!"),
        (" <!-- Comment --> ", None),
        (" <!-- Comment  1 --> my text <!-- Comment  2 --> ", "my text"),
    ],
)
def test_sanitise_text_input(value: str, expected: str) -> None:
    assert sanitise_text_input(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, None),
        ("  ", None),
        (" my text ", "<p>my text</p>"),
        (" <h1> </h1> ", "<h1> </h1>"),
        (" <h1> Hello, World! </h1> ", "<h1> Hello, World! </h1>"),
        (" <!-- Comment --> ", None),
        (" <!-- Comment  1 --> my text <!-- Comment  2 --> ", "<p>my text </p>"),
        (
            # Value
            "<em>Really!</em> It <notatag>is</notatag> very \nimportant "
            "<!-- Test -->to get this <script>alert('XSS')</script>done!<blink><p>Thank you!<p>\n"
            '<a href="http://example.com">Hyperlinks are OK</a>\n'
            '<img src="images-are-ok.jpg">\n'
            "<table>NO TABLES!</table> <form>NO FORMS!</form> <input> <button>NO BUTTONS!</button>\n"
            "<object>NO OBJECTS!</object> <embed>NO EMBEDS!</embed>\n"
            "<svg>NO SVGs!</svg> <canvas>NO CANVASES!</canvas>\n"
            "<head>NO HEADS!</head> <title>NO TITLES!</title>\n"
            "<base> <meta> <link> <style>NO STYLES!</style>\n",
            # Expected
            "<div><em>Really!</em> It is very \nimportant to get this done!<p>Thank you!</p><p>\n"
            '<a href="http://example.com">Hyperlinks are OK</a>\n'
            '<img src="images-are-ok.jpg">\n'
            "</p>NO TABLES! NO FORMS!  \n \n \n"
            "NO HEADS! NO TITLES!\n   </div>",
        ),
    ],
)
def test_sanitise_html_input(value: str, expected: str) -> None:
    assert sanitise_html_input(value) == expected
