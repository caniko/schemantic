from copy import deepcopy
from tests.schema.base import OtherTestClass, OtherTestDataclass, OtherTestModel, TestClass, TestDataclass, TestModel

from ordered_set import OrderedSet

from schemantic.schema.main import CultureSchema, GroupSchema, HomologueSchema, SingleSchema

class_single_schema = SingleSchema(origin=TestClass, schema_alias="single_test")
class_homolog_schema = HomologueSchema(
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
dataclass_homolog_schema = HomologueSchema(
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
model_homolog_schema = HomologueSchema(
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
