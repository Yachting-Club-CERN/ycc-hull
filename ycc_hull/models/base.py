"""
Base model.
"""

from typing import Any, Generic, TypeVar

from humps import camelize
import lxml
import lxml.etree
import lxml.html
import lxml.html.clean
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.fields import FieldInfo
from ycc_hull.utils import full_type_name

EntityT = TypeVar("EntityT")


class CamelisedBaseModel(BaseModel):
    """
    Base class for all model classes which will convert snake_case attributes to camelCase when converting to JSON.
    """

    model_config = ConfigDict(
        alias_generator=camelize,
        extra="forbid",
        frozen=True,
        populate_by_name=True,
    )

    # We are fighting XSS attacks here, so we need to sanitise all HTML input/output.
    # If you want to mark a field as HTML, use the following syntax:
    #
    # long_description: str | None = Field(json_schema_extra={"html": True})
    #
    # No @classmethod to make it run for subclasses.
    @model_validator(mode="before")
    def sanitise_values(cls, values: dict) -> dict:
        sanitised_values: dict = {}

        # Known fields
        for field_name, field_info in cls.model_fields.items():
            cls._sanitise_value(field_name, field_info, values, sanitised_values)
            cls._sanitise_value(field_info.alias, field_info, values, sanitised_values)
 
        # Unknown fields (keep for validation message)
        for key, value in values.items():
            sanitised_values[key] = cls._sanitise_string(None, value)

        return sanitised_values

    @classmethod
    def _sanitise_value(
        cls,
        key: str | None,
        field_info: FieldInfo,
        values: dict,
        sanitised_values: dict,
    ) -> Any:
        if key in values:
            value = values.pop(key)
            sanitised_values[key] = cls._sanitise_string(field_info, value)

    @staticmethod
    def _sanitise_string(field_info: FieldInfo | None, value: Any) -> Any:
        if isinstance(value, str):
            if (
                field_info
                and field_info.json_schema_extra
                and field_info.json_schema_extra.get("html")  # type: ignore
            ):
                return sanitise_html_input(value)

            return sanitise_text_input(value)

        return value


class CamelisedBaseModelWithEntity(CamelisedBaseModel, Generic[EntityT]):
    """
    Base class for all model classes related to entities.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    entity: EntityT | None = Field(exclude=True, default=None)
    """The entity associated with this model, if available. This allows to write model-oriented code, but still have access to the underlying entity."""

    def get_entity(self) -> EntityT:
        if not self.entity:
            raise ValueError(
                f"No entity is associated with this model: {full_type_name(self.__class__)}{self.model_dump()}"
            )
        return self.entity


def sanitise_text_input(text: str | None) -> str | None:
    if not text:
        return None

    try:
        element = _parse_html(text)

        if element is None:
            return None

        clean_text = (
            lxml.html.clean.Cleaner().clean_html(element).text_content().strip()
        )
        return clean_text if clean_text else None
    except Exception as e:
        raise ValueError(f"Failed to sanitise text input: {text}") from e


def sanitise_html_input(html: str | None) -> str | None:
    if not html:
        return None

    try:
        element = _parse_html(html)

        if element is None:
            return None

        cleaner = lxml.html.clean.Cleaner(
            scripts=True,
            javascript=True,
            comments=True,
            style=True,
            inline_style=True,
            links=True,
            meta=True,
            page_structure=True,
            processing_instructions=True,
            embedded=True,
            frames=True,
            forms=True,
            annoying_tags=True,
            kill_tags=[
                "base",
                "canvas",
                "embed",
                "iframe",
                "object",
                "svg",
            ],
            remove_tags=["table", "tbody", "thead", "tfoot", "tr", "th", "td"],
            remove_unknown_tags=True,
        )
        clean_element = cleaner.clean_html(element)

        # clean_element could be wrapped in an extra <div> or <p> tag, it's OK
        return lxml.etree.tostring(clean_element, encoding="unicode", method="html")
    except Exception as e:
        raise ValueError(f"Failed to sanitise HTML input: {html}") from e


def _parse_html(text: str) -> lxml.html.HtmlElement | None:
    if not text:
        return None
    stripped = text.strip()
    if not stripped:
        return None

    try:
        return lxml.html.fromstring(stripped)
    except Exception as e:
        # Detect lxml.etree.ParseError("Document is empty")
        # (Cannot catch directly)
        if "Document is empty" in str(e):
            return None
        raise ValueError(f"Failed to parse text input: {text}") from e
