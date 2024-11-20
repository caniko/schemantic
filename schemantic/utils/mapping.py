from typing import Any, Optional, TypeVar


def update_assert_disjoint(dict_a: dict, dict_b: dict, error_msg_add: Optional[str] = None) -> None:
    """
    Detects key collisions between two dictionaries.

    :raises ValueError: If a key collision is detected.
    """
    if any(k in dict_a and dict_a[k] != dict_a[k] for k in dict_b):
        error_msg_add = f"{error_msg_add} " if error_msg_add else ""
        msg = f"{error_msg_add}Colliding keys: {set(dict_a).intersection(dict_b)}"
        raise ValueError(msg)

    dict_a.update(dict_b)


T = TypeVar("T")


def extract_sort_keys(source: dict[T, Any]) -> list[T]:
    return sorted(source.keys())


def dict_sorted_by_dict_key(source: dict) -> dict:
    return dict(sorted(source.items(), key=lambda kv: kv[0]))
