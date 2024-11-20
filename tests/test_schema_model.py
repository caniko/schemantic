import unittest
from typing import Optional

from pydantic import BaseModel

from schemantic.project import SchemanticProjectMixin
from tests.model import infer_expected_schemas
from tests.test_case.main import AbstractTestCulture, AbstractTestGroup, AbstractTestHomologue, AbstractTestSingle


class TestModel(SchemanticProjectMixin, BaseModel):
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


class OtherTestModel(BaseModel):
    we: str = "m"


expected_model_schemas = infer_expected_schemas(TestModel, OtherTestModel)


class TestSingleWithModel(unittest.TestCase, AbstractTestSingle):
    single_schemer_origin = TestModel
    expected_schema = expected_model_schemas.single_schema


class TestHomologueWithModel(unittest.TestCase, AbstractTestHomologue):
    homologue_schemer_origin = TestModel
    expected_schema = expected_model_schemas.homologue_schema


class TestGroupWithModel(unittest.TestCase, AbstractTestGroup):
    group_schemer_origin_a = TestModel
    group_schemer_origin_b = OtherTestModel
    expected_schema = expected_model_schemas.group_schema


class TestCultureWithModel(unittest.TestCase, AbstractTestCulture):
    single_schemer_origin = TestModel
    homologue_schemer_origin = TestModel
    group_schemer_origin_a = TestModel
    group_schemer_origin_b = OtherTestModel

    expected_schema = expected_model_schemas.culture_schema
