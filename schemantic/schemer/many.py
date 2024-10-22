from collections.abc import Mapping, Set
from copy import copy
from functools import cached_property
from itertools import chain, combinations
from typing import Any, Callable, Generic, Iterable, Optional, TypeAlias

from ordered_set import OrderedSet
from pydantic import Field, model_validator, validate_call
from typing_extensions import Annotated, Doc, Self

from schemantic.schema.arg_type_info import DUMP_RAW_FIELD_TYPE_INFO_CTX, InitArgTypeInfo
from schemantic.schema.model import (
    CommonSignatureModel,
    CultureSchema,
    GroupMemberSchema,
    GroupSchema,
    HomologueSchema,
    LoadedOrPathSchema,
    LoadedSchema,
    NameToInstance,
    ParsedSchema,
    SchemaDefinition,
    merge_signature_models_by_flattening,
    merge_signature_models_by_intersection,
)
from schemantic.schemer.abstract import AbstractSchemer, HomologousGroupSchemer
from schemantic.schemer.single import Origin, SingleSchemer
from schemantic.utils.constant import (
    ARGUMENT_TO_TYPING_KEY,
    CLASS_NAME_KEY,
    COMMON_MAPPING_KEY,
    CULTURE_KEY,
    DEFINED_MAPPING_KEY,
    GROUP_MEMBER_KEY,
    HOMOLOGUE_INSTANCE_KEY,
)
from schemantic.utils.mapping import dict_sorted_by_dict_key

HomologueNameGetterKwargs: TypeAlias = Annotated[dict[str, Any], Doc("Kwargs to provide the name_getter Callable")]
MappingNameToDefinition: TypeAlias = Annotated[dict[str, SchemaDefinition], Doc("Mapping name to schema definition")]


class HomologueSchemer(HomologousGroupSchemer[HomologueSchema], Generic[Origin]):
    """
    Represents a schema with multiple instances of the same origin, but are uniquely
    identified by their names. This is often useful in situations where you have
    a list of similar objects that each need their own configuration.
    """

    single_schemer: SingleSchemer[Origin]

    instance_name_to_pre_definition: MappingNameToDefinition = Field(default_factory=dict)
    instance_name_getter: Optional[Callable[..., dict[str, SchemaDefinition]]] = None

    schema_alias: Optional[str] = None

    def __hash__(self):
        return hash(self.single_schemer)

    @model_validator(mode="before")
    def instance_names_are_defined(cls, data):
        if not (data.get("instance_name_to_pre_definition", {}) or data.get("instance_name_getter", [])):
            msg = (
                f"Either instance_names or name_getter has to be defined in order to define homologue instances. "
                f"Use {SingleSchemer.__name__} instead if there are no homologous instances, but single instance"
            )
            raise AttributeError(msg)
        return data

    @model_validator(mode="after")
    def ensure_pre_definitions_in_schema(self) -> Self:
        if not self.instance_name_to_pre_definition:
            return self

        all_pre_defined_fields = frozenset(chain.from_iterable(self.instance_name_to_pre_definition.values()))
        if bad_keys := all_pre_defined_fields.difference(self.single_schemer.arg_to_info()):
            raise ValueError(f"Pre defined not a part of the schema:\n{','.join(bad_keys)}")
        return self

    @property
    def origin(self) -> type[Origin]:
        return self.single_schemer.origin

    @property
    def mapping_name(self) -> str:
        return self.schema_alias or self.single_schemer.mapping_name

    def homologue_instance_to_definition(
        self, name_getter_kwargs: Optional[HomologueNameGetterKwargs] = None
    ) -> MappingNameToDefinition:
        result = copy(self.instance_name_to_pre_definition)
        if self.instance_name_getter:
            result.update(self.instance_name_getter(**(name_getter_kwargs or {})))
        return result

    def arg_to_info(self) -> dict[str, InitArgTypeInfo]:
        return self.single_schemer.arg_to_info()

    @validate_call
    def schema(self, name_getter_kwargs: Optional[HomologueNameGetterKwargs] = None) -> HomologueSchema:
        return HomologueSchema(
            class_name=self.origin.__name__,
            common=self.pre_definition_common.get(COMMON_MAPPING_KEY, {}),
            instances=self.homologue_instance_to_definition(name_getter_kwargs),
            init_signature=self.single_schemer.schema_to_fields_to_info(),
        )

    def _schema_parser(
        self,
        loaded_schema: LoadedSchema,
        *,
        _inferior_config_kwargs: Optional[SchemaDefinition] = None,
    ) -> ParsedSchema:
        return {
            name: ({**(_inferior_config_kwargs or {}), **loaded_schema.get(COMMON_MAPPING_KEY, {}), **specific_schema})
            for name, specific_schema in loaded_schema[HOMOLOGUE_INSTANCE_KEY].items()
        }

    def _parse_into_instance_by_mapping_name(
        self, loaded_schema: LoadedSchema, inferior_config_kwargs: SchemaDefinition
    ) -> NameToInstance:
        common = loaded_schema[COMMON_MAPPING_KEY]
        return {
            name: self.origin(**{**inferior_config_kwargs, **common, **instance_kwargs})
            for name, instance_kwargs in self.load_definitions(loaded_schema).items()
        }

    @classmethod
    def from_originating_type(cls, origin: type, **kwargs) -> Self:
        return cls(single_schemer=SingleSchemer.from_origin(origin=origin), **kwargs)

    def logical_post_dump_sort(self, dumped_schema: dict) -> None:
        pass


