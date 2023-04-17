"""
Base model.
"""
from typing import Generic, Optional, TypeVar

from humps import camelize
from lxml.html.clean import Cleaner
from pydantic import BaseModel, Extra, Field
from lxml.html import fromstring
from ycc_hull.utils import full_type_name
from lxml import etree

EntityT = TypeVar("EntityT")


class CamelisedBaseModel(BaseModel):
    """
    Base class for all model classes which will convert snake_case attributes to camelCase when converting to JSON.
    """

    class Config:
        """
        Base config.
        """

        alias_generator = camelize
        allow_population_by_field_name = True
        allow_mutation = False
        extra = Extra.forbid


class CamelisedBaseModelWithEntity(CamelisedBaseModel, Generic[EntityT]):
    """
    Base class for all model classes related to entities.
    """

    entity: Optional[EntityT] = Field(exclude=True)
    """The entity associated with this model, if available. This allows to write model-oriented code, but still have access to the underlying entity."""

    def get_entity(self) -> EntityT:
        if not self.entity:
            raise ValueError(
                f"No entity is associated with this model: {full_type_name(self.__class__)}{self.dict()}"
            )
        return self.entity


def _stringify_children(node):
    from lxml.etree import tostring
    from itertools import chain

    parts = (
        [node.text]
        + list(chain(*([c.text, tostring(c), c.tail] for c in node.getchildren())))
        + [node.tail]
    )
    # filter removes possible Nones in texts and tails
    return "".join(filter(None, parts))


def sanitise_text_input(text: Optional[str]) -> Optional[str]:
    if not text:
        return text

    element = fromstring(text)
    return Cleaner().clean_html(element).text_content().strip()


def sanitise_html_input(html: Optional[str]) -> Optional[str]:
    if not html:
        return html

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
