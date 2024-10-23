from collections.abc import Mapping, Set
from functools import cached_property
from typing import Any, Callable, Generic, Iterable, Optional, Type, TypeVar, TypeAlias

from ordered_set import OrderedSet
from pydantic import BaseModel, field_validator, model_validator, validate_call
from typing_extensions import Self

from schemantic.model.field_info import FieldMetadata, class_field_alias_to_type_string, model_field_alias_to_field_info
from schemantic.model.schematic import Schematic
from schemantic.project import SchemanticProjectMixin
from schemantic.schema.abstract import AbstractSchema, HomologousGroupMixin, AbstractSingleHomologousGroupSchema, AbstractSingleHomologousSchema, \
    ProhibitedKeys
from schemantic.utils.constant import (
    SCHEMA_DEFINED_MAPPING_KEY,
    SCHEMA_FIELD_INFO_MAPPING_KEY,
    SCHEMA_OPTIONAL_MAPPING_KEY,
    SCHEMA_REQUIRED_MAPPING_KEY,
)
from schemantic.utils.misc import update_assert_disjoint
from schemantic.utils.typing import (
    DefinedSchema,
    NameToFieldMetadata,
    NameToStrFieldMetadata,
    SchemaCommonMap,
    SchemaGroupMemberMap,
)

T = TypeVar("T")


class SingleSchema(AbstractSingleHomologousSchema, Generic[T]):
    """
    Used to define the schema of a single class or model.

    origin: Type
        The class or model of interest
    """

    origin: Type[T]
    pre_definitions: dict[str, Any] | None = None

    def __hash__(self):
        return hash(self.origin)

    def __eq__(self, other) -> bool:
        if not isinstance(other, SingleSchema):
            return False
        return self.origin == other.origin

    @property
    def mapping_name(self) -> str:
        return self.schema_alias or self.origin.__name__

    @cached_property
    def schematic(self) -> Schematic:
        kwargs = {}
        if issubclass(self.origin, SchemanticProjectMixin):
            kwargs.update(self.origin.single_schema_kwargs())

        required_optional_to_field_to_info = (
            model_field_alias_to_field_info(self.origin, **kwargs)
            if issubclass(self.origin, BaseModel)
            else class_field_alias_to_type_string(self.origin, **kwargs)
        )

        return Schematic(class_name=self.origin.__name__, **required_optional_to_field_to_info)

    @validate_call
    def schema(
        self, with_defined: bool = False, **schematic_dict_kwargs
    ) -> dict[str, str | dict | list[str] | dict[str, str]]:
        result = self.schematic.schema_dict(with_defined=with_defined, **schematic_dict_kwargs)

        if self.pre_definitions:
            if with_defined:
                result["defined"] = self.pre_definitions
            else:
                if SCHEMA_REQUIRED_MAPPING_KEY in result:
                    for k in result[SCHEMA_REQUIRED_MAPPING_KEY]:
                        if k in self.pre_definitions:
                            result[SCHEMA_REQUIRED_MAPPING_KEY][k] = self.pre_definitions[k]
                if SCHEMA_OPTIONAL_MAPPING_KEY in result:
                    for k in result[SCHEMA_OPTIONAL_MAPPING_KEY]:
                        if k in self.pre_definitions:
                            result[SCHEMA_OPTIONAL_MAPPING_KEY][k] = self.pre_definitions[k]

        return result

    @validate_call
    def parse_schema(
        self,
        defined_schema: DefinedSchema,
        *,
        _inferior_config_kwargs: Optional[dict[str, Any]] = None,
    ) -> dict[str, dict[str, Any]]:
        defined_schema = self._make_sure_defined_schema_is_loaded(defined_schema)

        config_from_file = self._get_configuration_from_mapping(defined_schema, stored_in_defined=True)
        if not _inferior_config_kwargs:
            return config_from_file
        return {**_inferior_config_kwargs, **config_from_file}

    @validate_call
    def parse_schema_to_instance(
        self,
        defined_schema: DefinedSchema,
        *,
        _inferior_config_kwargs: Optional[dict[str, Any]] = None,
    ) -> dict[str, T]:
        """
        Note that SingleSchema uses its sole mapping_name as name here; dict with a single key-value pair

        Parameters
        ----------
        defined_schema
        _inferior_config_kwargs

        Returns
        -------

        """
        return {self.mapping_name: self.origin(**self.parse_schema(defined_schema))}


