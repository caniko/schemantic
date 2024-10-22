import unittest
from tests.abstract.main import AbstractTestCulture, AbstractTestGroup, AbstractTestHomolog, AbstractTestSingle
from tests.schema.bare import model_culture_schema, model_group_schema, model_homolog_schema, model_single_schema
from tests.schema.base import OtherTestModel, TestModel
from tests.schema.pre_defined import (
    model_group_pre_definitions,
    model_group_with_pre_def_schema,
    model_homolog_with_pre_def_schema,
    model_single_with_pre_def_schema,
)
from typing import ClassVar, Type

from schemantic.utils.constant import (
    SCHEMA_DEFINED_MAPPING_KEY,
    SCHEMA_FIELD_INFO_MAPPING_KEY,
    SCHEMA_OPTIONAL_MAPPING_KEY,
    SCHEMA_REQUIRED_MAPPING_KEY,
)


class WithModelMixin:
    _test_class: ClassVar[Type] = TestModel
    _other_test_class: ClassVar[Type] = OtherTestModel


class TestSingleWithModel(unittest.TestCase, AbstractTestSingle):
    schema_instance = model_single_schema
    schema_instance_with_pre_defined = model_single_with_pre_def_schema

    expected_schema = {
        "class_name": "TestModel",
        SCHEMA_OPTIONAL_MAPPING_KEY: {
            "age": "integer",
            "n": "null",
            "new_age": "Any[integer, string]",
            "we": "string(default: TestModel -> n)",
        },
        SCHEMA_REQUIRED_MAPPING_KEY: {"must_be": "integer"},
    }

    def test_parse_schema_to_instance(self):
        self.assertEqual(
            self.schema_instance.parse_schema_to_instance(self.schema_with_instance_configuration),
            {self.schema_instance.mapping_name: self.schema_instance.origin(**self.instance_configuration)},
        )


class TestHomologWithModel(unittest.TestCase, AbstractTestHomolog):
    schema_instance = model_homolog_schema
    schema_instance_with_pre_defined = model_homolog_with_pre_def_schema

    expected_schema = {
        "class_name": "TestModel",
        "common": {},
        "test_1": {},
        "test_2": {},
        SCHEMA_REQUIRED_MAPPING_KEY: ["must_be"],
        SCHEMA_OPTIONAL_MAPPING_KEY: ["age", "n", "new_age", "we"],
        SCHEMA_FIELD_INFO_MAPPING_KEY: {
            "must_be": "integer",
            "age": "integer",
            "n": "null",
            "new_age": "Any[integer, string]",
            "we": "string(default: TestModel -> n)",
        },
    }

    def test_parse_schema_to_instance(self):
        origin = self.schema_instance.single_schema.origin
        self.assertEqual(
            self.schema_instance.parse_schema_to_instance(self.schema_with_instance_configuration),
            {
                "test_1": origin(
                    **self.instance_configuration["common"],
                    **self.instance_configuration["test_1"],
                ),
                "test_2": origin(
                    **{
                        **self.instance_configuration["common"],
                        **self.instance_configuration["test_2"],
                    }
                ),
            },
        )


