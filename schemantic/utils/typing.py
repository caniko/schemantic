from typing import Any, TypeAlias

from pydantic import FilePath

from schemantic.model.field_info import FieldMetadata




DefinedSchema: TypeAlias = dict[str, Any] | FilePath

SchemaCommonMap: TypeAlias = dict[str, dict | list[str]]
SchemaGroupMemberMap: TypeAlias = dict[str, str | dict | list[str]]

NameToFieldMetadata: TypeAlias = dict[str, FieldMetadata]
NameToStrFieldMetadata: TypeAlias = dict[str, str]
