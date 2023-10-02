import unittest
from test.abstract.main import AbstractTestCulture, AbstractTestGroup, AbstractTestHomolog, AbstractTestSingle
from test.schema.bare import class_culture_schema, class_group_schema, class_homolog_schema, class_single_schema
from test.schema.base import OtherTestClass, TestClass
from test.schema.pre_defined import (
    class_group_pre_definitions,
    class_group_with_pre_def_schema,
    class_homolog_with_pre_def_schema,
    class_single_with_pre_def_schema,
)
from typing import ClassVar, Type

from schemantic.utils.constant import (
    SCHEMA_DEFINED_MAPPING_KEY,
    SCHEMA_FIELD_INFO_MAPPING_KEY,
    SCHEMA_OPTIONAL_MAPPING_KEY,
    SCHEMA_REQUIRED_MAPPING_KEY,
)


class WithClassMixin:
    _test_class: ClassVar[Type] = TestClass
    _other_test_class: ClassVar[Type] = OtherTestClass

    def test_parse_schema_to_instance(self):
        self.assertTrue(self.schema_instance.parse_schema_to_instance(self.schema_with_instance_configuration))


class TestSingleWithCLS(unittest.TestCase, WithClassMixin, AbstractTestSingle):
    schema_instance = class_single_schema
    schema_instance_with_pre_defined = class_single_with_pre_def_schema

    expected_schema = {
        "class_name": "TestClass",
        SCHEMA_OPTIONAL_MAPPING_KEY: {
            "age": "int",
            "n": "NoneType",
            "new_age": "Any[int, str]",
            "we": "str(default: TestClass -> n)",
        },
        SCHEMA_REQUIRED_MAPPING_KEY: {"must_be": "int"},
    }


class TestHomologWithCLS(unittest.TestCase, WithClassMixin, AbstractTestHomolog):
    schema_instance = class_homolog_schema
    schema_instance_with_pre_defined = class_homolog_with_pre_def_schema

    expected_schema = {
        "class_name": "TestClass",
        "common": {},
        "test_1": {},
        "test_2": {},
        SCHEMA_REQUIRED_MAPPING_KEY: ["must_be"],
        SCHEMA_OPTIONAL_MAPPING_KEY: ["age", "n", "new_age", "we"],
        SCHEMA_FIELD_INFO_MAPPING_KEY: {
            "must_be": "int",
            "age": "int",
            "n": "NoneType",
            "new_age": "Any[int, str]",
            "we": "str(default: TestClass -> n)",
        },
    }


class TestGroupWithCLS(unittest.TestCase, WithClassMixin, AbstractTestGroup):
    schema_instance = class_group_schema
    schema_instance_with_pre_defined = class_group_with_pre_def_schema

    pre_defined_map = class_group_pre_definitions

    expected_schema = {
        "common": {
            SCHEMA_DEFINED_MAPPING_KEY: {},
            SCHEMA_REQUIRED_MAPPING_KEY: ["must_be"],
            SCHEMA_OPTIONAL_MAPPING_KEY: ["age", "n", "new_age", "we"],
        },
        "TestClass": {
            "class_name": "TestClass",
            SCHEMA_DEFINED_MAPPING_KEY: {},
            SCHEMA_REQUIRED_MAPPING_KEY: ["must_be"],
            SCHEMA_OPTIONAL_MAPPING_KEY: ["age", "n", "new_age", "we"],
        },
        "OtherTestClass": {
            "class_name": "OtherTestClass",
            SCHEMA_DEFINED_MAPPING_KEY: {},
            SCHEMA_OPTIONAL_MAPPING_KEY: ["we"],
        },
        "field_to_info": {
            "age": "int",
            "must_be": "int",
            "n": "NoneType",
            "new_age": "Any[int, str]",
            "we": "str(default: OtherTestClass -> n; TestClass -> n)",
        },
    }


class TestCultureWithCLS(unittest.TestCase, WithClassMixin, AbstractTestCulture):
    single_schema_instance = class_single_schema
    homolog_schema_instance = class_homolog_schema
    group_schema_instance = class_group_schema

    schema_instance = class_culture_schema

    expected_schema = {
        "single_test": {
            "class_name": "TestClass",
            SCHEMA_DEFINED_MAPPING_KEY: {},
            SCHEMA_REQUIRED_MAPPING_KEY: ["must_be"],
            SCHEMA_OPTIONAL_MAPPING_KEY: ["age", "n", "new_age", "we"],
        },
        "homolog_test": {
            "class_name": "TestClass",
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
            "TestClass": {
                "class_name": "TestClass",
                SCHEMA_DEFINED_MAPPING_KEY: {},
                SCHEMA_REQUIRED_MAPPING_KEY: ["must_be"],
                SCHEMA_OPTIONAL_MAPPING_KEY: ["age", "n", "new_age", "we"],
            },
            "OtherTestClass": {
                "class_name": "OtherTestClass",
                SCHEMA_DEFINED_MAPPING_KEY: {},
                SCHEMA_OPTIONAL_MAPPING_KEY: ["we"],
            },
        },
        "field_to_info": {
            "age": "int",
            "must_be": "int",
            "n": "NoneType",
            "new_age": "Any[int, str]",
            "we": "str(default: OtherTestClass -> n; TestClass -> n)",
        },
    }
