import inspect
from functools import partial
from types import UnionType
from typing import Optional, Union, get_type_hints

from ordered_set import OrderedSet
from pydantic import BaseModel

from schemantic.schema.arg_type_info import InitArgTypeInfo
from schemantic.schema.model import SignatureModel
from schemantic.utils.constant import OPTIONAL_MAPPING_KEY, REQUIRED_MAPPING_KEY
from schemantic.utils.mapping import dict_sorted_by_dict_key


def model_arg_alias_to_arg_info(
    model: type[BaseModel], fields_to_exclude: Optional[set[str]] = None, include_private: bool = False
) -> SignatureModel:
    model_schema = model.model_json_schema()
    required = model_schema.get(REQUIRED_MAPPING_KEY, OrderedSet([]))
    try:
        optional = OrderedSet(model_schema["properties"]).difference(required)
    except KeyError as e:
        msg = f"Schemantic does not support untyped arguments, which is present in {model.__name__}"
        raise AttributeError(msg) from e

    result = dict(required={}, optional={})
    for group, arg_type in ((REQUIRED_MAPPING_KEY, required), (OPTIONAL_MAPPING_KEY, optional)):
        arg_to_arg_info = {}
        for name in arg_type:
            if include_private and name.startswith("_") or fields_to_exclude and name in fields_to_exclude:
                """
                The fields_to_exclude kwarg is used by fields_to_exclude_from_single_schema to
                fields_to_exclude developer defined fields from the following schema.
                """
                continue

            arg_property = model_schema["properties"][name]
            if "type" in arg_property:
                arg_type = model_fallback_get(arg_property["type"])

            elif "anyOf" in arg_property:
                type_sequence = [model_fallback_get(one_of["type"]) for one_of in arg_property["anyOf"]]

                arg_type = type_sequence[0] if len(type_sequence) == 1 else f"Any[{', '.join(type_sequence)}]"

            elif "allOf" in arg_property:
                arg_type = f"All[{arg_property['allOf']}]"

            else:
                arg_type = "Unknown"

            arg_to_arg_info[name] = InitArgTypeInfo(
                type_hint=arg_type,
                owner_to_default={model: arg_property.get("default", None)},
            )
        result[group] = dict_sorted_by_dict_key(arg_to_arg_info)

    return SignatureModel(**result)


def class_arg_alias_to_type_string(
    source_cls: type, fields_to_exclude: Optional[set[str]] = None, include_private: bool = False
) -> SignatureModel:
    constructor_signature = inspect.signature(source_cls.__init__)

    result = SignatureModel()

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
            type_sequence = [
                native_fallback_get(type_arg.__name__) for type_arg in type_hint.__args__ if type_arg is not None
            ]
            arg_type = type_sequence[0] if len(type_sequence) == 1 else f"Any[{', '.join(type_sequence)}]"

        else:
            arg_type = native_fallback_get(type_hint.__name__)

        if param.default == inspect.Parameter.empty:
            result.required[param_name] = InitArgTypeInfo(
                type_hint=arg_type, owner_to_default={source_cls: None}
            )
        else:
            result.optional[param_name] = InitArgTypeInfo(
                type_hint=arg_type, owner_to_default={source_cls: param.default}
            )

    return result


def _fallback_get(source: dict, key: str) -> str:
    return source.get(key, key)


_NATIVE_TYPE_TO_NAME = {
    "int": "integer",
    "NoneType": "None",
    "str": "string",
}


_MODEL_TYPE_TO_NAME = {
    "null": "None",
}

native_fallback_get = partial(_fallback_get, _NATIVE_TYPE_TO_NAME)
model_fallback_get = partial(_fallback_get, _MODEL_TYPE_TO_NAME)
