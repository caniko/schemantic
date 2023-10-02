from copy import deepcopy
from test.schema.base import OtherTestClass, OtherTestDataclass, OtherTestModel, TestClass, TestDataclass, TestModel
from typing import Any

from ordered_set import OrderedSet

from schemantic import GroupSchema, HomologSchema, SingleSchema

SINGLE_PRE_DEFINITION = dict(new_age=3)
HOMOLOG_PRE_DEFINITION = dict(test_1=dict(new_age=4))


def group_pre_definition(main: type, other: type) -> dict[str, dict[str, Any]]:
    return {main.__name__: dict(new_age="can"), other.__name__: dict(new_age="cant")}


class_group_pre_definitions = group_pre_definition(TestClass, OtherTestClass)
dataclass_group_pre_definitions = group_pre_definition(TestDataclass, OtherTestDataclass)
model_group_pre_definitions = group_pre_definition(TestModel, OtherTestModel)


class_single_with_pre_def_schema = SingleSchema(
    origin=TestClass, schema_alias="single_test", pre_definitions=SINGLE_PRE_DEFINITION
)
class_homolog_with_pre_def_schema = HomologSchema(
    single_schema=deepcopy(class_single_with_pre_def_schema),
    instance_names=OrderedSet(("test_1", "test_2")),
    schema_alias="homolog_test",
    pre_definitions=HOMOLOG_PRE_DEFINITION,
)
class_group_with_pre_def_schema = GroupSchema.from_originating_types(
    origins=OrderedSet((TestClass, OtherTestClass)),
    mapping_name="group_test",
    pre_definitions=class_group_pre_definitions,
)


dataclass_single_with_pre_def_schema = SingleSchema(
    origin=TestDataclass, schema_alias="single_test", pre_definitions=SINGLE_PRE_DEFINITION
)
dataclass_homolog_with_pre_def_schema = HomologSchema(
    single_schema=deepcopy(dataclass_single_with_pre_def_schema),
    instance_names=OrderedSet(("test_1", "test_2")),
    schema_alias="homolog_test",
    pre_definitions=HOMOLOG_PRE_DEFINITION,
)
dataclass_group_with_pre_def_schema = GroupSchema.from_originating_types(
    origins=OrderedSet((TestDataclass, OtherTestDataclass)),
    mapping_name="group_test",
    pre_definitions=dataclass_group_pre_definitions,
)


model_single_with_pre_def_schema = SingleSchema(
    origin=TestModel, schema_alias="single_test", pre_definitions=SINGLE_PRE_DEFINITION
)
model_homolog_with_pre_def_schema = HomologSchema(
    single_schema=deepcopy(model_single_with_pre_def_schema),
    instance_names=OrderedSet(("test_1", "test_2")),
    schema_alias="homolog_test",
    pre_definitions=HOMOLOG_PRE_DEFINITION,
)
model_group_with_pre_def_schema = GroupSchema.from_originating_types(
    origins=OrderedSet((TestModel, OtherTestModel)),
    mapping_name="group_test",
    pre_definitions=model_group_pre_definitions,
)