class TestGroupWithModel(unittest.TestCase, AbstractTestGroup, WithModelMixin):
    schema_instance = model_group_schema
    schema_instance_with_pre_defined = model_group_with_pre_def_schema

    pre_defined_map = model_group_pre_definitions

    expected_schema = {
        "common": {
            SCHEMA_DEFINED_MAPPING_KEY: {},
            SCHEMA_REQUIRED_MAPPING_KEY: ["must_be"],
            SCHEMA_OPTIONAL_MAPPING_KEY: ["age", "n", "new_age", "we"],
        },
        "TestModel": {
            "class_name": "TestModel",
            SCHEMA_DEFINED_MAPPING_KEY: {},
            SCHEMA_REQUIRED_MAPPING_KEY: ["must_be"],
            SCHEMA_OPTIONAL_MAPPING_KEY: ["age", "n", "new_age", "we"],
        },
        "OtherTestModel": {
            "class_name": "OtherTestModel",
            SCHEMA_DEFINED_MAPPING_KEY: {},
            SCHEMA_OPTIONAL_MAPPING_KEY: ["we"],
        },
        SCHEMA_FIELD_INFO_MAPPING_KEY: {
            "age": "integer",
            "must_be": "integer",
            "n": "null",
            "new_age": "Any[integer, string]",
            "we": "string(default: OtherTestModel -> d; TestModel -> n)",
        },
    }

    def test_parse_schema_to_instance(self):
        self.assertEqual(
            self.schema_instance.parse_schema_to_instance(self.schema_with_instance_configuration),
            {
                self._test_class.__name__: self._test_class(
                    **{
                        **self.schema_with_instance_configuration["common"][SCHEMA_DEFINED_MAPPING_KEY],
                        **self.schema_with_instance_configuration[self._test_class.__name__][
                            SCHEMA_DEFINED_MAPPING_KEY
                        ],
                    }
                ),
                self._other_test_class.__name__: self._other_test_class(
                    **self.schema_with_instance_configuration["common"][SCHEMA_DEFINED_MAPPING_KEY]
                ),
            },
        )


class TestCultureWithModel(unittest.TestCase, AbstractTestCulture, WithModelMixin):
    single_schema_instance = model_single_schema
    homolog_schema_instance = model_homolog_schema
    group_schema_instance = model_group_schema

    schema_instance = model_culture_schema

    expected_schema = {
        "single_test": {
            "class_name": "TestModel",
            SCHEMA_DEFINED_MAPPING_KEY: {},
            SCHEMA_REQUIRED_MAPPING_KEY: ["must_be"],
            SCHEMA_OPTIONAL_MAPPING_KEY: ["age", "n", "new_age", "we"],
        },
        "homolog_test": {
            "class_name": "TestModel",
            "common": {},
            "test_1": {},
            "test_2": {},
            SCHEMA_REQUIRED_MAPPING_KEY: ["must_be"],
            SCHEMA_OPTIONAL_MAPPING_KEY: ["age", "n", "new_age", "we"],
        },
        "group_test": {
            "common": {
                SCHEMA_DEFINED_MAPPING_KEY: {},
                SCHEMA_REQUIRED_MAPPING_KEY: ["must_be"],
                SCHEMA_OPTIONAL_MAPPING_KEY: ["age", "n", "new_age", "we"],
            },
            "TestModel": {
                "class_name": "TestModel",
                SCHEMA_DEFINED_MAPPING_KEY: {},
                SCHEMA_REQUIRED_MAPPING_KEY: ["must_be"],
                SCHEMA_OPTIONAL_MAPPING_KEY: ["age", "n", "new_age", "we"],
            },
            "OtherTestModel": {
                "class_name": "OtherTestModel",
                SCHEMA_DEFINED_MAPPING_KEY: {},
                SCHEMA_OPTIONAL_MAPPING_KEY: ["we"],
            },
        },
        SCHEMA_FIELD_INFO_MAPPING_KEY: {
            "age": "integer",
            "must_be": "integer",
            "n": "null",
            "new_age": "Any[integer, string]",
            "we": "string(default: OtherTestModel -> d; TestModel -> n)",
        },
    }

    def test_parse_schema_to_instance(self):
        self.assertEqual(
            self.schema_instance.parse_schema_to_instance(self.schema_with_instance_configuration),
            {
                self.single_schema_instance.mapping_name: self._test_class(**self.single_schema_config),
                "test_1": self._test_class(**self.homolog_test_1_config),
                "test_2": self._test_class(**self.homolog_test_2_config),
                self._test_class.__name__: self._test_class(**self.group_test_config),
                self._other_test_class.__name__: self._other_test_class(**self.group_other_test_config),
            },
        )
