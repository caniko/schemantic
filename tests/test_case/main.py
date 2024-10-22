from abc import ABC
from copy import deepcopy
from functools import cached_property
from typing import ClassVar, Type

from ordered_set import OrderedSet

from schemantic import CultureSchemer, GroupSchemer, HomologueSchemer, SingleSchemer
from schemantic.schemer.many import _ensure_defined_key_in_mapping
from schemantic.utils.constant import (
    ARGUMENT_TO_TYPING_KEY,
    COMMON_MAPPING_KEY,
    CULTURE_KEY,
    DEFINED_MAPPING_KEY,
    GROUP_MEMBER_KEY,
    HOMOLOGUE_INSTANCE_KEY,
    INIT_SIGNATURE_MAPPING_KEY,
    OPTIONAL_MAPPING_KEY,
    REQUIRED_MAPPING_KEY,
)
from schemantic.utils.mapping import extract_sort_keys
from tests.test_case.abstract import (
    AbstractSchemerTestCase,
    AbstractSingleHomoGroupSchemerTestCase,
    AbstractSingleHomoSchemerTestCase,
)


def _infer_single_schemer(origin: type, pre_definition: dict | None) -> SingleSchemer:
    return SingleSchemer.from_origin(origin=origin, schema_alias="single_test", pre_definition=pre_definition)


class SetSchemerMixin:
    def test_load_into_mapping_name_to_instance_control(self):
        parse_result = self.main_schemer._parse_into_instance_by_mapping_name(self.dump_expected_schema(), {})
        for mapping_name, instance in parse_result.items():
            self.assertEqual(instance, self.expected_mapping_name_to_instance[mapping_name])


# The mixins are used to define the schemers within their respective test-case,
# SingleMixin -> SingleTestCase, and culture test case for the culture schemer.
# Remember, the culture schemer combines all the schemer paradigms under one.


class SingleMixin:
    single_schemer_origin: ClassVar[Type]
    single_origin_pre_configuration: ClassVar[dict] = dict(must_be=5, we="must_work")

    @classmethod
    def single_schemer(cls) -> SingleSchemer:
        return _infer_single_schemer(cls.single_schemer_origin, cls.single_origin_pre_configuration)

    @classmethod
    def single_expected_mapping_name_to_config(cls) -> dict:
        return cls.single_origin_pre_configuration

    @classmethod
    def single_expected_mapping_name_to_instance(cls) -> dict:
        return cls.single_schemer_origin(**cls.single_origin_pre_configuration)


class AbstractTestSingle(SingleMixin, AbstractSingleHomoSchemerTestCase[SingleSchemer], ABC):
    expected_number_of_instances = 1

    @property
    def main_schemer(self) -> SingleSchemer:
        return self.single_schemer()

    @property
    def main_pre_configuration(self) -> dict:
        return self.single_origin_pre_configuration

    def dump_expected_schema(self) -> dict:
        result = super().dump_expected_schema()
        result[DEFINED_MAPPING_KEY] = self.single_origin_pre_configuration
        return result

    @property
    def expected_mapping_name_to_config(self) -> dict:
        return self.single_expected_mapping_name_to_config()

    @property
    def expected_mapping_name_to_instance(self) -> dict:
        return self.single_expected_mapping_name_to_instance()


