from typing import Any, ClassVar


class SchemanticProjectMixin:
    include_private: ClassVar[bool] = False

    @classmethod
    def fields_to_exclude_from_single_schema(cls) -> set[str]:
        """
        Some required fields for a class are sometimes highly specific to its respective object. These fields should
        be recorded in this class-property to be excluded by the config generator function

        Usage:
            @classmethod
            def fields_to_exclude_from_single_schema(cls) -> set[str]:
                upstream = super().fields_to_exclude_from_single_schema()
                upstream.update(("SOME", "FIELD"))
                return upstream

            Notice `upstream = super().fields_to_exclude_from_single_schema()`, it ensures
            that we can inherit the exclusion fields from the parent class. You don't need
            to do this on your root class; moreover, downstream classes could benefit from it.
        """
        return set()

    @classmethod
    def single_schema_kwargs(cls) -> dict[str, Any]:
        return dict(
            include_private=cls.include_private,
            fields_to_exclude=cls.fields_to_exclude_from_single_schema(),
        )
