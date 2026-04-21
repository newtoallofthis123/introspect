"""Named markers stored in marks.jsonl per id."""
from __future__ import annotations

import datetime
import json
from pathlib import Path

from . import storage


def _path(id_: str) -> Path:
    return storage.id_dir(id_) / 'marks.jsonl'


def add(id_: str, name: str, note: str | None = None) -> dict:
    from . import reader, timestamps

    line = reader.line_count(id_)
    ts_dt = timestamps.ts_at_line(id_, line) if line > 0 else None
    ts = (ts_dt or datetime.datetime.now()).isoformat()
    entry = {'name': name, 'line': line, 'ts': ts}
    if note:
        entry['note'] = note
    p = _path(id_)
    # replace if name already exists
    existing = list_(id_)
    existing = [m for m in existing if m.get('name') != name]
    existing.append(entry)
    p.write_text(''.join(json.dumps(m) + '\n' for m in existing))
    return entry


def list_(id_: str) -> list[dict]:
    p = _path(id_)
    if not p.exists():
        return []
    out = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def find(id_: str, name: str) -> dict | None:
    for m in list_(id_):
        if m.get('name') == name:
            return m
    return None


def remove(id_: str, name: str) -> bool:
    all_ = list_(id_)
    kept = [m for m in all_ if m.get('name') != name]
    if len(kept) == len(all_):
        return False
    p = _path(id_)
    p.write_text(''.join(json.dumps(m) + '\n' for m in kept))
    return True
