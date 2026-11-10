# Schemantic vision

Schemantic is a Python library that derives configuration-file schemas from
existing models and classes. Given a `pydantic.BaseModel`, a plain class, or a
dataclass, it produces a schema document that can be dumped to YAML or TOML and
parsed back into typed instances. It organises those schemas in three
paradigms: homologue, grouped, and culture.

## Problem

A project that stores configuration in files already has the shape of that
configuration in Python types. Re-declaring it in YAML, TOML, or a separate
schema language duplicates the definition and drifts from the code. What is
missing is a way to derive the file schema from the type, record which fields
are required, and allow per-instance overrides that parse back into the original
type.

## Principles

- The originating type is the source of truth. Schemas derive from classes,
  dataclasses, and pydantic models rather than from a hand-written schema file.
- Three composition paradigms, each with the same methods: `HomologueSchemer`
  for sibling instances of one type, `GroupSchemer` for several types managed
  together, and `CultureSchemer` for several schemas under one culture.
- `.schema()` and `.dump()` produce the document, and
  `load_into_mapping_name_to_instance()` parses it back into typed instances, so
  the generated document is both the artifact and the input.
- Instance names are explicit. Homologue schemas accept
  `instance_name_to_pre_definition` and `instance_name_getter` so a per-instance
  section has a defined initial value.
- Per-type control stays with the type. `SchemanticProjectMixin` lets a class
  exclude fields and shape its own single schema.
- Optional formats are extras: `toml` (rtoml) and `yaml` (ruamel-yaml) install
  separately from the core dependency on pydantic and `ordered-set`.

## Scope

- Schema generation from pydantic models, plain classes, dataclasses, and
  pydantic dataclasses.
- Homologue, group, and culture schema composition.
- Dump to YAML/TOML and parse back into typed instances.
- Field exclusion and required/field-info bookkeeping in the generated schema.

## Direction

The Unreleased changelog entries are the current work: preserving boolean,
numeric, and container defaults in generated schemas, preserving zero and false
defaults in rendered type information, and moving development dependencies and
locking from Poetry to uv.

## Place in the fleet

No canix consumer was found. Canix names `schemantic` in the atlas
`simit-updater` registry and names `schemantic-private` in a developer-tooling
repository list, which is a separate project.