class HomologueMixin:
    homologue_schemer_origin: ClassVar[Type]
    homologue_common_config: ClassVar[dict] = dict(must_be=10)
    homologue_instance_config: ClassVar[dict] = dict(
        test_1={"we": "are_friends"},
        test_2={"new_age": "Unknown", "must_be": 12},
    )

    @classmethod
    def homologue_pre_configuration(cls) -> dict:
        return {
            COMMON_MAPPING_KEY: cls.homologue_common_config,
            HOMOLOGUE_INSTANCE_KEY: cls.homologue_instance_config,
        }

    @classmethod
    def homologue_instance_a_pre_configuration(cls) -> dict:
        return {
            **cls.homologue_common_config,
            **cls.homologue_instance_config["test_1"],
        }

    @classmethod
    def homologue_instance_b_pre_configuration(cls) -> dict:
        return {
            **cls.homologue_common_config,
            **cls.homologue_instance_config["test_2"],
        }

    @classmethod
    def homologue_schemer(cls) -> HomologueSchemer:
        return HomologueSchemer(
            single_schemer=_infer_single_schemer(cls.homologue_schemer_origin, None),
            instance_name_to_pre_definition=cls.homologue_instance_config,
            schema_alias="homologue_test",
            pre_definition_common=cls.homologue_pre_configuration(),
        )

    @classmethod
    def homologue_expected_mapping_name_to_config(cls) -> dict:
        return {
            "test_1": cls.homologue_instance_a_pre_configuration(),
            "test_2": cls.homologue_instance_b_pre_configuration(),
        }

    @classmethod
    def homologue_expected_mapping_name_to_instance(cls) -> dict:
        return {
            "test_1": cls.homologue_schemer_origin(**cls.homologue_instance_a_pre_configuration()),
            "test_2": cls.homologue_schemer_origin(**cls.homologue_instance_b_pre_configuration()),
        }


class AbstractTestHomologue(HomologueMixin, SetSchemerMixin, AbstractSingleHomoSchemerTestCase[HomologueSchemer], ABC):
    expected_number_of_instances = 2

    @property
    def main_schemer(self) -> HomologueSchemer:
        return self.homologue_schemer()

    @property
    def main_pre_configuration(self) -> dict:
        return self.homologue_pre_configuration()

    def dump_expected_schema(self) -> dict:
        result = super().dump_expected_schema()
        result[COMMON_MAPPING_KEY] = self.homologue_common_config
        result[HOMOLOGUE_INSTANCE_KEY] = self.homologue_instance_config
        return result

    @property
    def expected_mapping_name_to_config(self) -> dict:
        return self.homologue_expected_mapping_name_to_config()

    @property
    def expected_mapping_name_to_instance(self) -> dict:
        return self.homologue_expected_mapping_name_to_instance()

    @cached_property
    def schema_instance_with_pre_defined(self) -> HomologueSchemer:
        expected_schemer_with_pre_defined = deepcopy(self.main_schemer)
        expected_schemer_with_pre_defined.pre_definitions = self.main_pre_configuration
        return expected_schemer_with_pre_defined

    def test_from_originating_type(self):
        self.assertTrue(
            HomologueSchemer.from_originating_type(
                origin=self.main_schemer.single_schemer.origin,
                instance_name_to_pre_definition={"MyName": {}, "My2ndName": {}},
            )
        )

    def test_name_instances_and_name_getter_undefined(self):
        with self.assertRaises(AttributeError):
            HomologueSchemer.from_originating_type(origin=self.homologue_schemer().single_schemer.origin)


