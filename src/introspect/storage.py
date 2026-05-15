"""File-system layout for introspect data under ~/.introspect/<id>/."""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

ROOT = Path.home() / '.introspect'
ID_RE = re.compile(r'^[A-Za-z0-9._-]+$')


def validate_id(id_: str) -> str:
    if not id_:
        raise ValueError("id cannot be empty")
    if id_ in {'.', '..'} or not ID_RE.fullmatch(id_):
        raise ValueError("invalid id: use only letters, numbers, '.', '_', and '-'")
    return id_


def id_dir(id_: str) -> Path:
    validate_id(id_)
    return ROOT / id_


def ensure(id_: str) -> Path:
    d = id_dir(id_)
    d.mkdir(parents=True, exist_ok=True)
    return d


def exists(id_: str) -> bool:
    return id_dir(id_).exists()


def require(id_: str) -> Path:
    d = id_dir(id_)
    if not d.exists():
        raise FileNotFoundError(f"no such id: {id_}")
    return d


def gen_id(cmd: list[str]) -> str:
    base = Path(cmd[0]).name.replace('/', '_') or 'cmd'
    h = hashlib.sha1((' '.join(cmd) + str(time.time_ns())).encode()).hexdigest()[:4]
    return f"{base}-{h}"


def read_meta(id_: str) -> dict:
    p = id_dir(id_) / 'meta.json'
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def write_meta(id_: str, **kv) -> None:
    p = id_dir(id_) / 'meta.json'
    cur = read_meta(id_)
    cur.update(kv)
    p.write_text(json.dumps(cur))


def list_ids() -> list[str]:
    if not ROOT.exists():
        return []
    return [d.name for d in sorted(ROOT.iterdir()) if (d / 'meta.json').exists()]


def is_alive(meta: dict) -> bool:
    import os
    pid = meta.get('pid')
    if not pid or meta.get('exited'):
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False
