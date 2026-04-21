"""Read log bytes and split into lines. ANSI-stripping and filter application."""
from __future__ import annotations

import re
from . import storage

ANSI_RE = re.compile(rb'\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07]*(?:\x07|\x1b\\)|\x1b[@-Z\\-_]')


def strip_ansi(b: bytes) -> bytes:
    return ANSI_RE.sub(b'', b)


def read_log_bytes(id_: str) -> bytes:
    return (storage.require(id_) / 'log').read_bytes()


def split_lines(data: bytes, strip_ansi_: bool = True) -> list[bytes]:
    """Split raw log bytes into lines. Only \\n terminates (reader/writer agree on this)."""
    if strip_ansi_:
        data = strip_ansi(data)
    data = data.replace(b'\r\n', b'\n')
    if not data:
        return []
    lines = data.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()
    return lines


def read_lines(id_: str, strip_ansi_: bool = True) -> list[bytes]:
    return split_lines(read_log_bytes(id_), strip_ansi_=strip_ansi_)


def line_count(id_: str) -> int:
    """Count \\n bytes in log — matches what split_lines will yield for \\n-terminated data."""
    path = storage.require(id_) / 'log'
    if not path.exists():
        return 0
    n = 0
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            n += chunk.count(b'\n')
    return n


def compile_filter(pattern: str | None) -> re.Pattern | None:
    if not pattern:
        return None
    return re.compile(pattern.encode())


def apply_filter(lines_with_nums: list[tuple[int, bytes]], rx: re.Pattern | None) -> list[tuple[int, bytes]]:
    if rx is None:
        return lines_with_nums
    return [(n, l) for (n, l) in lines_with_nums if rx.search(l)]


def number_lines(lines: list[bytes], start: int = 1) -> list[tuple[int, bytes]]:
    return [(start + i, l) for i, l in enumerate(lines)]
