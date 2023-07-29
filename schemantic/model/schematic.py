from functools import cached_property
from typing import Optional

from pydantic import BaseModel, computed_field, model_validator

from schemantic.model.field_info import FieldMetadata
from schemantic.utils.constant import (
    SCHEMA_DEFINED_MAPPING_KEY,
    SCHEMA_FIELD_INFO_MAPPING_KEY,
    SCHEMA_OPTIONAL_MAPPING_KEY,
    SCHEMA_REQUIRED_MAPPING_KEY,
)


class Schematic(BaseModel):
    class_name: str

    required: Optional[dict[str, FieldMetadata]] = None
    optional: Optional[dict[str, FieldMetadata]] = None

    @model_validator(mode="before")
    def required_or_optional(cls, values):
        if SCHEMA_REQUIRED_MAPPING_KEY not in values and SCHEMA_OPTIONAL_MAPPING_KEY not in values:
            msg = "Either required or optional fields must exist in the origin class"
            raise ValueError(msg)
        return values

    @model_validator(mode="after")
    def no_collisions_required_optional(cls, values):
        if not (SCHEMA_REQUIRED_MAPPING_KEY in values and SCHEMA_OPTIONAL_MAPPING_KEY in values):
            return values

        if not frozenset(values[SCHEMA_REQUIRED_MAPPING_KEY]).isdisjoint(values[SCHEMA_OPTIONAL_MAPPING_KEY]):
            msg = "Fields cannot be both required and optional simultaneously"
            raise ValueError(msg)

        return values

    @computed_field(return_type=dict[str, FieldMetadata])
    @cached_property
    def field_to_info(self) -> dict[str, FieldMetadata]:
        result = {}
        if self.required:
            result.update(self.required)
        if self.optional:
            result.update(self.optional)
        return result

    def schema_dict(
        self, with_class_name: bool = True, with_defined: bool = False
    ) -> dict[str, str | dict | dict[str, str]]:
        result = {}

        if with_class_name:
            result["class_name"] = self.class_name

        if with_defined:
            result[SCHEMA_DEFINED_MAPPING_KEY] = {}

        if self.required:
            result[SCHEMA_REQUIRED_MAPPING_KEY] = {
                name: field_info.field_info_string for name, field_info in self.required.items()
            }

        if self.optional:
            result[SCHEMA_OPTIONAL_MAPPING_KEY] = {
                name: field_info.field_info_string for name, field_info in self.optional.items()
            }

        return result

    def schema_dict_field_info_extracted(
        self, with_class_name: bool = False, with_defined: bool = False
    ) -> dict[str, str | dict | list[str] | dict[str, str]]:
        result: dict[str, str | dict | list[str] | dict[str, str]] = self.schema_dict(
            with_class_name=with_class_name,
            with_defined=with_defined,
        )
        field_to_info: dict[str, str] = {}

        if SCHEMA_REQUIRED_MAPPING_KEY in result:
            field_to_info.update(result[SCHEMA_REQUIRED_MAPPING_KEY])
            result[SCHEMA_REQUIRED_MAPPING_KEY] = list(result[SCHEMA_REQUIRED_MAPPING_KEY])

        if SCHEMA_OPTIONAL_MAPPING_KEY in result:
            field_to_info.update(result[SCHEMA_OPTIONAL_MAPPING_KEY])
            result[SCHEMA_OPTIONAL_MAPPING_KEY] = list(result[SCHEMA_OPTIONAL_MAPPING_KEY])

        result[SCHEMA_FIELD_INFO_MAPPING_KEY] = field_to_info

        return result
