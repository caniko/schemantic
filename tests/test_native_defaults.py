from pydantic import BaseModel

from schemantic import SingleSchemer


def test_schema_preserves_native_falsy_and_container_defaults():
    class Settings(BaseModel):
        enabled: bool = False
        count: int = 0
        scale: float = 0.5
        labels: tuple[str, ...] = ()

    schemer = SingleSchemer.from_origin(Settings)
    assert schemer.optional["enabled"].owner_to_default[Settings] is False
    assert schemer.optional["count"].owner_to_default[Settings] == 0
    assert schemer.optional["scale"].owner_to_default[Settings] == 0.5
    # Pydantic's JSON schema represents tuple defaults as JSON arrays.
    assert schemer.optional["labels"].owner_to_default[Settings] == []
    rendered = schemer.optional["enabled"].model_dump()
    assert "False" in rendered
