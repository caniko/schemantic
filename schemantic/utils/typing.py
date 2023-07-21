from typing import Any, Union

from pydantic import FilePath

from schemantic.model.field_info import FieldMetadata

DefinedSchema = dict[str, Any] | FilePath

SchemaCommonMap = dict[str, dict | list[str]]
SchemaGroupMemberMap = dict[str, str | dict | list[str]]

NameToFieldMetadata = dict[str, FieldMetadata]
NameToStrFieldMetadata = dict[str, str]
