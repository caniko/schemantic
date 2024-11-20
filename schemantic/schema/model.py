from copy import copy
from functools import reduce
from typing import Annotated, Any, Mapping, TypeAlias

from pydantic import BaseModel, Field, FilePath, model_serializer
from typing_extensions import Doc

from schemantic.schema.arg_type_info import ArgNameToTypeInfo, merge_arg_type_infos
from schemantic.utils.constant import MIXED_MAPPING_KEY, OPTIONAL_MAPPING_KEY, REQUIRED_MAPPING_KEY
from schemantic.utils.mapping import dict_sorted_by_dict_key, extract_sort_keys

LoadedSchema: TypeAlias = Annotated[dict[str, Any], Doc("Schema that has been loaded from a schemantic map or file")]
LoadedOrPathSchema: TypeAlias = Annotated[LoadedSchema | FilePath, Doc("Loaded schema or path to a schema")]
ParsedSchema: TypeAlias = Annotated[
    dict[str, dict[str, Any]], Doc("Schema that has been parsed from a schemantic map or file")
]
NameToInstance: TypeAlias = Annotated[dict[str, Any], Doc("The mapping name of the instance to the instance itself")]

SchemaDefinition: TypeAlias = Annotated[dict[str, Any], Doc("Definition of the outer a schema")]


class ClassNameMixin(BaseModel):
    class_name: str


class DefiningMixin(BaseModel):
    defined: SchemaDefinition = Field(default_factory=dict)


class SignatureModel(BaseModel):
    dump_arg_name_only: bool = Field(False, exclude=True)

    required: ArgNameToTypeInfo = Field(default_factory=dict)
    optional: ArgNameToTypeInfo = Field(default_factory=dict)
    mixed: ArgNameToTypeInfo = Field(default_factory=dict)

    @model_serializer(mode="wrap")
    def serialize_model(self, handler, _info):
        result = handler(self)
        _sort_signature_dump(result, self.dump_arg_name_only)
        return result

    @property
    def all_fields(self) -> ArgNameToTypeInfo:
        return {**self.required, **self.optional, **self.mixed}

    def intersection(self, other: "SignatureModel", dump_arg_name_only: bool = False) -> "SignatureModel":
        required: ArgNameToTypeInfo = copy(self.required)
        optional: ArgNameToTypeInfo = copy(self.optional)
        mixed: ArgNameToTypeInfo = copy(self.mixed)

        _intersection_update_type_info(mixed, other.mixed)
        _merge_new_fields_to_info_trackers(other.required, required, optional, mixed)
        _merge_new_fields_to_info_trackers(other.optional, optional, required, mixed)

        return SignatureModel(
            dump_arg_name_only=dump_arg_name_only,
            required=required,
            optional=optional,
            mixed=mixed,
        )


SignatureModel.model_rebuild()


def merge_signature_models_by_intersection(*signature_models: SignatureModel) -> SignatureModel:
    return reduce(SignatureModel.intersection, signature_models)


def merge_signature_models_by_flattening(*signature_models: SignatureModel) -> ArgNameToTypeInfo:
    return merge_arg_type_infos(*(signature_model.all_fields for signature_model in signature_models))


MixedFields: TypeAlias = Annotated[
    ArgNameToTypeInfo, Doc("List of field names that are mixed required and optional in from other schemas")
]


class CommonSignatureModel(SignatureModel, DefiningMixin):
    dump_arg_name_only: bool = Field(True, exclude=True)


class DefiningSignatureModel(SignatureModel, DefiningMixin):
    pass


class GroupMemberSchema(SignatureModel, ClassNameMixin, DefiningMixin):
    pass


class SingleSchema(DefiningSignatureModel, ClassNameMixin):
    pass


class HomologueSchema(ClassNameMixin):
    common: dict = Field(default_factory=dict)
    instances: Annotated[dict[str, SchemaDefinition], Doc("The definition of each class instance")]
    init_signature: SignatureModel


class GroupSchema(BaseModel):
    common: CommonSignatureModel = Field(default_factory=CommonSignatureModel)
    members: Annotated[dict[str, GroupMemberSchema], Doc("The definition of each group member")]
    argument_to_typing: ArgNameToTypeInfo


class CultureSchema(BaseModel):
    common: CommonSignatureModel = Field(default_factory=CommonSignatureModel)
    culture: Mapping[str, SingleSchema | HomologueSchema | GroupSchema]
    argument_to_typing: ArgNameToTypeInfo


AnySSchema: TypeAlias = Annotated[
    SingleSchema | HomologueSchema | GroupSchema | CultureSchema, Doc("Any schemantic schema type")
]


def _merge_new_fields_to_info_trackers(
    new_fields: ArgNameToTypeInfo,
    target_mapping: ArgNameToTypeInfo,
    mutually_exclusive_mapping: ArgNameToTypeInfo,
    mutually_inclusive_mapping: ArgNameToTypeInfo,
) -> None:
    for field_name, field_info in new_fields.items():
        if field_name in mutually_inclusive_mapping:
            mutually_inclusive_mapping[field_name] |= field_info

        elif existing := mutually_exclusive_mapping.pop(field_name, None):
            assert (
                field_name not in mutually_inclusive_mapping
            ), "Field was just explored in mutually exclusive mapping, it should not be in the mutually inclusive mapping, yet"
            merged = existing | field_info
            if existing_ii := target_mapping.pop(field_name, None):
                merged |= existing_ii
            mutually_inclusive_mapping[field_name] = merged

        elif field_name in target_mapping:
            target_mapping[field_name] |= field_info

        else:
            target_mapping[field_name] = field_info


def _intersection_update_type_info(target: ArgNameToTypeInfo, source: ArgNameToTypeInfo) -> None:
    for s_field_name, s_field_info in source.items():
        if s_field_name in target:
            target[s_field_name] |= s_field_info


def _sort_signature_dump(dumped_schema: dict, dump_arg_name_only: bool = False) -> None:
    sorter = extract_sort_keys if dump_arg_name_only else dict_sorted_by_dict_key

    if REQUIRED_MAPPING_KEY in dumped_schema:
        dumped_schema[REQUIRED_MAPPING_KEY] = sorter(dumped_schema[REQUIRED_MAPPING_KEY])
    if OPTIONAL_MAPPING_KEY in dumped_schema:
        dumped_schema[OPTIONAL_MAPPING_KEY] = sorter(dumped_schema[OPTIONAL_MAPPING_KEY])
    if MIXED_MAPPING_KEY in dumped_schema:
        dumped_schema[MIXED_MAPPING_KEY] = sorter(dumped_schema[MIXED_MAPPING_KEY])
