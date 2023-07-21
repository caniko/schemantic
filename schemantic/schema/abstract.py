from abc import ABC, abstractmethod
from copy import copy
from pathlib import Path
from typing import Any, ClassVar, Optional

from pydantic import BaseModel, FilePath, computed_field, validate_call

from schemantic.utils.constant import (
    SCHEMA_DEFINED_MAPPING_KEY,
    SCHEMA_OPTIONAL_MAPPING_KEY,
    SCHEMA_REQUIRED_MAPPING_KEY,
)
from schemantic.utils.typing import DefinedSchema


class BaseSchema(BaseModel, ABC, arbitrary_types_allowed=True):
    prohibited_keys: ClassVar[set[str]] = set()

    @abstractmethod
    def schema(self, *args, **kwargs):
        ...

    @abstractmethod
    def parse_schema(self, defined_schema: DefinedSchema) -> dict[str, dict[str, Any]]:
        ...

    @abstractmethod
    def parse_schema_to_instance(self, defined_schema: DefinedSchema) -> dict[str, Any]:
        ...

    @validate_call
    def dump(self, dump_path: Path, **schema_kwargs) -> None:
        schema = self.schema(**schema_kwargs)

        match dump_path.suffix:
            case ".toml":
                from rtoml import dump

                dump(schema, dump_path)

            case ".yaml" | ".yml":
                from ruamel.yaml import YAML

                YAML().dump(schema, dump_path)

            case _:
                msg = f"{dump_path.suffix} is unsupported"
                raise NotImplementedError(msg)

    @staticmethod
    @validate_call
    def load(schema_path: FilePath) -> dict:
        match schema_path.suffix:
            case ".toml":
                from rtoml import load

                return load(schema_path)

            case ".yaml" | ".yml":
                from ruamel.yaml import YAML

                return YAML().load(schema_path)

            case _:
                msg = f"{schema_path.suffix} is unsupported"
                raise NotImplementedError(msg)

    @classmethod  # type: ignore[misc]
    @computed_field(return_type=set[str])
    @property
    def _keys_to_not_parse(cls) -> set[str]:
        result = copy(cls.prohibited_keys) if cls.prohibited_keys else set()
        result.update((SCHEMA_REQUIRED_MAPPING_KEY, SCHEMA_OPTIONAL_MAPPING_KEY))
        return result

    @validate_call
    def _make_sure_defined_schema_is_loaded(self, defined_schema: DefinedSchema) -> dict[str, Any]:
        if isinstance(defined_schema, Path):
            defined_schema = self.load(defined_schema)
        return defined_schema

    @validate_call
    def _get_configuration_from_mapping(self, source: dict, *, stored_in_defined: bool) -> dict[str, Any]:
        try:
            result = source[self.mapping_name]
        except KeyError:
            # The provided schema may be a shallow definition;
            # no self.mapping_name resolution needed.
            result = source

        return result[SCHEMA_DEFINED_MAPPING_KEY] if stored_in_defined else result


class NotCultureSchema(BaseSchema, ABC):
    @abstractmethod
    def parse_schema(
        self,
        defined_schema: DefinedSchema,
        *,
        _inferior_config_kwargs: Optional[dict[str, Any]] = None,
    ) -> dict[str, dict[str, Any]]:
        ...

    @abstractmethod
    def parse_schema_to_instance(
        self,
        defined_schema: DefinedSchema,
        *,
        _inferior_config_kwargs: Optional[dict[str, Any]] = None,
    ):
        ...


class SingleHomologousSchema(NotCultureSchema, ABC):
    schema_alias: Optional[str] = None

    @property
    @abstractmethod
    def mapping_name(self) -> str:
        ...

    @validate_call
    def parse_schema_to_instance(
        self,
        defined_schema: DefinedSchema,
        *,
        _inferior_config_kwargs: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
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
