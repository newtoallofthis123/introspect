"""Named regex filters stored in meta.json['filters']."""
from __future__ import annotations

from . import storage


def set_(id_: str, name: str, pattern: str) -> None:
    meta = storage.read_meta(id_)
    filters = dict(meta.get('filters') or {})
    filters[name] = pattern
    storage.write_meta(id_, filters=filters)


def get(id_: str, name: str) -> str | None:
    return (storage.read_meta(id_).get('filters') or {}).get(name)


def list_(id_: str) -> dict[str, str]:
    return dict(storage.read_meta(id_).get('filters') or {})


def remove(id_: str, name: str) -> bool:
    meta = storage.read_meta(id_)
    filters = dict(meta.get('filters') or {})
    if name not in filters:
        return False
    filters.pop(name)
    storage.write_meta(id_, filters=filters)
    return True
