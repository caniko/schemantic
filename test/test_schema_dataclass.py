import unittest
from test.abstract.assets import (
    OtherTestDataclass,
    TestDataclass,
    dataclass_culture_schema,
    dataclass_group_schema,
    dataclass_homolog_schema,
    dataclass_single_schema,
)
from test.abstract.main import AbstractTestCulture, AbstractTestGroup, AbstractTestHomolog, AbstractTestSingle
from typing import ClassVar, Type

from schemantic.utils.constant import (
    SCHEMA_DEFINED_MAPPING_KEY,
    SCHEMA_FIELD_INFO_MAPPING_KEY,
    SCHEMA_OPTIONAL_MAPPING_KEY,
    SCHEMA_REQUIRED_MAPPING_KEY,
)


class WithDataclassMixin:
    _test_class: ClassVar[Type] = TestDataclass
    _other_test_class: ClassVar[Type] = OtherTestDataclass

    def test_parse_schema_to_instance(self):
        self.assertTrue(self.schema_instance.parse_schema_to_instance(self.schema_with_instance_configuration))


class TestSingleWithCLS(unittest.TestCase, WithDataclassMixin, AbstractTestSingle):
    schema_instance = dataclass_single_schema

    expected_schema = {
        "class_name": "TestDataclass",
        SCHEMA_OPTIONAL_MAPPING_KEY: {
            "age": "int",
            "n": "NoneType",
            "new_age": "Any[int, str]",
            "we": "str(default: TestDataclass -> n)",
        },
        SCHEMA_REQUIRED_MAPPING_KEY: {"must_be": "int"},
    }


class TestHomologWithCLS(unittest.TestCase, WithDataclassMixin, AbstractTestHomolog):
    schema_instance = dataclass_homolog_schema

    expected_schema = {
        "class_name": "TestDataclass",
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
            "we": "str(default: TestDataclass -> n)",
        },
    }


class TestGroupWithCLS(unittest.TestCase, WithDataclassMixin, AbstractTestGroup):
    schema_instance = dataclass_group_schema

    expected_schema = {
        "common": {
            SCHEMA_DEFINED_MAPPING_KEY: {},
            SCHEMA_REQUIRED_MAPPING_KEY: ["must_be"],
            SCHEMA_OPTIONAL_MAPPING_KEY: ["age", "n", "new_age", "we"],
        },
        "TestDataclass": {
            "class_name": "TestDataclass",
            SCHEMA_DEFINED_MAPPING_KEY: {},
            SCHEMA_REQUIRED_MAPPING_KEY: ["must_be"],
            SCHEMA_OPTIONAL_MAPPING_KEY: ["age", "n", "new_age", "we"],
        },
        "OtherTestDataclass": {
            "class_name": "OtherTestDataclass",
            SCHEMA_DEFINED_MAPPING_KEY: {},
            SCHEMA_OPTIONAL_MAPPING_KEY: ["we"],
        },
        "field_to_info": {
            "age": "int",
            "must_be": "int",
            "n": "NoneType",
            "new_age": "Any[int, str]",
            "we": "str(default: OtherTestDataclass -> n; TestDataclass -> n)",
        },
    }


class TestCultureWithCLS(unittest.TestCase, WithDataclassMixin, AbstractTestCulture):
    single_schema_instance = dataclass_single_schema
    homolog_schema_instance = dataclass_homolog_schema
    group_schema_instance = dataclass_group_schema

    schema_instance = dataclass_culture_schema

    expected_schema = {
        "single_test": {
            "class_name": "TestDataclass",
            SCHEMA_DEFINED_MAPPING_KEY: {},
            SCHEMA_REQUIRED_MAPPING_KEY: ["must_be"],
            SCHEMA_OPTIONAL_MAPPING_KEY: ["age", "n", "new_age", "we"],
        },
        "homolog_test": {
            "class_name": "TestDataclass",
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
            "TestDataclass": {
                "class_name": "TestDataclass",
                SCHEMA_DEFINED_MAPPING_KEY: {},
                SCHEMA_REQUIRED_MAPPING_KEY: ["must_be"],
                SCHEMA_OPTIONAL_MAPPING_KEY: ["age", "n", "new_age", "we"],
            },
            "OtherTestDataclass": {
                "class_name": "OtherTestDataclass",
                SCHEMA_DEFINED_MAPPING_KEY: {},
                SCHEMA_OPTIONAL_MAPPING_KEY: ["we"],
            },
        },
        "field_to_info": {
            "age": "int",
            "must_be": "int",
            "n": "NoneType",
            "new_age": "Any[int, str]",
            "we": "str(default: OtherTestDataclass -> n; TestDataclass -> n)",
        },
    }
