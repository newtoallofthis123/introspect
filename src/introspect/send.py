"""Send bytes to a running id's pty master via its ctl.sock."""
from __future__ import annotations

import socket

from . import storage


def send(id_: str, data: bytes) -> None:
    d = storage.require(id_)
    sock_path = d / 'ctl.sock'
    if not sock_path.exists():
        raise FileNotFoundError(f"{id_} has no ctl.sock — is it running?")
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        s.connect(str(sock_path))
        s.sendall(data)
    finally:
        s.close()