class GroupSchemer(HomologousGroupSchemer[GroupSchema]):
    """
    Represents a group of SingleSchema objects, and is used when you need to handle multiple models at the same time.
    """

    single_schemers: OrderedSet[SingleSchemer]
    name_to_pre_definition: MappingNameToDefinition = Field(default_factory=dict)

    def __hash__(self):
        return hash(tuple(self.single_schemers))

    def __eq__(self, other) -> bool:
        assert isinstance(other, GroupSchemer)
        return self.single_schemers == other.single_schemers

    @property
    def mapping_name(self) -> str:
        return self.schema_alias or self.__class__.__name__

    @property
    def inner_schema_name_to_schema(self) -> dict[str, SingleSchemer]:
        return {schema.mapping_name: schema for schema in self.single_schemers}

    @cached_property
    def member_label_to_origin(self) -> dict[str, type]:
        return {mapping_name: schema.origin for mapping_name, schema in self.inner_schema_name_to_schema.items()}

    @property
    def schema_alias_to_class(self) -> dict[str, Any]:
        if isinstance(self.single_schemers, Mapping):
            return {alias: model_schema.origin for alias, model_schema in self.single_schemers.items()}
        if isinstance(self.single_schemers, Set):
            return {model_schema.origin.__name__: model_schema.origin for alias, model_schema in self.single_schemers}

        raise ValueError(f"Unsupported type {type(self.single_schemers)}")

    @property
    def common_signature_model(self) -> CommonSignatureModel:
        common_signature = merge_signature_models_by_intersection(
            *(single_schema.signature_model for single_schema in self.single_schemers)
        )
        return CommonSignatureModel(
            defined=self.pre_definition_common,
            **common_signature.model_dump(exclude_defaults=True, context=DUMP_RAW_FIELD_TYPE_INFO_CTX),
        )

    def arg_to_info(self) -> dict[str, InitArgTypeInfo]:
        result: dict[str, InitArgTypeInfo] = {}

        owner_to_arg_to_info = {}

        for single_schema in self.single_schemers:
            owner_to_arg_to_info[single_schema.origin] = single_schema.arg_to_info()
            result.update(single_schema.arg_to_info())

        for (a_owner, a_arg_to_info), (b_owner, b_arg_to_info) in combinations(owner_to_arg_to_info.items(), 2):
            intercept = a_arg_to_info.keys() & b_arg_to_info.keys()
            for intercept_key in intercept:
                merged_info = a_arg_to_info[intercept_key].merge_owner_to_default_with_other(
                    b_arg_to_info[intercept_key]
                )
                if intercept_key in result:
                    merged_info = result[intercept_key].merge_owner_to_default_with_other(merged_info)
                result[intercept_key] = merged_info

        return dict_sorted_by_dict_key(result)

    def schema(self) -> GroupSchema:
        schema_name_to_sub_schema = {
            single_schema.mapping_name: GroupMemberSchema(
                class_name=single_schema.origin.__name__,
                defined=self.name_to_pre_definition.get(single_schema.mapping_name, {}),
                required=single_schema.required,
                optional=single_schema.optional,
            )
            for single_schema in self.single_schemers
        }
        return GroupSchema(
            common=self.common_signature_model,
            members=schema_name_to_sub_schema,
            argument_to_typing=self.arg_to_info(),
        )

    @validate_call
    def _parse_into_instance_by_mapping_name(
        self, loaded_schema: LoadedSchema, inferior_config_kwargs: SchemaDefinition
    ) -> NameToInstance:
        common = loaded_schema[COMMON_MAPPING_KEY][DEFINED_MAPPING_KEY]
        return {
            name: self.member_label_to_origin[name](**{**inferior_config_kwargs, **common, **instance_kwargs})
            for name, instance_kwargs in self.load_definitions(loaded_schema).items()
        }

    @classmethod
    def from_originating_types(cls, origins: Iterable[type] | Mapping[str, type], **kwargs) -> Self:
        return cls(
            single_schemers=(
                OrderedSet(
                    SingleSchemer.from_origin(origin=origin, schema_alias=alias) for alias, origin in origins.items()
                )
                if isinstance(origins, Mapping)
                else OrderedSet(SingleSchemer.from_origin(origin=source_schema) for source_schema in origins)
            ),
            **kwargs,
        )

    def _schema_parser(
        self, loaded_schema: LoadedSchema, *, _inferior_config_kwargs: Optional[SchemaDefinition] = None
    ) -> ParsedSchema:
        result = {}
        common = loaded_schema.pop(COMMON_MAPPING_KEY, {}).get(DEFINED_MAPPING_KEY, {})
        for name, specific_schema in loaded_schema[GROUP_MEMBER_KEY].items():
            pre_specific_config = {**common, **specific_schema[DEFINED_MAPPING_KEY]}
            result[name] = (
                {**_inferior_config_kwargs, **pre_specific_config} if _inferior_config_kwargs else pre_specific_config
            )
        return result

    def logical_post_dump_sort(self, dumped_schema: dict) -> None:
        _ensure_defined_key_in_mapping(dumped_schema, COMMON_MAPPING_KEY)
        for key, member_schema in dumped_schema[GROUP_MEMBER_KEY].items():
            dumped_schema[GROUP_MEMBER_KEY][key] = {
                DEFINED_MAPPING_KEY: member_schema.pop(DEFINED_MAPPING_KEY, {}),
                **member_schema,
            }


