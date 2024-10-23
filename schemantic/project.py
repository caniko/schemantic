from typing import Any, ClassVar, Type

from pydantic import BaseModel, computed_field


class SchemanticProjectMixin:
    include_private: ClassVar[bool] = False

    @classmethod
    def fields_to_exclude_from_single_schema(cls) -> set[str]:
        """
        Some required fields for a class are sometimes highly specific to its respective object. These fields should
        be recorded in this class-property to be excluded by the config generator function

        Usage:
            @classmethod
            @property
            def fields_to_exclude_from_single_schema(cls) -> set[str]:
                upstream = super().fields_to_exclude_from_single_schema()
                upstream.update(("SOME", "FIELD"))
                return upstream

        :return:
        """
        return set()

    @classmethod
    def single_schema_kwargs(cls) -> dict[str, Any]:
        return dict(
            include_private=cls.include_private,
            fields_to_exclude=cls.fields_to_exclude_from_single_schema(),
        )


SchemanticProjectType = Type[SchemanticProjectMixin]


class SchemanticProjectModelMixin(BaseModel, SchemanticProjectMixin):
    @classmethod
    def fields_to_exclude_from_single_schema(cls) -> set[str]:
        return super().fields_to_exclude_from_single_schema()

    @classmethod
    def single_schema_kwargs(cls) -> dict[str, Any]:
        return super().single_schema_kwargs()
