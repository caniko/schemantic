from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, computed_field

from schemantic.project import SchemanticProjectMixin, SchemanticProjectModelMixin


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
        pass

    @classmethod
    def fields_to_exclude_from_single_schema(cls) -> set[str]:
        upstream = super().fields_to_exclude_from_single_schema()
        upstream.add("exclude_me")
        return upstream


class OtherTestClass:
    def __init__(self, we: str = "n"):
        pass


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
    we: str = "n"


class TestModel(SchemanticProjectModelMixin, BaseModel):
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
    we: str = "d"
