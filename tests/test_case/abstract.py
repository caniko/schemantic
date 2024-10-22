import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar, Generic

from parameterized import parameterized

from schemantic.schema.model import AnySSchema
from schemantic.schemer.abstract import Schemer


class AbstractSchemerTestCase(Generic[Schemer], ABC):
    expected_schema: ClassVar[AnySSchema]
    expected_schema_with_pre_defined: ClassVar[AnySSchema]
    expected_number_of_instances: ClassVar[int]

    @property
    @abstractmethod
    def main_schemer(self) -> Schemer: ...

    @property
    @abstractmethod
    def expected_mapping_name_to_config(self) -> dict: ...

    @abstractmethod
    def dump_expected_schema(self) -> dict:
        return self.expected_schema.model_dump(exclude_defaults=True)

    @property
    @abstractmethod
    def expected_mapping_name_to_instance(self) -> dict: ...

    def test_schema_generates(self):
        self.assertTrue(self.main_schemer.schema())

    def test_load_into_mapping_name_to_instance_call(self):
        self.assertTrue(self.expected_mapping_name_to_instance)

    def test_load_definitions(self):
        self.assertEqual(
            self.main_schemer.load_definitions(self.dump_expected_schema()),
            self.expected_mapping_name_to_config,
        )

    @parameterized.expand([".toml", ".yaml"])
    def test_dump(self, suffix: str):
        with tempfile.NamedTemporaryFile(mode="w+", delete=True, suffix=suffix) as tf:
            self.main_schemer.dump(Path(tf.name))

    @parameterized.expand([".toml", ".yaml"])
    def test_dump_parse(self, suffix: str):
        with tempfile.NamedTemporaryFile(mode="w+", delete=True, suffix=suffix) as tf:
            schema_path = Path(tf.name)

            self.main_schemer.dump(schema_path)

            loaded_schema = self.main_schemer.load(schema_path)

            self.assertEqual(loaded_schema, self.dump_expected_schema())


class AbstractSingleHomoGroupSchemerTestCase(AbstractSchemerTestCase[Schemer], Generic[Schemer], ABC):
    pass


class AbstractSingleHomoSchemerTestCase(AbstractSingleHomoGroupSchemerTestCase[Schemer], Generic[Schemer], ABC):
    @property
    @abstractmethod
    def main_pre_configuration(self) -> dict: ...