class HomologueSchema(HomologousGroupMixin, AbstractSingleHomologousSchema, Generic[T]):
    """
    Represents a schema with multiple instances of the same origin, but are uniquely
    identified by their names. This is often useful in situations where you have
    a list of similar objects that each need their own configuration.

    single_schema: SingleSchema
        The single schema to use a reference for the single origin
    instances names: OrderedSet[str]
        The name of each instance of the single schema
    name_getter: Optional[Callable[[...], OrderedSet[str]]]
        Function used to define names when `schema` is called.
        Specifically useful when passing the schema from a library.
    """

    single_schema: SingleSchema[T]
    instance_names: Optional[OrderedSet[str]] = None
    name_getter: Optional[Callable[[...], OrderedSet[str]]] = None

    prohibited_keys: ProhibitedKeys = {"class_name", "common", SCHEMA_DEFINED_MAPPING_KEY, SCHEMA_FIELD_INFO_MAPPING_KEY}

    def __hash__(self):
        return hash(self.single_schema)

    @model_validator(mode="before")
    def instance_names_or_name_getter(cls, data):
        if not (data["instance_names"] or data["name_getter"]):
            msg = (
                f"Either instance_names or name_getter has to be defined in order to define homologue instances. "
                f"Use {SingleSchema.__name__} instead if there are no homologous instances, but single instance"
            )
            raise AttributeError(msg)
        return data

    @model_validator(mode="after")
    def must_have_more_than_one_instance(cls, model):
        if model.name_getter:
            return model

        if len(model.instance_names) == 1:
            msg = (
                "There is no possibility to generate more than one homologue given there is no name_getter defined, "
                "and instance_names only has a single name"
            )
            raise ValueError(msg)

        return model

    @property
    def origin(self) -> Type[T]:
        return self.single_schema.origin

    @property
    def mapping_name(self) -> str:
        return self.schema_alias or self.single_schema.mapping_name

    @validate_call
    def homologue_names(self, name_getter_kwargs: Optional[Mapping[str, Any]] = None) -> OrderedSet[str]:
        """
        Collect all names by combining instance names and the callback from the name_getter

        Parameters
        ----------
        name_getter_kwargs: Optional[Mapping]
            Kwargs to provide the name_getter Callable

        Returns
        -------
        str, names of each single_schema instance
        """
        result = (
            self.instance_names
            if not self.name_getter or not name_getter_kwargs
            else OrderedSet((*self.name_getter(**name_getter_kwargs), *self.instance_names))
        )
        if self._keys_to_not_parse() and any(name in self._keys_to_not_parse() for name in result):
            msg = (
                f"The names {self._keys_to_not_parse().intersection(result)} are not allowed. "
                f"Set of names that cannot be used: {self._keys_to_not_parse()}"
            )
            raise AttributeError(msg)

        return result

    @validate_call
    def schema(
        self, name_getter_kwargs: Optional[dict[str, Any]] = None, with_common: bool = True
    ) -> dict[str, str | dict | list[str] | NameToFieldMetadata]:
        result = dict(class_name=self.origin.__name__)
        if with_common:
            result["common"] = {}

        for name in self.homologue_names(name_getter_kwargs):
            result[name] = self.pre_definitions[name] if self.pre_definitions and name in self.pre_definitions else {}

        result.update(self.single_schema.schematic.schema_dict_field_info_extracted(with_class_name=False))

        return result

    @validate_call
    def parse_schema(
        self,
        defined_schema: DefinedSchema,
        *,
        _inferior_config_kwargs: Optional[dict[str, Any]] = None,
    ) -> dict[str, dict[str, Any]] | dict[str, T]:
        defined_schema = self._make_sure_defined_schema_is_loaded(defined_schema)

        config = self._get_configuration_from_mapping(defined_schema, stored_in_defined=False)
        result = {}
        for name in config:
            if name in self._keys_to_not_parse():
                continue

            pre_specific_config = {**config["common"], **config[name]}

            result[name] = (
                {**_inferior_config_kwargs, **pre_specific_config} if _inferior_config_kwargs else pre_specific_config
            )

        return result

    @validate_call
    def parse_schema_to_instance(
            self,
            defined_schema: DefinedSchema,
            *,
            _inferior_config_kwargs: Optional[dict[str, Any]] = None,
    ) -> dict[str, T]:
        """
        Note that SingleSchema uses its sole mapping_name as name here; dict with a single key-value pair

        Parameters
        ----------
        defined_schema
        _inferior_config_kwargs

        Returns
        -------

        """
        return {
            name: self.origin(**instance_kwargs) for name, instance_kwargs in self.parse_schema(defined_schema).items()
        }

    @classmethod
    def from_originating_type(
        cls,
        origin: Type[T],
        instance_names: Optional[OrderedSet[str]] = None,
        name_getter: Optional[Callable[[...], OrderedSet[str]]] = None,
    ) -> "HomologueSchema":
        return cls(single_schema=SingleSchema(origin=origin), instance_names=instance_names, name_getter=name_getter)