class GroupMixin:
    group_schemer_origin_a: ClassVar[Type]
    group_schemer_origin_b: ClassVar[Type]

    group_common_config_definition: ClassVar[dict] = dict(we="are_the_best")
    group_origin_config_a: ClassVar[dict] = dict(must_be=5)
    group_origin_config_b: ClassVar[dict] = dict(we="must_work")

    @classmethod
    def group_origin_object_a_values(cls):
        return {**cls.group_common_config_definition, **cls.group_origin_config_a}

    @classmethod
    def group_origin_object_b_values(cls):
        return {**cls.group_common_config_definition, **cls.group_origin_config_b}

    @classmethod
    def group_expected_mapping_name_to_config(cls) -> dict:
        return {
            cls.group_schemer_origin_a.__name__: cls.group_origin_object_a_values(),
            cls.group_schemer_origin_b.__name__: cls.group_origin_object_b_values(),
        }

    @classmethod
    def group_expected_mapping_name_to_instance(cls) -> dict:
        return {
            cls.group_schemer_origin_a.__name__: cls.group_schemer_origin_a(**cls.group_origin_object_a_values()),
            cls.group_schemer_origin_b.__name__: cls.group_schemer_origin_b(**cls.group_origin_object_b_values()),
        }

    @classmethod
    def group_name_to_pre_definition(cls) -> dict:
        return {
            cls.group_schemer_origin_a.__name__: cls.group_origin_config_a,
            cls.group_schemer_origin_b.__name__: cls.group_origin_config_b,
        }

    @classmethod
    def group_common_config(cls) -> dict:
        return {
            "defined": cls.group_common_config_definition,
            "optional": ["age", "n", "new_age", "we"],
            "required": ["must_be"],
        }

    @classmethod
    def group_schemer(cls) -> GroupSchemer:
        return GroupSchemer.from_originating_types(
            origins=OrderedSet((cls.group_schemer_origin_a, cls.group_schemer_origin_b)),
            schema_alias="group_test",
            pre_definition_common=cls.group_common_config_definition,
            name_to_pre_definition=cls.group_name_to_pre_definition(),
        )


class AbstractTestGroup(GroupMixin, SetSchemerMixin, AbstractSingleHomoGroupSchemerTestCase, ABC):
    group_schemer_origin_a: ClassVar[Type]
    group_schemer_origin_b: ClassVar[Type]

    expected_number_of_instances = 2

    @property
    def main_schemer(self) -> GroupSchemer:
        return self.group_schemer()

    @property
    def main_pre_configuration(self) -> dict:
        return self.group_origin_config_a

    def dump_expected_schema(self) -> dict:
        result = super().dump_expected_schema()
        result[COMMON_MAPPING_KEY]["defined"] = self.group_common_config_definition
        result["members"][self.group_schemer_origin_a.__name__]["defined"] = self.group_origin_config_a
        result["members"][self.group_schemer_origin_b.__name__]["defined"] = self.group_origin_config_b
        return result

    @property
    def expected_mapping_name_to_config(self) -> dict:
        return self.group_expected_mapping_name_to_config()

    @property
    def expected_mapping_name_to_instance(self) -> dict:
        return self.group_expected_mapping_name_to_instance()

    def test_from_originating_types_list(self):
        self.assertTrue(
            GroupSchemer.from_originating_types(
                origins=[self.group_schemer_origin_a, self.group_schemer_origin_b], mapping_name="testing"
            )
        )

    def test_from_originating_types_dict(self):
        self.assertTrue(
            GroupSchemer.from_originating_types(
                origins={"MyTest": self.group_schemer_origin_a, "MyOtherTest": self.group_schemer_origin_b},
                mapping_name="testing",
            )
        )


