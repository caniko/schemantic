import unittest
from typing import Optional

from schemantic.project import SchemanticProjectMixin
from tests.model import infer_expected_schemas
from tests.test_case.main import AbstractTestCulture, AbstractTestGroup, AbstractTestHomologue, AbstractTestSingle


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
        self.must_be = must_be
        self.we = we
        self.n = n
        self.age = age
        self.new_age = new_age
        self.exclude_me = exclude_me
        self._exclude_me_too = _exclude_me_too

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @classmethod
    def fields_to_exclude_from_single_schema(cls) -> set[str]:
        upstream = super().fields_to_exclude_from_single_schema()
        upstream.add("exclude_me")
        return upstream


class OtherTestClass:
    def __init__(self, we: str = "m"):
        self.we = we

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


expected_class_schemas = infer_expected_schemas(TestClass, OtherTestClass)


class TestSingleWithCLS(unittest.TestCase, AbstractTestSingle):
    single_schemer_origin = TestClass
    expected_schema = expected_class_schemas.single_schema


class TestHomologueWithCLS(unittest.TestCase, AbstractTestHomologue):
    homologue_schemer_origin = TestClass
    expected_schema = expected_class_schemas.homologue_schema


class TestGroupWithCLS(unittest.TestCase, AbstractTestGroup):
    group_schemer_origin_a = TestClass
    group_schemer_origin_b = OtherTestClass
    expected_schema = expected_class_schemas.group_schema


class TestCultureWithCLS(unittest.TestCase, AbstractTestCulture):
    single_schemer_origin = TestClass
    homologue_schemer_origin = TestClass
    group_schemer_origin_a = TestClass
    group_schemer_origin_b = OtherTestClass

    expected_schema = expected_class_schemas.culture_schema
