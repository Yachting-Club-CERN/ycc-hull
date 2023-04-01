"""
Base model.
"""
from humps import camelize
from pydantic import BaseModel


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