class AbstractTestCulture(SingleMixin, HomologueMixin, GroupMixin, AbstractSchemerTestCase[CultureSchemer], ABC):
    @cached_property
    def main_schemer(self) -> CultureSchemer:
        return CultureSchemer(
            source_schemers=OrderedSet((self.single_schemer(), self.homologue_schemer(), self.group_schemer()))
        )

    @cached_property
    def group_test_config(self):
        return {
            **self.dump_expected_schema()[CULTURE_KEY][self.group_schemer().mapping_name][COMMON_MAPPING_KEY][
                DEFINED_MAPPING_KEY
            ],
            **self.dump_expected_schema()[CULTURE_KEY][self.group_schemer().mapping_name][self._test_class.__name__][
                DEFINED_MAPPING_KEY
            ],
        }

    @cached_property
    def group_other_test_config(self):
        return self.dump_expected_schema()[self.group_schemer().mapping_name][COMMON_MAPPING_KEY][DEFINED_MAPPING_KEY]

    def dump_expected_schema(self) -> dict:
        result = super().dump_expected_schema()

        result[COMMON_MAPPING_KEY] = {"optional": ["age", "n", "new_age", "we"], "required": ["must_be"]}

        result[CULTURE_KEY][self.single_schemer().mapping_name][
            DEFINED_MAPPING_KEY
        ] = self.single_origin_pre_configuration
        result[CULTURE_KEY][self.single_schemer().mapping_name][REQUIRED_MAPPING_KEY] = extract_sort_keys(
            result[CULTURE_KEY][self.single_schemer().mapping_name][REQUIRED_MAPPING_KEY]
        )
        result[CULTURE_KEY][self.single_schemer().mapping_name][OPTIONAL_MAPPING_KEY] = extract_sort_keys(
            result[CULTURE_KEY][self.single_schemer().mapping_name][OPTIONAL_MAPPING_KEY]
        )

        result[CULTURE_KEY][self.homologue_schemer().mapping_name][COMMON_MAPPING_KEY] = self.homologue_common_config
        result[CULTURE_KEY][self.homologue_schemer().mapping_name][
            HOMOLOGUE_INSTANCE_KEY
        ] = self.homologue_instance_config
        init_signature = result[CULTURE_KEY][self.homologue_schemer().mapping_name][INIT_SIGNATURE_MAPPING_KEY]
        result[CULTURE_KEY][self.homologue_schemer().mapping_name][INIT_SIGNATURE_MAPPING_KEY][REQUIRED_MAPPING_KEY] = (
            extract_sort_keys(init_signature[REQUIRED_MAPPING_KEY])
        )
        result[CULTURE_KEY][self.homologue_schemer().mapping_name][INIT_SIGNATURE_MAPPING_KEY][OPTIONAL_MAPPING_KEY] = (
            extract_sort_keys(init_signature[OPTIONAL_MAPPING_KEY])
        )

        result[CULTURE_KEY][self.group_schemer().mapping_name].pop(ARGUMENT_TO_TYPING_KEY)
        result[CULTURE_KEY][self.group_schemer().mapping_name][COMMON_MAPPING_KEY] = self.group_common_config()
        result[CULTURE_KEY][self.group_schemer().mapping_name][GROUP_MEMBER_KEY][self.group_schemer_origin_a.__name__][
            DEFINED_MAPPING_KEY
        ] = self.group_origin_config_a
        result[CULTURE_KEY][self.group_schemer().mapping_name][GROUP_MEMBER_KEY][self.group_schemer_origin_b.__name__][
            DEFINED_MAPPING_KEY
        ] = self.group_origin_config_b

        for member_name in (self.group_schemer_origin_a.__name__, self.group_schemer_origin_b.__name__):
            init_signature = result[CULTURE_KEY][self.group_schemer().mapping_name][GROUP_MEMBER_KEY][member_name]
            if REQUIRED_MAPPING_KEY in init_signature:
                result[CULTURE_KEY][self.group_schemer().mapping_name][GROUP_MEMBER_KEY][member_name][
                    REQUIRED_MAPPING_KEY
                ] = extract_sort_keys(init_signature[REQUIRED_MAPPING_KEY])
            if OPTIONAL_MAPPING_KEY in init_signature:
                result[CULTURE_KEY][self.group_schemer().mapping_name][GROUP_MEMBER_KEY][member_name][
                    OPTIONAL_MAPPING_KEY
                ] = extract_sort_keys(init_signature[OPTIONAL_MAPPING_KEY])

        _ensure_defined_key_in_mapping(result, COMMON_MAPPING_KEY)

        return result

    @property
    def expected_mapping_name_to_config(self):
        return {
            self.single_schemer().mapping_name: self.single_origin_pre_configuration,
            self.homologue_schemer().mapping_name: self.homologue_expected_mapping_name_to_config(),
            self.group_schemer().mapping_name: self.group_expected_mapping_name_to_config(),
        }

    @property
    def expected_mapping_name_to_instance(self):
        return {
            self.single_schemer().mapping_name: self.single_origin_pre_configuration,
            **self.homologue_expected_mapping_name_to_config(),
            **self.group_expected_mapping_name_to_config(),
        }
