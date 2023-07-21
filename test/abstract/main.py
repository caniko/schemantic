from abc import ABC
from functools import cached_property
from test.abstract.base import AbstractSchemaTester
from typing import ClassVar

from parameterized import parameterized

from schemantic.utils.constant import SCHEMA_DEFINED_MAPPING_KEY

from .assets import *


class AbstractTestSingle(AbstractSchemaTester, ABC):
    instance_configuration = {"must_be": 5, "we": "must_work"}

    @cached_property
    def schema_with_instance_configuration(self) -> dict:
        schema = self.schema_instance.schema(with_defined=True)
        schema[SCHEMA_DEFINED_MAPPING_KEY] = self.instance_configuration
        return schema

    def test_parse_schema(self):
        self.assertEqual(
            self.schema_instance.parse_schema(self.schema_with_instance_configuration),
            {self.schema_instance.mapping_name: self.instance_configuration},
        )


class AbstractTestHomolog(AbstractSchemaTester, ABC):
    instance_configuration = dict(
        common={"must_be": 10},
        test_1={"we": "are_friends"},
        test_2={"new_age": "Unknown", "must_be": 12},
    )

    @property
    def schema_with_instance_configuration(self) -> dict:
        schema = self.schema_instance.schema()
        schema.update(self.instance_configuration)
        return schema

    def test_from_originating_type(self):
        self.assertTrue(
            HomologSchema.from_originating_type(
                origin=self.schema_instance.single_schema.origin, instance_names=OrderedSet(("MyName", "My2ndName"))
            )
        )

    def test_name_instances_and_name_getter_undefined(self):
        with self.assertRaises(AttributeError):
            HomologSchema.from_originating_type(origin=self.schema_instance.single_schema.origin)

    def test_must_have_more_than_one_instance(self):
        with self.assertRaises(ValueError):
            HomologSchema.from_originating_type(
                origin=self.schema_instance.single_schema.origin, instance_names=OrderedSet(("MyName",))
            )

    def test_parse_schema(self):
        self.assertEqual(
            self.schema_instance.parse_schema(self.schema_with_instance_configuration),
            {
                "test_1": {
                    **self.instance_configuration["common"],
                    **self.instance_configuration["test_1"],
                },
                "test_2": {
                    **self.instance_configuration["common"],
                    **self.instance_configuration["test_2"],
                },
            },
        )


class AbstractTestGroup(AbstractSchemaTester, ABC):
    @cached_property
    def schema_with_instance_configuration(self) -> dict:
        schema = self.schema_instance.schema()

        schema["common"][SCHEMA_DEFINED_MAPPING_KEY]["we"] = "are_the_coolest"
        schema[self._test_class.__name__][SCHEMA_DEFINED_MAPPING_KEY] = {"must_be": 10}

        return schema

    @parameterized.expand(
        [[OrderedSet((TestModel, OtherTestModel))], [{"MyTest": TestModel, "MyOtherTest": OtherTestModel}]]
    )
    def test_from_originating_types(self, origins):
        self.assertTrue(GroupSchema.from_originating_types(origins=origins, mapping_name="testing"))

    def test_parse_schema(self):
        self.assertEqual(
            self.schema_instance.parse_schema(self.schema_with_instance_configuration),
            {
                self._test_class.__name__: {
                    **self.schema_with_instance_configuration["common"][SCHEMA_DEFINED_MAPPING_KEY],
                    **self.schema_with_instance_configuration[self._test_class.__name__][SCHEMA_DEFINED_MAPPING_KEY],
                },
                self._other_test_class.__name__: self.schema_with_instance_configuration["common"][
                    SCHEMA_DEFINED_MAPPING_KEY
                ],
            },
        )


class AbstractTestCulture(AbstractSchemaTester, ABC):
    single_schema_instance: ClassVar[SingleSchema]
    homolog_schema_instance: ClassVar[HomologSchema]
    group_schema_instance: ClassVar[GroupSchema]

    @cached_property
    def schema_with_instance_configuration(self) -> dict:
        schema = self.schema_instance.schema()

        schema[self.single_schema_instance.mapping_name][SCHEMA_DEFINED_MAPPING_KEY]["must_be"] = 12

        schema[self.homolog_schema_instance.mapping_name]["common"]["must_be"] = 10
        schema[self.homolog_schema_instance.mapping_name]["test_1"] = {"we": "are_friends"}
        schema[self.homolog_schema_instance.mapping_name]["test_2"] = {"new_age": "Unknown"}

        schema[self.group_schema_instance.mapping_name]["common"][SCHEMA_DEFINED_MAPPING_KEY]["we"] = "are_the_coolest"
        schema[self.group_schema_instance.mapping_name][self._test_class.__name__][SCHEMA_DEFINED_MAPPING_KEY][
            "must_be"
        ] = 10

        return schema

    @cached_property
    def single_schema_config(self):
        return self.schema_with_instance_configuration[self.single_schema_instance.mapping_name][
            SCHEMA_DEFINED_MAPPING_KEY
        ]

    @cached_property
    def homolog_test_1_config(self):
        return {
            **self.schema_with_instance_configuration[self.homolog_schema_instance.mapping_name]["common"],
            **self.schema_with_instance_configuration[self.homolog_schema_instance.mapping_name]["test_1"],
        }

    @cached_property
    def homolog_test_2_config(self):
        return {
            **self.schema_with_instance_configuration[self.homolog_schema_instance.mapping_name]["common"],
            **self.schema_with_instance_configuration[self.homolog_schema_instance.mapping_name]["test_2"],
        }

    @cached_property
    def group_test_config(self):
        return {
            **self.schema_with_instance_configuration[self.group_schema_instance.mapping_name]["common"][
                SCHEMA_DEFINED_MAPPING_KEY
            ],
            **self.schema_with_instance_configuration[self.group_schema_instance.mapping_name][
                self._test_class.__name__
            ][SCHEMA_DEFINED_MAPPING_KEY],
        }

    @cached_property
    def group_other_test_config(self):
        return self.schema_with_instance_configuration[self.group_schema_instance.mapping_name]["common"][
            SCHEMA_DEFINED_MAPPING_KEY
        ]

    def test_parse_schema(self):
        self.assertEqual(
            self.schema_instance.parse_schema(self.schema_with_instance_configuration),
            {
                self.single_schema_instance.mapping_name: self.single_schema_config,
                "test_1": self.homolog_test_1_config,
                "test_2": self.homolog_test_2_config,
                self._other_test_class.__name__: self.group_other_test_config,
                self._test_class.__name__: self.group_test_config,
            },
        )
