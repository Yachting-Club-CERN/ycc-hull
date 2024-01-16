"""
Base model.
"""
from typing import Generic, Optional, TypeVar

from humps import camelize
from lxml import etree
from lxml.html import fromstring
from lxml.html.clean import Cleaner
from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    # long_description: Optional[str] = Field(json_schema_extra={"html": True})
    #
    # No @classmethod to make it run for subclasses.
    @model_validator(mode="before")
    def sanitise_strings(cls, values: dict) -> dict:
        for key, value in values.items():
            if isinstance(value, str):
                field_info = cls.model_fields.get(key)
                if (
                    field_info
                    and field_info.json_schema_extra
                    and field_info.json_schema_extra.get("html")  # type: ignore
                ):
                    values[key] = sanitise_html_input(value)
                else:
                    values[key] = sanitise_text_input(value)
        return values


class CamelisedBaseModelWithEntity(CamelisedBaseModel, Generic[EntityT]):
    """
    Base class for all model classes related to entities.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    entity: Optional[EntityT] = Field(exclude=True, default=None)
    """The entity associated with this model, if available. This allows to write model-oriented code, but still have access to the underlying entity."""

    def get_entity(self) -> EntityT:
        if not self.entity:
            raise ValueError(
                f"No entity is associated with this model: {full_type_name(self.__class__)}{self.model_dump()}"
            )
        return self.entity


def sanitise_text_input(text: Optional[str]) -> Optional[str]:
    if not text:
        return None

    element = fromstring(text)
    clean_text = Cleaner().clean_html(element).text_content().strip()
    return clean_text if clean_text else None


def sanitise_html_input(html: Optional[str]) -> Optional[str]:
    if not html:
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

    element = fromstring(html)
    clean_element = cleaner.clean_html(element)

    # clean_element could be wrapped in an extra <div> or <p> tag, it's OK
    return etree.tostring(clean_element, encoding="unicode", method="html")