class CultureSchemer(AbstractSchemer):
    source_schemers: OrderedSet[SingleSchemer | HomologueSchemer | GroupSchemer]
    common_pre_definitions: SchemaDefinition = Field(default_factory=dict)

    @validate_call
    def schema(
        self,
        homologue_name_getter_kwargs: Optional[HomologueNameGetterKwargs] = None,
    ) -> CultureSchema:
        culture = {}
        signature_models = []

        for schemer in self.source_schemers:
            if isinstance(schemer, SingleSchemer):
                schema = schemer.schema()
                schema.dump_arg_name_only = True
                signature_models.append(schemer.signature_model)

            elif isinstance(schemer, HomologueSchemer):
                schema = schemer.schema(name_getter_kwargs=homologue_name_getter_kwargs)
                schema.init_signature.dump_arg_name_only = True
                signature_models.append(schemer.single_schemer.signature_model)

            elif isinstance(schemer, GroupSchemer):
                schema = schemer.schema()
                for member_schema in schema.members.values():
                    member_schema.dump_arg_name_only = True
                signature_models.append(schemer.common_signature_model)

            else:
                msg = f"{schemer.__class__} is not supported"
                raise NotImplementedError(msg)

            culture[schemer.mapping_name] = schema

        signature_common_schema = merge_signature_models_by_intersection(*signature_models)
        signature_common_schema.dump_arg_name_only = True

        return CultureSchema(
            common=CommonSignatureModel.model_validate(signature_common_schema, from_attributes=True),
            culture=culture,
            argument_to_typing=merge_signature_models_by_flattening(*signature_models),
        )

    def load_definitions(self, schema_finding_info: LoadedOrPathSchema) -> dict:
        loaded_schema = self.ensure_config_is_loaded(schema_finding_info)
        common = loaded_schema.get(COMMON_MAPPING_KEY, {}).get(DEFINED_MAPPING_KEY, {})
        result: ParsedSchema = {}
        for schemer_name, internal in loaded_schema[CULTURE_KEY].items():
            schemer = self._mapping_name_to_schemer[schemer_name]
            result[schemer_name] = schemer._schema_parser(internal, _inferior_config_kwargs=common)
        return result

    def load_into_mapping_name_to_instance(self, schema_finding_info: LoadedOrPathSchema) -> NameToInstance:
        loaded_schema = self.ensure_config_is_loaded(schema_finding_info)
        common = loaded_schema.get(COMMON_MAPPING_KEY, {}).get(DEFINED_MAPPING_KEY, {})
        result: ParsedSchema = {}
        for schemer_name, internal in loaded_schema[CULTURE_KEY].items():
            schemer = self._mapping_name_to_schemer[schemer_name]
            result[schemer_name] = schemer._parse_into_instance_by_mapping_name(internal, inferior_config_kwargs=common)
        return result

    @cached_property
    def _mapping_name_to_schemer(self) -> dict[str, SingleSchemer | HomologueSchemer | GroupSchemer]:
        return {schema.mapping_name: schema for schema in self.source_schemers}

    def logical_post_dump_sort(self, dumped_schema: dict) -> None:
        if COMMON_MAPPING_KEY in dumped_schema:
            _ensure_defined_key_in_mapping(dumped_schema, COMMON_MAPPING_KEY)

        for schemer in self.source_schemers:
            if isinstance(schemer, SingleSchemer):
                _ensure_defined_key_in_mapping(dumped_schema, CULTURE_KEY, schemer.mapping_name)
            if isinstance(schemer, GroupSchemer):
                dumped_schema[CULTURE_KEY][schemer.mapping_name].pop(ARGUMENT_TO_TYPING_KEY)


Schemer: TypeAlias = SingleSchemer | HomologueSchemer | GroupSchemer | CultureSchemer


def _ensure_defined_key_in_mapping(dumped_schema: dict, *target_path: str) -> None:
    target = dumped_schema
    *remaining_path, last_key = target_path

    for path in remaining_path:
        target = target[path]

    new_target = {}
    if CLASS_NAME_KEY in target[last_key]:
        new_target[CLASS_NAME_KEY] = target[last_key].pop(CLASS_NAME_KEY)

    new_target[DEFINED_MAPPING_KEY] = target[last_key].pop(DEFINED_MAPPING_KEY, {})
    new_target.update(target[last_key])

    target[last_key] = new_target
