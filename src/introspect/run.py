"""Spawn a command under a pty; tee output to log + ts.log; accept send() over ctl.sock."""
from __future__ import annotations

import fcntl
import os
import pty
import select
import signal
import socket
import sys
import termios
import time
import tty

from . import storage, timestamps


def run(cmd: list[str], id_: str | None = None) -> int:
    if not cmd:
        raise ValueError("nothing to run")
    id_ = id_ or storage.gen_id(cmd)
    d = storage.ensure(id_)
    log_path = d / 'log'
    ts_path = d / 'ts.log'
    sock_path = d / 'ctl.sock'

    storage.write_meta(
        id_, id=id_, cmd=list(cmd), cwd=os.getcwd(),
        started=time.time(), pid=None, exited=None, exit_status=None,
    )

    if sys.stdout.isatty():
        sys.stdout.write(f"\x1b[2m[introspect id={id_}]\x1b[0m\n")
        sys.stdout.flush()

    logf = open(log_path, 'ab', buffering=0)
    tsf = open(ts_path, 'ab', buffering=0)

    try:
        sock_path.unlink()
    except FileNotFoundError:
        pass
    ctl = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    ctl.bind(str(sock_path))
    os.chmod(sock_path, 0o600)
    ctl.listen(4)
    ctl.setblocking(False)

    pid, fd = pty.fork()
    if pid == 0:
        try:
            os.execvp(cmd[0], list(cmd))
        except FileNotFoundError:
            sys.stderr.write(f"introspect: {cmd[0]}: not found\n")
            os._exit(127)

    storage.write_meta(id_, pid=pid)

    def set_size(*_):
        try:
            s = fcntl.ioctl(sys.stdin.fileno(), termios.TIOCGWINSZ, b'\0' * 8)
            fcntl.ioctl(fd, termios.TIOCSWINSZ, s)
        except Exception:
            pass

    set_size()
    signal.signal(signal.SIGWINCH, set_size)

    stdin_is_tty = sys.stdin.isatty()
    old_attrs = None
    if stdin_is_tty:
        try:
            old_attrs = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin)
        except termios.error:
            old_attrs = None

    clients: list[socket.socket] = []
    status = 0
    stdin_open = True

    try:
        while True:
            readable = [fd, ctl] + clients
            if stdin_open:
                readable.append(sys.stdin)
            try:
                r, _, _ = select.select(readable, [], [])
            except (InterruptedError, OSError):
                continue

            if fd in r:
                try:
                    data = os.read(fd, 8192)
                except OSError:
                    data = b''
                if not data:
                    break
                os.write(sys.stdout.fileno(), data)
                logf.write(data)
                n = data.count(b'\n')
                if n:
                    tsf.write(timestamps.now_ts_bytes() * n)

            if stdin_open and sys.stdin in r:
                try:
                    data = os.read(sys.stdin.fileno(), 8192)
                except OSError:
                    data = b''
                if not data:
                    stdin_open = False
                else:
                    os.write(fd, data)

            if ctl in r:
                try:
                    client, _ = ctl.accept()
                    client.setblocking(False)
                    clients.append(client)
                except BlockingIOError:
                    pass

            for c in list(clients):
                if c in r:
                    try:
                        data = c.recv(8192)
                    except (BlockingIOError, ConnectionError):
                        data = b''
                    if not data:
                        clients.remove(c)
                        try:
                            c.close()
                        except Exception:
                            pass
                    else:
                        os.write(fd, data)
    finally:
        if stdin_is_tty and old_attrs is not None:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_attrs)
            except Exception:
                pass
        for c in clients:
            try:
                c.close()
            except Exception:
                pass
        try:
            ctl.close()
        except Exception:
            pass
        try:
            sock_path.unlink()
        except FileNotFoundError:
            pass
        try:
            os.close(fd)
        except Exception:
            pass
        try:
            _, status = os.waitpid(pid, 0)
        except ChildProcessError:
            status = 0
        logf.close()
        tsf.close()
        storage.write_meta(id_, exited=time.time(), exit_status=status)

    if os.WIFEXITED(status):
        return os.WEXITSTATUS(status)
    if os.WIFSIGNALED(status):
        return 128 + os.WTERMSIG(status)
    return 0
