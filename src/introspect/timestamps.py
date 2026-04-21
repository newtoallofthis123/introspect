"""Per-line wall-clock timestamps stored in a fixed-width sidecar (ts.log).

Each record is `YYYY-MM-DDTHH:MM:SS.ffffff\\n` — 27 bytes. Line N of the log
corresponds to record N-1 (0-indexed) in ts.log, so random access is O(1).
"""
from __future__ import annotations

import datetime
import re
from pathlib import Path

from . import storage

TS_FMT = "%Y-%m-%dT%H:%M:%S.%f"
TS_LEN = 26
RECORD = TS_LEN + 1  # + \n


def now_ts_bytes() -> bytes:
    return datetime.datetime.now().strftime(TS_FMT).encode() + b'\n'


def ts_path(id_: str) -> Path:
    return storage.id_dir(id_) / 'ts.log'


def ts_at_line(id_: str, line_no: int) -> datetime.datetime | None:
    """1-indexed line number → datetime, or None if unknown."""
    p = ts_path(id_)
    if not p.exists() or line_no < 1:
        return None
    offset = (line_no - 1) * RECORD
    try:
        with open(p, 'rb') as f:
            f.seek(offset)
            rec = f.read(TS_LEN)
        return datetime.datetime.strptime(rec.decode(), TS_FMT)
    except Exception:
        return None


def ts_count(id_: str) -> int:
    p = ts_path(id_)
    try:
        return p.stat().st_size // RECORD
    except FileNotFoundError:
        return 0


DUR_RE = re.compile(r'^(\d+)(ms|s|m|h|d)$')

_ABS_FORMATS = [
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%H:%M:%S",
    "%H:%M",
]


def parse_absolute(spec: str) -> datetime.datetime | None:
    now = datetime.datetime.now()
    for f in _ABS_FORMATS:
        try:
            dt = datetime.datetime.strptime(spec, f)
        except ValueError:
            continue
        if '%Y' not in f:
            dt = dt.replace(year=now.year, month=now.month, day=now.day)
        return dt
    return None


def parse_duration(spec: str) -> datetime.timedelta | None:
    m = DUR_RE.match(spec)
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2)
    sec = {'ms': n / 1000, 's': n, 'm': n * 60, 'h': n * 3600, 'd': n * 86400}[unit]
    return datetime.timedelta(seconds=sec)


def resolve_spec(id_: str, spec: str) -> int:
    """Resolve a spec (duration / absolute / mark name) to a 1-indexed line number."""
    from . import marks

    mk = marks.find(id_, spec)
    if mk:
        return max(1, int(mk.get('line') or 1))

    dur = parse_duration(spec)
    if dur is not None:
        target = datetime.datetime.now() - dur
        return line_at_or_after(id_, target)

    abs_dt = parse_absolute(spec)
    if abs_dt is not None:
        return line_at_or_after(id_, abs_dt)

    raise ValueError(f"could not parse spec: {spec!r} (expected duration like '5m', absolute time, or mark name)")


def line_at_or_after(id_: str, target: datetime.datetime) -> int:
    """First line whose timestamp is >= target. 1-indexed. O(log N) via fixed-width bsearch."""
    p = ts_path(id_)
    if not p.exists():
        return 1
    count = p.stat().st_size // RECORD
    if count == 0:
        return 1
    with open(p, 'rb') as f:
        lo, hi = 0, count
        while lo < hi:
            mid = (lo + hi) // 2
            f.seek(mid * RECORD)
            rec = f.read(TS_LEN)
            try:
                dt = datetime.datetime.strptime(rec.decode(), TS_FMT)
            except Exception:
                return lo + 1
            if dt < target:
                lo = mid + 1
            else:
                hi = mid
    return lo + 1
