# Schemantic

Do you have configurations stored in files? You have come to the right place! Create schemas from models or classes with homologous, grouped, or cultured paradigms. Batteries for loading and dumping included!

Supports `pydantic.BaseModel` and any Python class and `dataclass`/`pydantic.dataclass`!

## Classes of schemas

### Homologue
```python
from pydantic import BaseModel
from schemantic import HomologueSchemer

class Thief(BaseModel):
    stolen_goods: int
    steals_only: str

my_homolog = HomologueSchemer.from_originating_type(Thief, instance_name_to_pre_definition={"copycat": {}, "pink_panther": {}})
```

`HomologueSchemer` also accepts `instance_name_getter` parameter, which is a dictionary of instance names to pre-defined values.

### Grouped
You can manage multiple schemas as a group:

```python
from pydantic import BaseModel
from schemantic import GroupSchemer

class Baker(BaseModel):
    baked_goods: int
    citizen_of: str

class Cop(BaseModel):
    years_of_service: int
    citizen_of: str

group_schema = GroupSchemer.from_originating_types([Baker, Cop])
```

### Culture
You can also manage multiple types of schemas under one culture:

```python
from ordered_set import OrderedSet
from schemantic import CultureSchemer

CultureSchemer(source_schemas=OrderedSet([homolog_schema, group_schema]))
```

## Methods
`HomologueSchemer`, `GroupSchemer`, and `CultureSchemer` have the following methods.

### `.schema()`
Creates a BaseModel derived class instance, which represents the schema of the origin class/model.

```python
my_homolog.schema()
```
Output:
```yaml
"class_name": "Thief"
"common": {
    steals_only: "jewelry"
}
"copycat": {}
"pink_panther": {}
"required": ["stolen_goods", "steals_only"]
"field_to_info": {"stolen_goods": "integer"}
```

### `.dump()`
Dump the dictionary from `.schema()` to a yaml or toml file.
```python
my_schema.dump("my/path/schema.yaml")
# There is also toml support
my_schema.dump("my/path/schema.toml")
```

### `.parse()`
```yaml
"class_name": "Thief"
"common": {
    steals_only: "jewelry"
}
"copycat": {
    stolen_goods: 10
}
"pink_panther": {
    stolen_goods: 14
}
"required": ["stolen_goods", "steals_only"]
"field_to_info": {"stolen_goods": "integer"}
```
```python
parsed = my_homolog.parse_schema("my/path/schema.yaml")

# parsed["copycat"].stolen_goods == 10
# parsed["pink_panther"].stolen_goods == 14

# Both -> steals_only == "jewelry"
```

## Class configuration
Use `schemantic.project` module to control schemantic processing from the origin class/model side.

Classes and dataclasses
```python
from dataclasses import dataclass
from typing import Optional, Union

from schemantic.project import SchemanticProjectMixin


@dataclass
class TestDataclass(SchemanticProjectMixin):
    must_be: int
    we: str = "n"

    n: None = None
    age: Optional[int] = None
    new_age: Union[int, str, None] = None

    exclude_me: Optional[int] = None
    _exclude_me_too: Optional[float] = None

    @classmethod
    @property
    def fields_to_exclude_from_single_schema(cls) -> set[str]:
        upstream = super().fields_to_exclude_from_single_schema
        upstream.update(("exclude_me",))
        return upstream
```

This will exclude `exclude_me` (defined in `fields_to_exclude_from_single_schema`) and `_exclude_me_too` (private).

Same for `pydantic.BaseModel`:
```python
from typing import Optional, Union

from pydantic import BaseModel, computed_field

from schemantic.project import SchemanticProjectModelMixin


class TestModel(SchemanticProjectModelMixin, BaseModel):
    must_be: int
    we: str = "n"

    n: None = None
    age: Optional[int] = None
    new_age: Union[int, str, None] = None

    exclude_me: Optional[int] = None
    _exclude_me_too: Optional[float] = None

    @classmethod
    def fields_to_exclude_from_single_schema(cls) -> set[str]:
        upstream = super().fields_to_exclude_from_single_schema
        upstream.update(("exclude_me",))
        return upstream
```

### Install
```shell
pip install schemantic
```

For `toml` or `yaml` dumping and parsing
```shell
pip install schemantic[toml]
pip install schemantic[yaml]
```
