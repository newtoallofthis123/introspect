"""Regex search via ripgrep."""
from __future__ import annotations

import shutil
import subprocess

from . import storage


def _rg() -> str:
    rg = shutil.which('rg')
    if not rg:
        raise RuntimeError("rg (ripgrep) not found in PATH")
    return rg


def search_id(id_: str, pattern: str, extra: list[str]) -> int:
    target = str(storage.require(id_) / 'log')
    cmd = [_rg(), '-n'] + list(extra) + ['--', pattern, target]
    return subprocess.call(cmd)


def search_all(pattern: str, extra: list[str]) -> int:
    ids = storage.list_ids()
    if not ids:
        return 1
    logs = [str(storage.id_dir(i) / 'log') for i in ids]
    cmd = [_rg(), '-n', '-H'] + list(extra) + ['--', pattern] + logs
    return subprocess.call(cmd)
