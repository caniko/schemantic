from typing import Any, Hashable, Optional


def update_assert_disjoint(dict_a: dict, dict_b: dict, error_msg_add: Optional[str] = None) -> None:
    """
    Detects key collisions between two dictionaries.

    :param dict_a: The first dictionary.
    :param dict_b: The second dictionary.
    :raises ValueError: If a key collision is detected.
    """
    if any(k in dict_a and dict_a[k] != dict_a[k] for k in dict_b):
        error_msg_add = f"{error_msg_add} " if error_msg_add else ""
        msg = f"{error_msg_add}Colliding keys: {set(dict_a).intersection(dict_b)}"
        raise ValueError(msg)

    dict_a.update(dict_b)


def sorted_by_dict_key(source: dict) -> list[tuple[Hashable, Any]]:
    return sorted(source.items(), key=lambda kv: kv[0])


def dict_sorted_by_dict_key(source: dict) -> dict:
    return dict(sorted_by_dict_key(source))
