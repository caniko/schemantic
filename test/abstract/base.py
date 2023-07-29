import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar, Literal

from parameterized import parameterized

from schemantic.schema.abstract import BaseSchema


class AbstractSchemaTester(ABC):
    schema_instance: ClassVar[BaseSchema]

    expected_schema: ClassVar[dict]
    instance_configuration: ClassVar[dict]

    @property
    @abstractmethod
    def schema_with_instance_configuration(self) -> dict:
        ...

    @abstractmethod
    def test_parse_schema(self):
        ...

    @abstractmethod
    def test_parse_schema_to_instance(self):
        ...

    def test_schema(self):
        self.assertEqual(self.schema_instance.schema(), self.expected_schema)

    @parameterized.expand([".toml", ".yaml"])
    def test_dump(self, suffix: str):
        with tempfile.NamedTemporaryFile(mode="w+", delete=True, suffix=suffix) as tf:
            self.schema_instance.dump(Path(tf.name))

    @parameterized.expand([".toml", ".yaml"])
    def test_dump_parse(self, suffix: str):
        with tempfile.NamedTemporaryFile(mode="w+", delete=True, suffix=suffix) as tf:
            schema_path = Path(tf.name)

            self.schema_instance.dump(schema_path)

            self.assertEqual(self.schema_instance.load(schema_path), self.expected_schema)


class AbstractNotCulturalTester(AbstractSchemaTester, ABC):
    schema_instance_with_pre_defined: ClassVar[BaseSchema]

    @abstractmethod
    def test_schema_with_pre_defined(self):
        ...
