from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field, model_validator, validate_call
from typing_extensions import Annotated, Doc, Self

from schemantic.project import SchemanticProjectMixin
from schemantic.schema.arg_type_info import DUMP_RAW_FIELD_TYPE_INFO_CTX, ArgNameToTypeInfo, InitArgTypeInfo
from schemantic.schema.functional import class_arg_alias_to_type_string, model_arg_alias_to_arg_info
from schemantic.schema.model import (
    DefiningSignatureModel,
    LoadedSchema,
    ParsedSchema,
    SchemaDefinition,
    SignatureModel,
    SingleSchema,
)
from schemantic.schemer.abstract import AbstractSingleHomologousGroupSchemer
from schemantic.utils.constant import DEFINED_MAPPING_KEY

Origin = TypeVar("Origin")


class SingleSchemer(AbstractSingleHomologousGroupSchemer[SingleSchema], Generic[Origin]):
    """
    Schema of a class; supports dataclass and Pydantic models.

    Notes
    -----
    - Use higher order pre-definition when used in homologue, group, or culture.
    """

    origin: Annotated[type[Origin], Doc("The class or model of interest")]

    required: ArgNameToTypeInfo = Field(default_factory=dict)
    optional: ArgNameToTypeInfo = Field(default_factory=dict)
    pre_definition: SchemaDefinition = Field(default_factory=dict)

    def __hash__(self):
        return hash(self.origin)

    def __eq__(self, other) -> bool:
        if not isinstance(other, SingleSchemer):
            return False
        return self.origin == other.origin

    @model_validator(mode="after")
    def ensure_pre_definitions_in_schema(self) -> Self:
        if not self.pre_definition:
            return self

        bad_keys = set(self.pre_definition)
        if self.required:
            bad_keys = bad_keys.difference(self.required)
        if self.optional:
            bad_keys = bad_keys.difference(self.optional)

        if bad_keys:
            raise ValueError(f"Pre defined not a part of the schema:\n{','.join(bad_keys)}")

        return self

    @model_validator(mode="after")
    def either_required_or_optional(self):
        if not (self.required or self.optional):
            msg = "Either self.required or self.optional fields must exist in the origin class"
            raise ValueError(msg)

        return self

    @model_validator(mode="after")
    def no_collisions_required_optional(self):
        if not (self.required and self.optional):
            return self

        if not frozenset(self.required).isdisjoint(self.optional):
            msg = "Fields cannot be both required and self.optional simultaneously"
            raise ValueError(msg)

        return self

    @classmethod
    def from_origin(
        cls, origin: type, schema_alias: Optional[str] = None, pre_definition: Optional[SchemaDefinition] = None
    ) -> Self:
        kwargs = {}
        if issubclass(origin, SchemanticProjectMixin):
            kwargs.update(origin.single_schema_kwargs())

        signature_model = (
            model_arg_alias_to_arg_info(origin, **kwargs)
            if issubclass(origin, BaseModel)
            else class_arg_alias_to_type_string(origin, **kwargs)
        )
        return cls(
            origin=origin,
            schema_alias=schema_alias,
            pre_definition=pre_definition or {},
            **signature_model.model_dump(exclude_defaults=True, context=DUMP_RAW_FIELD_TYPE_INFO_CTX),
        )

    @property
    def mapping_name(self) -> str:
        return self.schema_alias or self.origin.__name__

    def arg_to_info(self) -> dict[str, InitArgTypeInfo]:
        result = {}
        result.update(self.required)
        result.update(self.optional)
        return result

    def schema_to_fields_to_info(self) -> SignatureModel:
        return SignatureModel(required=self.required, optional=self.optional)

    def serialized_defining_schema(self) -> DefiningSignatureModel:
        return DefiningSignatureModel(required=self.required, optional=self.optional)

    def schema(self) -> SingleSchema:
        return SingleSchema(
            class_name=self.origin.__name__,
            defined=self.pre_definition,
            required=self.required,
            optional=self.optional,
        )

    @validate_call
    def parse_into_instance(self, defined_schema: SchemaDefinition) -> Origin:
        return self.origin(**self.load_definitions(defined_schema))

    @validate_call
    def _parse_into_instance_by_mapping_name(
        self, loaded_schema: LoadedSchema, inferior_config_kwargs: SchemaDefinition
    ) -> dict[str, Origin]:
        """
        Note that SingleSchema uses its sole mapping_name as name here; dict with a single key-value pair
        """
        return {self.origin.__name__: self.origin(**{**inferior_config_kwargs, **loaded_schema[DEFINED_MAPPING_KEY]})}

    @property
    def signature_model(self) -> SignatureModel:
        return SignatureModel(required=self.required, optional=self.optional)

    def logical_post_dump_sort(self, dumped_schema: dict) -> None:
        pass

    def _schema_parser(
        self,
        loaded_schema: LoadedSchema,
        *,
        _inferior_config_kwargs: Optional[SchemaDefinition] = None,
    ) -> ParsedSchema:
        config_from_file = loaded_schema[DEFINED_MAPPING_KEY]
        if not _inferior_config_kwargs:
            return config_from_file
        return {**_inferior_config_kwargs, **config_from_file}