class GroupSchema(HomologousGroupMixin, AbstractSingleHomologousGroupSchema):
    """
    Represents a group of SingleSchema objects, and is used when you need to handle multiple models at the same time.
    """

    single_schemas: OrderedSet[SingleSchema]
    mapping_name: str

    prohibited_keys: ProhibitedKeys = {"common", SCHEMA_FIELD_INFO_MAPPING_KEY}

    def __hash__(self):
        return hash(frozenset(self.single_schemas))

    def __eq__(self, other: Self) -> bool:
        return self.single_schemas == other.single_schemas

    @field_validator("single_schemas")
    def single_schemas_do_not_map_from_prohibited_keys(cls, value):
        if cls.prohibited_keys:
            if intersection := OrderedSet(single_schema.__class__.__name__ for single_schema in value).intersection(
                cls.prohibited_keys
            ):
                msg = (
                    f"The names {intersection} are not allowed. "
                    f"Set of names that cannot be used: {cls.prohibited_keys}"
                )
                raise AttributeError(msg)

            if intersection := OrderedSet(single_schema.schema_alias for single_schema in value).intersection(
                cls.prohibited_keys
            ):
                msg = (
                    f"The names {intersection} are not allowed. "
                    f"Set of names that cannot be used: {cls.prohibited_keys}"
                )
                raise AttributeError(msg)

        return value

    @property
    def schema_mapping_name_to_instance_schema(self) -> dict[str, SingleSchema]:
        return {schema.mapping_name: schema for schema in self.single_schemas}

    @cached_property
    def member_label_to_origin(self) -> dict[str, Type]:
        return {
            mapping_name: schema.origin for mapping_name, schema in self.schema_mapping_name_to_instance_schema.items()
        }

    @property
    def schema_alias_to_class(self) -> dict[str, Any]:
        if isinstance(self.single_schemas, Mapping):
            return {alias: model_schema.origin for alias, model_schema in self.single_schemas.items()}
        if isinstance(self.single_schemas, Set):
            return {model_schema.origin.__name__: model_schema.origin for alias, model_schema in self.single_schemas}

        raise ValueError(f"Unsupported type {type(self.single_schemas)}")

    @validate_call
    def schema_with_field_metadata(
        self,
        with_defined: bool = True,
        with_common: bool = True,
        with_optional: bool = True,
        with_required: bool = True,
    ) -> dict[str, SchemaCommonMap, SchemaGroupMemberMap, NameToFieldMetadata]:
        schema_name_to_sub_schema = {}

        owner_to_field_to_info: dict[Type, dict[str, FieldMetadata]] = {}
        common_field_to_info: dict[str, FieldMetadata] = {}
        field_to_field_info: dict[str, FieldMetadata] = {}
        for single_schema in self.single_schemas:
            name = single_schema.mapping_name
            schema_name_to_sub_schema[name] = dict(class_name=single_schema.origin.__name__)

            if with_defined:
                schema_name_to_sub_schema[name][SCHEMA_DEFINED_MAPPING_KEY] = (
                    self.pre_definitions[name] if self.pre_definitions and name in self.pre_definitions else {}
                )

            if with_required and single_schema.schematic.required:
                schema_name_to_sub_schema[name][SCHEMA_REQUIRED_MAPPING_KEY] = list(single_schema.schematic.required)

            if with_optional and single_schema.schematic.optional:
                schema_name_to_sub_schema[name][SCHEMA_OPTIONAL_MAPPING_KEY] = list(single_schema.schematic.optional)

            owner_to_field_to_info[single_schema.origin] = single_schema.schematic.field_to_info
            field_to_field_info.update(single_schema.schematic.field_to_info)

        for owner, field_to_info in owner_to_field_to_info.items():
            for field, field_info in field_to_info.items():
                for other_owner, other_field_to_info in owner_to_field_to_info.items():
                    if other_owner == owner:
                        continue

                    if field in other_field_to_info:
                        other_info = other_field_to_info[field]
                        if field in common_field_to_info:
                            common_field_to_info[field].merge_owner_to_default_with_other(other_info)
                        else:
                            common_field_to_info[field] = other_info

        result = {}

        if common_field_to_info and with_common:
            required: set[str] = set()
            optional: set[str] = set()
            for _schema_name, schema in schema_name_to_sub_schema.items():
                required.update(schema.get(SCHEMA_REQUIRED_MAPPING_KEY, []))
                optional.update(schema.get("optional", []))

            common_dict = {}
            if with_defined:
                common_dict[SCHEMA_DEFINED_MAPPING_KEY] = (
                    self.pre_definitions[SCHEMA_DEFINED_MAPPING_KEY]
                    if self.pre_definitions and SCHEMA_DEFINED_MAPPING_KEY in self.pre_definitions
                    else {}
                )
            if required:
                common_dict[SCHEMA_REQUIRED_MAPPING_KEY] = list(sorted(required))
            if optional:
                common_dict["optional"] = list(sorted(optional))
            result["common"] = common_dict

        result.update(schema_name_to_sub_schema)

        combined_field_info = field_to_field_info
        if common_field_to_info:
            combined_field_info.update(common_field_to_info)

        result[SCHEMA_FIELD_INFO_MAPPING_KEY] = combined_field_info

        return result

    @validate_call
    def schema(
        self,
        with_defined: bool = True,
        with_common: bool = True,
        with_required: bool = True,
        with_optional: bool = True,
    ) -> dict[str, SchemaCommonMap | SchemaGroupMemberMap | NameToStrFieldMetadata]:
        result = self.schema_with_field_metadata(
            with_common=with_common, with_required=with_required, with_optional=with_optional
        )
        result[SCHEMA_FIELD_INFO_MAPPING_KEY] = {
            field: field_info.field_info_string
            for field, field_info in sorted(result[SCHEMA_FIELD_INFO_MAPPING_KEY].items(), key=lambda kv: kv[0])
        }
        return result

    @validate_call
    def parse_schema(
        self,
        defined_schema: DefinedSchema,
        *,
        _inferior_config_kwargs: Optional[dict[str, Any]] = None,
    ) -> dict[str, dict[str, Any]]:
        defined_schema = self._make_sure_defined_schema_is_loaded(defined_schema)

        config = self._get_configuration_from_mapping(defined_schema, stored_in_defined=False)
        result = {}
        for name, model_schema in self.schema_mapping_name_to_instance_schema.items():
            if name in self._keys_to_not_parse():
                continue

            specific_config = {}
            if _inferior_config_kwargs:
                specific_config.update(_inferior_config_kwargs)
            if "common" in config:
                specific_config.update(config["common"][SCHEMA_DEFINED_MAPPING_KEY])
            specific_config.update(config[name][SCHEMA_DEFINED_MAPPING_KEY])

            result[name] = specific_config

        return result

    @validate_call
    def parse_schema_to_instance(
        self,
        defined_schema: DefinedSchema,
        *,
        _inferior_config_kwargs: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        return {
            name: self.member_label_to_origin[name](**instance_kwargs)
            for name, instance_kwargs in self.parse_schema(defined_schema).items()
        }

    @classmethod
    def from_originating_types(cls, origins: Iterable[Type] | Mapping[str, Type], **kwargs) -> "GroupSchema":
        return cls(
            single_schemas=OrderedSet(
                SingleSchema(origin=origin, schema_alias=alias) for alias, origin in origins.items()
            )
            if isinstance(origins, Mapping)
            else OrderedSet(SingleSchema(origin=source_schema) for source_schema in origins),
            **kwargs,
        )


NotCultureSchema: TypeAlias = SingleSchema | HomologueSchema | GroupSchema


class CultureSchema(AbstractSchema):
    source_schemas: OrderedSet[NotCultureSchema]

    @validate_call
    def schema(
        self,
        with_global_common: bool = True,
        with_micro_common: bool = True,
        homologue_name_getter_kwargs: Optional[dict[str, Any]] = None,
    ) -> dict:
        """
        Field merge strategies:

        Parameters
        ----------
        with_global_common
        with_micro_common
        homologue_name_getter_kwargs

        Returns
        -------

        """

        def combine_field_metadata(new_source: dict[str, FieldMetadata]) -> None:
            for new_field, new_field_info in new_source.items():
                if new_field in fields:
                    fields[new_field].merge_owner_to_default_with_other(new_field_info)
                else:
                    fields[new_field] = new_field_info

        result = {}
        fields: dict[str, FieldMetadata] = {}
        common_required: set[str] = set()
        common_optional: set[str] = set()

        for model_schema in self.source_schemas:
            if isinstance(model_schema, SingleSchema):
                extended = model_schema.schema(with_class_name=True, with_defined=True)
                combine_field_metadata(model_schema.schematic.field_to_info)

                if SCHEMA_REQUIRED_MAPPING_KEY in extended:
                    common_required.update(extended[SCHEMA_REQUIRED_MAPPING_KEY])
                    extended[SCHEMA_REQUIRED_MAPPING_KEY] = list(extended[SCHEMA_REQUIRED_MAPPING_KEY])

                if SCHEMA_OPTIONAL_MAPPING_KEY in extended:
                    common_optional.update(extended[SCHEMA_OPTIONAL_MAPPING_KEY])
                    extended[SCHEMA_OPTIONAL_MAPPING_KEY] = list(extended[SCHEMA_OPTIONAL_MAPPING_KEY])

                result[model_schema.mapping_name] = extended

            elif isinstance(model_schema, HomologueSchema):
                extended = model_schema.schema(with_common=True, name_getter_kwargs=homologue_name_getter_kwargs)

                combine_field_metadata(model_schema.single_schema.schematic.field_to_info)

                if SCHEMA_REQUIRED_MAPPING_KEY in extended:
                    common_required.update(extended[SCHEMA_REQUIRED_MAPPING_KEY])
                if SCHEMA_OPTIONAL_MAPPING_KEY in extended:
                    common_optional.update(extended[SCHEMA_OPTIONAL_MAPPING_KEY])

                del extended[SCHEMA_FIELD_INFO_MAPPING_KEY]
                result[model_schema.mapping_name] = extended

            elif isinstance(model_schema, GroupSchema):
                extended = model_schema.schema_with_field_metadata(
                    with_defined=True, with_optional=True, with_required=True
                )

                combine_field_metadata(extended.pop(SCHEMA_FIELD_INFO_MAPPING_KEY))
                result[model_schema.mapping_name] = extended

            else:
                msg = f"{model_schema.__class__} is not supported"
                raise NotImplementedError(msg)

        result[SCHEMA_FIELD_INFO_MAPPING_KEY] = {
            field: info.field_info_string for field, info in sorted(fields.items(), key=lambda kv: kv[0])
        }

        return result

    @validate_call
    def parse_schema(self, defined_schema: DefinedSchema, keep_mapping_names: bool = True) -> dict[str, dict[str, Any]]:
        defined_schema = self._make_sure_defined_schema_is_loaded(defined_schema)
        result = {}

        for model_schema in self.source_schemas:
            parsed = model_schema.parse_schema(defined_schema[model_schema.mapping_name])
            if keep_mapping_names:
                result[model_schema.mapping_name] = parsed
            else:
                if isinstance(model_schema, SingleSchema):
                    result[model_schema.origin.__name__] = parsed
                else:
                    update_assert_disjoint(
                        result, parsed, f"{model_schema.mapping_name} collides with the existing parsimony."
                    )

        return result

    @validate_call
    def parse_schema_to_instance(self, defined_schema: DefinedSchema) -> dict[str, Any]:
        defined_schema = self._make_sure_defined_schema_is_loaded(defined_schema)

        result = {}
        for model_schema in self.source_schemas:
            update_assert_disjoint(
                result,
                model_schema.parse_schema_to_instance(defined_schema[model_schema.mapping_name]),
                f"{model_schema.mapping_name} collides with the existing parsimony.",
            )

        return result
