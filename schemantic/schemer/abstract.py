from abc import ABC, abstractmethod
from copy import deepcopy
from pathlib import Path
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field, FilePath, validate_call

from schemantic.schema.arg_type_info import InitArgTypeInfo
from schemantic.schema.model import LoadedOrPathSchema, LoadedSchema, NameToInstance, ParsedSchema, SchemaDefinition

Schema = TypeVar("Schema", bound=BaseModel)
T = TypeVar("T")


class AbstractSchemer(BaseModel, Generic[Schema], ABC, arbitrary_types_allowed=True):
    @abstractmethod
    def logical_post_dump_sort(self, dumped_schema: dict) -> None: ...

    @abstractmethod
    def load_into_mapping_name_to_instance(
        self, schema_finding_info: LoadedOrPathSchema
    ) -> dict[str, NameToInstance]: ...

    @validate_call
    def dump(self, dump_path: Path, **schema_kwargs) -> None:
        schema: Schema = self.schema(**schema_kwargs)
        dumped_schema = schema.model_dump(exclude_defaults=True)
        self.logical_post_dump_sort(dumped_schema)

        match dump_path.suffix:
            case ".toml":
                from rtoml import dump

                dump(dumped_schema, dump_path)

            case ".yaml" | ".yml":
                from ruamel.yaml import YAML

                YAML().dump(dumped_schema, dump_path)

            case _:
                raise NotImplementedError(f"{dump_path.suffix} is unsupported")

    @staticmethod
    def load(schema_path: FilePath) -> dict:
        match schema_path.suffix:
            case ".toml":
                from rtoml import load

                return load(schema_path, none_value="null")

            case ".yaml" | ".yml":
                from ruamel.yaml import YAML

                return dict(YAML().load(schema_path))

            case _:
                msg = f"{schema_path.suffix} is unsupported"
                raise NotImplementedError(msg)

    def ensure_config_is_loaded(self, schema_finding_info: LoadedOrPathSchema) -> LoadedSchema:
        if isinstance(schema_finding_info, Path):
            return self.load(schema_finding_info)
        if isinstance(schema_finding_info, dict):
            return deepcopy(schema_finding_info)

        raise TypeError(f"{schema_finding_info} is not a valid type")


Schemer = TypeVar("Schemer", bound=AbstractSchemer)


class AbstractSingleHomologousGroupSchemer(AbstractSchemer[Schema], Generic[Schema], ABC):
    schema_alias: Optional[str] = None

    @abstractmethod
    def _schema_parser(
        self,
        loaded_schema: LoadedSchema,
        *,
        _inferior_config_kwargs: Optional[SchemaDefinition] = None,
    ) -> ParsedSchema: ...

    @abstractmethod
    def _parse_into_instance_by_mapping_name(
        self, loaded_schema: LoadedSchema, inferior_config_kwargs: SchemaDefinition
    ) -> NameToInstance: ...

    @property
    @abstractmethod
    def mapping_name(self) -> str: ...

    @abstractmethod
    def arg_to_info(self) -> dict[str, InitArgTypeInfo]: ...

    @validate_call
    def load_into_mapping_name_to_instance(self, schema_finding_info: LoadedOrPathSchema) -> dict[str, NameToInstance]:
        """
        Load schema and parse it into a dictionary of instances.
        """
        loaded_schema = self.ensure_config_is_loaded(schema_finding_info)
        return self._parse_into_instance_by_mapping_name(loaded_schema, {})

    @validate_call
    def load_definitions(
        self,
        schema_finding_info: LoadedOrPathSchema,
        *,
        _inferior_config_kwargs: Optional[SchemaDefinition] = None,
    ) -> ParsedSchema:
        """
        Load schema and parse it into a dictionary of configuration.

        Example
        -------
        >>> schemer = MySchemer()
        >>> schemer.load_definitions("path/to/schema.toml")
        ... {"config1": {"key1": "value1"}, "config2": {"key2": "value2"}}
        """
        defined_schema = self.ensure_config_is_loaded(schema_finding_info)
        return self._schema_parser(defined_schema, _inferior_config_kwargs=_inferior_config_kwargs)


class HomologousGroupSchemer(AbstractSingleHomologousGroupSchemer[Schema], Generic[Schema], ABC):
    pre_definition_common: SchemaDefinition = Field(default_factory=dict)
