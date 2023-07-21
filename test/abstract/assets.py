from copy import deepcopy
from dataclasses import dataclass
from typing import Optional, Union

from ordered_set import OrderedSet
from pydantic import BaseModel, computed_field

from schemantic.project import SchemanticProjectMixin, SchemanticProjectModelMixin
from schemantic.schema.main import CultureSchema, GroupSchema, HomologSchema, SingleSchema


class TestClass(SchemanticProjectMixin):
    def __init__(
        self,
        must_be: int,
        we: str = "n",
        n: None = None,
        age: Optional[int] = None,
        new_age: int | str | None = None,
        exclude_me: Optional[int] = None,
        _exclude_me_too: Optional[float] = None,
    ):
        pass

    @classmethod
    @property
    def fields_to_exclude_from_single_schema(cls) -> set[str]:
        upstream = super().fields_to_exclude_from_single_schema
        upstream.update(("exclude_me",))
        return upstream


class OtherTestClass:
    def __init__(self, we: str = "n"):
        pass


@dataclass
class TestDataclass(SchemanticProjectMixin):
    must_be: int
    we: str = "n"

    n: None = None
    age: Optional[int] = None
    new_age: int | str | None = None

    exclude_me: Optional[int] = None
    _exclude_me_too: Optional[float] = None

    @classmethod
    @property
    def fields_to_exclude_from_single_schema(cls) -> set[str]:
        upstream = super().fields_to_exclude_from_single_schema
        upstream.update(("exclude_me",))
        return upstream


@dataclass
class OtherTestDataclass:
    we: str = "n"


class TestModel(SchemanticProjectModelMixin, BaseModel):
    must_be: int
    we: str = "n"

    n: None = None
    age: Optional[int] = None
    new_age: int | str | None = None

    exclude_me: Optional[int] = None
    _exclude_me_too: Optional[float] = None

    @classmethod  # type: ignore[misc]
    @computed_field(return_type=set[str])
    @property
    def fields_to_exclude_from_single_schema(cls) -> set[str]:
        upstream = super().fields_to_exclude_from_single_schema
        upstream.update(("exclude_me",))
        return upstream


class OtherTestModel(BaseModel):
    we: str = "d"


class_single_schema = SingleSchema(origin=TestClass, schema_alias="single_test")
class_homolog_schema = HomologSchema(
    single_schema=deepcopy(class_single_schema),
    instance_names=OrderedSet(("test_1", "test_2")),
    schema_alias="homolog_test",
)
class_group_schema = GroupSchema.from_originating_types(
    origins=OrderedSet((TestClass, OtherTestClass)), mapping_name="group_test"
)
class_culture_schema = CultureSchema(
    source_schemas=OrderedSet(
        (deepcopy(class_single_schema), deepcopy(class_homolog_schema), deepcopy(class_group_schema))
    )
)


dataclass_single_schema = SingleSchema(origin=TestDataclass, schema_alias="single_test")
dataclass_homolog_schema = HomologSchema(
    single_schema=deepcopy(dataclass_single_schema),
    instance_names=OrderedSet(("test_1", "test_2")),
    schema_alias="homolog_test",
)
dataclass_group_schema = GroupSchema.from_originating_types(
    origins=OrderedSet((TestDataclass, OtherTestDataclass)), mapping_name="group_test"
)
dataclass_culture_schema = CultureSchema(
    source_schemas=OrderedSet(
        (deepcopy(dataclass_single_schema), deepcopy(dataclass_homolog_schema), deepcopy(dataclass_group_schema))
    )
)


model_single_schema = SingleSchema(origin=TestModel, schema_alias="single_test")
model_homolog_schema = HomologSchema(
    single_schema=deepcopy(model_single_schema),
    instance_names=OrderedSet(("test_1", "test_2")),
    schema_alias="homolog_test",
)
model_group_schema = GroupSchema.from_originating_types(
    origins=OrderedSet((TestModel, OtherTestModel)), mapping_name="group_test"
)
model_culture_schema = CultureSchema(
    source_schemas=OrderedSet(
        (deepcopy(model_single_schema), deepcopy(model_homolog_schema), deepcopy(model_group_schema))
    )
)
