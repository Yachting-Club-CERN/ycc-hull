"""
Base model.
"""

from datetime import datetime
from typing import Any, Generic, TypeVar

import lxml
import lxml.etree
import lxml.html
import lxml.html.clean
from humps import camelize
from lxml_html_clean import Cleaner, clean_html
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.fields import FieldInfo

from ycc_hull.utils import TIME_ZONE, full_type_name

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
    @model_validator(mode="before")
    @classmethod
    def sanitise_values(cls, values: dict) -> dict:
        sanitised_values: dict = {}

        # Known fields
        for field_name, field_info in cls.model_fields.items():
            cls._extract_and_sanitise_value(
                field_name, field_info, values, sanitised_values
            )
            cls._extract_and_sanitise_value(
                field_info.alias, field_info, values, sanitised_values
            )

        # Unknown fields (keep for validation message)
        for key, value in values.items():
            sanitised_values[key] = cls._sanitise_value(None, value)

        return sanitised_values

    @classmethod
    def _extract_and_sanitise_value(
        cls,
        key: str | None,
        field_info: FieldInfo,
        values: dict,
        sanitised_values: dict,
    ) -> Any:
        if key in values:
            value = values.pop(key)
            sanitised_values[key] = cls._sanitise_value(field_info, value)

    @staticmethod
    def _sanitise_value(field_info: FieldInfo | None, value: Any) -> Any:
        is_str = isinstance(value, str)
        is_datetime = isinstance(value, datetime)
        is_datetime_field = field_info and field_info.annotation in (
            datetime,
            datetime | None,
        )

        if is_datetime or is_datetime_field:
            if value is None or is_str or is_datetime:
                return sanitise_datetime_input(value)

            msg_field = " for field {field_info.alias}" if field_info else ""
            raise ValueError(
                f"Invalid datetime value{msg_field}: {value} (type: {type(value)})"
            )

        if is_str and _get_field_info_extra_bool(field_info, "sanitise", True):
            if _get_field_info_extra_bool(field_info, "html", False):
                return sanitise_html_input(value)
            return sanitise_text_input(value)

        return value


def _get_field_info_extra_bool(
    field_info: FieldInfo | None, key: str, default: bool
) -> bool:
    if field_info and field_info.json_schema_extra:
        value = field_info.json_schema_extra.get(key, default)  # type: ignore

        if isinstance(value, bool):
            return value

        raise ValueError(f"Invalid value for JSON schema extra key '{key}': {value}")

    return default


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

        clean_text = clean_html(element).text_content().strip()
        return clean_text if clean_text else None
    except Exception as exc:
        raise ValueError(f"Failed to sanitise text input: {text}") from exc


def sanitise_html_input(html: str | None) -> str | None:
    if not html:
        return None
    if sanitise_text_input(html) is None:
        return None

    try:
        element = _parse_html(html)

        if element is None:
            return None

        cleaner = Cleaner(
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
    except Exception as exc:
        raise ValueError(f"Failed to sanitise HTML input: {html}") from exc


def _parse_html(text: str) -> lxml.html.HtmlElement | None:
    if not text:
        return None
    stripped = text.strip()
    if not stripped:
        return None

    try:
        return lxml.html.fromstring(stripped)
    except Exception as exc:
        # Detect lxml.etree.ParseError("Document is empty")
        # (Cannot catch directly)
        if "Document is empty" in str(exc):
            return None
        raise ValueError(f"Failed to parse text input: {text}") from exc


def sanitise_datetime_input(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None

    # Pydantic converts str to datetime, but does not add the time zone
    if isinstance(value, str):
        value = sanitise_text_input(value)
        if value is None:
            return None

        value = datetime.fromisoformat(value)

    if not isinstance(value, datetime):
        raise ValueError(f"Invalid datetime value: {value}")

    if value.tzinfo is None:
        return TIME_ZONE.localize(value)

    return value.astimezone(TIME_ZONE)
