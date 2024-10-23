import inspect
import logging
from types import UnionType
from typing import Literal, Optional, Type, Union, get_type_hints, TypedDict

from ordered_set import OrderedSet
from pydantic import BaseModel, Field, computed_field

from schemantic.utils.constant import SCHEMA_REQUIRED_MAPPING_KEY
from schemantic.utils.misc import dict_sorted_by_dict_key

logger = logging.getLogger(__file__)


class FieldMetadata(BaseModel):
    type_hint: str
    owner_to_default: Optional[dict[Type, str]] = Field(default_factory=dict)

    def __hash__(self):
        return self.type_hint

    @computed_field(return_type=set[str])  # type: ignore[misc]
    @property
    def field_info_string(self) -> str:
        if self.owner_to_default:
            default_string = "; ".join(
                f"{owner.__name__} -> {default}"
                for owner, default in sorted(self.owner_to_default.items(), key=lambda kv: kv[0].__name__)
            )
            return f"{self.type_hint}(default: {default_string})"
        return self.type_hint

    def merge_owner_to_default_with_other(self, other: "FieldMetadata") -> None:
        assert self.type_hint == other.type_hint

        if not self.owner_to_default:
            if other.owner_to_default:
                """
                If other has owner_to_default defined, we want to copy it.
                self is currently the tracker of the respective field state
                """
                self.owner_to_default = other.owner_to_default

            return
        elif not other.owner_to_default:
            return

        owner_intersection = frozenset(self.owner_to_default).intersection(other.owner_to_default)
        if owner_intersection:
            owner_to_differing_defaults = {}
            for duplicate_owner in owner_intersection:
                if self.owner_to_default[duplicate_owner] != other.owner_to_default[duplicate_owner]:
                    owner_to_differing_defaults[duplicate_owner] = (
                        self.owner_to_default[duplicate_owner],
                        other.owner_to_default[duplicate_owner],
                    )
            if owner_to_differing_defaults:
                msg = (
                    f"Owners are defined in both spaces with differing defaults.\n"
                    f"Owner to differing default map: {owner_to_differing_defaults}"
                )
                raise AttributeError(msg)

        self.owner_to_default.update(other.owner_to_default)


class ModelSchemaDict(TypedDict):
    required: dict[str, FieldMetadata]
    optional: dict[str, FieldMetadata]


def model_field_alias_to_field_info(
    model: Type[BaseModel], fields_to_exclude: Optional[set[str]] = None, include_private: bool = False
) -> ModelSchemaDict:
    model_schema = model.model_json_schema()

    required = (
        model_schema[SCHEMA_REQUIRED_MAPPING_KEY] if SCHEMA_REQUIRED_MAPPING_KEY in model_schema else OrderedSet([])
    )
    try:
        optional = OrderedSet(model_schema["properties"]).difference(required)
    except KeyError as e:
        msg = f"Schemantic does not support lazy typing, this was used in {model.__name__}"
        raise AttributeError(msg) from e

    result: ModelSchemaDict = {}
    for group, field_type in (("required", required), ("optional", optional)):
        field_to_field_info = {}
        for name in field_type:
            if include_private and name.startswith("_") or fields_to_exclude and name in fields_to_exclude:
                """
                The fields_to_exclude kwarg is used by fields_to_exclude_from_single_schema to
                fields_to_exclude developer defined fields from the following schema.
                """
                continue

            field_property = model_schema["properties"][name]
            if "type" in field_property:
                field_type = field_property["type"]

            elif "anyOf" in field_property:
                type_sequence = [one_of["type"] for one_of in field_property["anyOf"] if one_of["type"] != "null"]

                field_type = type_sequence[0] if len(type_sequence) == 1 else f"Any[{', '.join(type_sequence)}]"

            elif "allOf" in field_property:
                field_type = f"All[{field_property['allOf']}]"

            else:
                field_type = "Unknown"

            field_to_field_info[name] = FieldMetadata(
                type_hint=field_type,
                owner_to_default={model: field_property["default"]}
                if "default" in field_property and field_property["default"]
                else None,
            )
        result[group] = dict_sorted_by_dict_key(field_to_field_info)

    return result


def class_field_alias_to_type_string(
    source_cls: Type, fields_to_exclude: Optional[set[str]] = None, include_private: bool = False
) -> ModelSchemaDict:
    constructor_signature = inspect.signature(source_cls.__init__)

    result = dict(required={}, optional={})

    type_hints = get_type_hints(source_cls.__init__)
    for param_name, param in constructor_signature.parameters.items():
        if (
            param_name == "self"
            or (not include_private and param_name.startswith("_"))
            or (fields_to_exclude and param_name in fields_to_exclude)
        ):
            continue

        type_hint = type_hints[param_name]

        # The if-test supports both conventional Unions (a | b | c) aka UnionType and typing.Union.
        if isinstance(type_hint, UnionType) or hasattr(type_hint, "__origin__") and type_hint.__origin__ is Union:
            type_sequence = [type_arg.__name__ for type_arg in type_hint.__args__ if type_arg != type(None)]
            field_type = type_sequence[0] if len(type_sequence) == 1 else f"Any[{', '.join(type_sequence)}]"

        else:
            field_type = type_hint.__name__

        if param.default == inspect.Parameter.empty:
            result["required"][param_name] = FieldMetadata(type_hint=field_type)
        else:
            result["optional"][param_name] = FieldMetadata(
                type_hint=field_type, owner_to_default=None if param.default is None else {source_cls: param.default}
            )

    mapped_result = ModelSchemaDict(required=dict_sorted_by_dict_key(result["required"]), optional=dict_sorted_by_dict_key(result["optional"]))

    return mapped_result
