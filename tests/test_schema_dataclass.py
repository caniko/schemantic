import unittest
from dataclasses import dataclass
from typing import Optional

from schemantic.project import SchemanticProjectMixin
from tests.model import infer_expected_schemas
from tests.test_case.main import AbstractTestCulture, AbstractTestGroup, AbstractTestHomologue, AbstractTestSingle


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
    def fields_to_exclude_from_single_schema(cls) -> set[str]:
        upstream = super().fields_to_exclude_from_single_schema()
        upstream.add("exclude_me")
        return upstream


@dataclass
class OtherTestDataclass:
    we: str = "m"


expected_dataclass_schemas = infer_expected_schemas(TestDataclass, OtherTestDataclass)


class TestSingleWithDataclass(unittest.TestCase, AbstractTestSingle):
    single_schemer_origin = TestDataclass
    expected_schema = expected_dataclass_schemas.single_schema


class TestHomologueWithDataclass(unittest.TestCase, AbstractTestHomologue):
    homologue_schemer_origin = TestDataclass
    expected_schema = expected_dataclass_schemas.homologue_schema


class TestGroupWithDataclass(unittest.TestCase, AbstractTestGroup):
    group_schemer_origin_a = TestDataclass
    group_schemer_origin_b = OtherTestDataclass
    expected_schema = expected_dataclass_schemas.group_schema


class TestCultureWithDataclass(unittest.TestCase, AbstractTestCulture):
    single_schemer_origin = TestDataclass
    homologue_schemer_origin = TestDataclass
    group_schemer_origin_a = TestDataclass
    group_schemer_origin_b = OtherTestDataclass

    expected_schema = expected_dataclass_schemas.culture_schema
