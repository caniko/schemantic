import logging
from copy import deepcopy
from typing import Annotated, Final, TypeAlias

from pydantic import BaseModel, Field, field_validator, model_serializer
from typing_extensions import Doc, Self

from schemantic.utils.mapping import dict_sorted_by_dict_key

logger = logging.getLogger(__file__)
DUMP_RAW_FIELD_TYPE_INFO_KEY: Final[str] = "dump_raw_arg_type_info"
DUMP_RAW_FIELD_TYPE_INFO_CTX: Final[dict] = {DUMP_RAW_FIELD_TYPE_INFO_KEY: True}


OwnerToDefault: TypeAlias = Annotated[
    dict[type, str | None], Doc("Owner to default value mapping. Owner is a class type.")
]


class InitArgTypeInfo(BaseModel, frozen=True):
    type_hint: str
    required_by: list[type] = Field(default_factory=list)
    owner_to_default: OwnerToDefault = Field(default_factory=dict)

    def __hash__(self):
        return self.type_hint

    def __eq__(self, other):
        assert isinstance(other, self.__class__)
        return self.type_hint == other.type_hint

    def __or__(self, other: Self) -> Self:
        if self.type_hint != other.type_hint:
            msg = f"type hints do not match: {self.type_hint} != {other.type_hint}"
            raise AttributeError(msg)

        return self.merge_owner_to_default_with_other(other)

    @field_validator("type_hint")
    @classmethod
    def validate_type_hint(cls, value):
        if value == "str":
            1
        return value

    @model_serializer(mode="wrap")
    def serialize_model(self, handler, info):
        if info.context is not None and info.context.get(DUMP_RAW_FIELD_TYPE_INFO_KEY, False):
            return handler(self)

        default_string = "; ".join(
            f"{owner.__name__} -> {default}"
            for owner, default in sorted(self.owner_to_default.items(), key=lambda kv: kv[0].__name__)
            if default
        )
        if default_string:
            return f"{self.type_hint}(default: {default_string})"
        return self.type_hint

    def merge_owner_to_default_with_other(self, other: Self) -> Self:
        assert self.type_hint == other.type_hint

        if not self.owner_to_default:
            if other.owner_to_default:
                """
                If other has owner_to_default defined, we want to copy it.
                self is currently the tracker of the respective argument state
                """
                return deepcopy(other)

        elif not other.owner_to_default:
            return deepcopy(self)

        # If both have owner_to_default defined, we want to check for conflicts.
        else:
            intersecting_keys = frozenset(self.owner_to_default).intersection(other.owner_to_default)
            if any(self.owner_to_default[key] != other.owner_to_default[key] for key in intersecting_keys):
                msg = f"Owner to default conflicts detected: {self.owner_to_default} and {other.owner_to_default}"
                raise AttributeError(msg)

            result = deepcopy(self)
            result.owner_to_default.update(other.owner_to_default)
            return result

        raise RuntimeError


ArgNameToTypeInfo: TypeAlias = Annotated[dict[str, InitArgTypeInfo], Doc("Field name to type string mapping")]


def merge_arg_type_infos(*arg_name_to_type_infos: ArgNameToTypeInfo) -> ArgNameToTypeInfo:
    result: ArgNameToTypeInfo = {}
    for arg_name_to_type_info in arg_name_to_type_infos:
        for arg_name, arg_info in arg_name_to_type_info.items():
            if arg_name in result:
                result[arg_name] |= arg_info
            else:
                result[arg_name] = deepcopy(arg_info)
    return dict_sorted_by_dict_key(result)
