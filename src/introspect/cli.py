"""Click CLI for introspect."""
from __future__ import annotations

import re
import sys

import click

from . import filters as F
from . import marks as M
from . import reader as R
from . import run as RUN
from . import search as SEARCH
from . import send as SEND
from . import storage
from . import timestamps as T


KNOWN = {
    'run', 'ls', 'get-lines', 'tail', 'since', 'between',
    'mark', 'marks', 'unmark', 'search', 'filter', 'filters',
    'send', 'rm', 'clear', 'path', 'help', '--help', '-h',
}


# ---------- helpers ----------

def _parse_range(tokens: tuple[str, ...]) -> tuple[int | None, int | None]:
    """Accept (N, M), (N_M,), (N..M,), or (N,)."""
    if not tokens:
        return None, None
    if len(tokens) == 1:
        t = tokens[0]
        if '_' in t:
            a, b = t.split('_', 1)
        elif '..' in t:
            a, b = t.split('..', 1)
        else:
            return int(t), int(t)
        return int(a), int(b)
    return int(tokens[0]), int(tokens[1])


def _write_lines(pairs: list[tuple[int, bytes]]) -> None:
    if not pairs:
        return
    width = len(str(pairs[-1][0]))
    for n, line in pairs:
        sys.stdout.buffer.write(f"{n:>{width}}: ".encode() + line + b'\n')
    sys.stdout.flush()


def _resolve_filter(id_: str, name: str | None) -> re.Pattern | None:
    if not name:
        return None
    pat = F.get(id_, name)
    if pat is None:
        raise click.ClickException(f"filter {name!r} not defined for {id_}")
    return re.compile(pat.encode())


# ---------- group ----------

@click.group(context_settings={'help_option_names': ['-h', '--help']})
def cli():
    """introspect — run anything under a pty, log every byte, query later."""


# ---------- run ----------

@cli.command(context_settings={'ignore_unknown_options': True, 'allow_extra_args': True})
@click.option('--id', 'id_', default=None, help="explicit id (otherwise auto-generated)")
@click.argument('cmd', nargs=-1, type=click.UNPROCESSED)
def run(id_, cmd):
    """Run CMD under introspect. Use -- to separate flags from the child command."""
    cmd = list(cmd)
    if cmd and cmd[0] == '--':
        cmd = cmd[1:]
    if not cmd:
        raise click.UsageError("nothing to run")
    sys.exit(RUN.run(cmd, id_=id_))


# ---------- ls ----------

@cli.command()
def ls():
    """List known ids."""
    ids = storage.list_ids()
    if not ids:
        return
    rows = []
    for i in ids:
        m = storage.read_meta(i)
        status = 'running' if storage.is_alive(m) else 'exited'
        try:
            lines = R.line_count(i)
        except Exception:
            lines = 0
        cmd = ' '.join(m.get('cmd') or [])
        rows.append((i, status, str(lines), cmd))
    w = [max(len(r[c]) for r in rows) for c in range(3)]
    for r in rows:
        click.echo(f"{r[0]:<{w[0]}}  {r[1]:<{w[1]}}  {r[2]:>{w[2]}}L  {r[3]}")


# ---------- get-lines ----------

@cli.command('get-lines')
@click.argument('id_', metavar='ID')
@click.argument('range_', nargs=-1, metavar='[N [M]] | [N_M] | [N..M]')
@click.option('--raw', is_flag=True, help="keep ANSI escapes")
@click.option('--filter', 'filter_name', default=None, help="named filter to apply")
@click.option('--grep', default=None, help="ad-hoc regex to apply")
def get_lines(id_, range_, raw, filter_name, grep):
    """Print lines N..M from ID's log."""
    start, end = _parse_range(range_)
    lines = R.read_lines(id_, strip_ansi_=not raw)
    start = start or 1
    end = end or len(lines)
    start = max(1, start)
    end = min(end, len(lines))
    sliced = R.number_lines(lines[start - 1:end], start=start)
    rx_f = _resolve_filter(id_, filter_name)
    sliced = R.apply_filter(sliced, rx_f)
    if grep:
        sliced = R.apply_filter(sliced, re.compile(grep.encode()))
    _write_lines(sliced)


# ---------- tail ----------

@cli.command()
@click.argument('id_', metavar='ID')
@click.argument('n', type=int, required=False, default=20)
@click.option('-f', '--follow', is_flag=True)
@click.option('--raw', is_flag=True)
@click.option('--filter', 'filter_name', default=None)
def tail(id_, n, follow, raw, filter_name):
    """Last N lines, optionally follow."""
    import time as _time

    lines = R.read_lines(id_, strip_ansi_=not raw)
    total = len(lines)
    start = max(1, total - n + 1)
    pairs = R.number_lines(lines[start - 1:], start=start)
    rx_f = _resolve_filter(id_, filter_name)
    pairs = R.apply_filter(pairs, rx_f)
    _write_lines(pairs)
    if not follow:
        return

    log = storage.require(id_) / 'log'
    next_line = total + 1
    with open(log, 'rb') as f:
        f.seek(0, 2)
        buf = b''
        while True:
            chunk = f.read(8192)
            if not chunk:
                _time.sleep(0.1)
                continue
            buf += chunk
            while b'\n' in buf:
                idx = buf.index(b'\n')
                raw_line, buf = buf[:idx], buf[idx + 1:]
                line = raw_line if raw else R.strip_ansi(raw_line.replace(b'\r\n', b'\n'))
                pair = [(next_line, line)]
                if rx_f:
                    pair = R.apply_filter(pair, rx_f)
                if pair:
                    sys.stdout.buffer.write(f"{next_line}: ".encode() + pair[0][1] + b'\n')
                    sys.stdout.flush()
                next_line += 1


# ---------- since / between ----------

@cli.command()
@click.argument('id_', metavar='ID')
@click.argument('spec')
@click.option('--raw', is_flag=True)
@click.option('--filter', 'filter_name', default=None)
def since(id_, spec, raw, filter_name):
    """Print lines since a duration ('5m'), time ('09:00'), or mark name."""
    start = T.resolve_spec(id_, spec)
    lines = R.read_lines(id_, strip_ansi_=not raw)
    end = len(lines)
    pairs = R.number_lines(lines[start - 1:end], start=start)
    pairs = R.apply_filter(pairs, _resolve_filter(id_, filter_name))
    _write_lines(pairs)


@cli.command()
@click.argument('id_', metavar='ID')
@click.argument('a')
@click.argument('b')
@click.option('--raw', is_flag=True)
@click.option('--filter', 'filter_name', default=None)
def between(id_, a, b, raw, filter_name):
    """Print lines between two specs (durations, times, or mark names)."""
    s1 = T.resolve_spec(id_, a)
    s2 = T.resolve_spec(id_, b)
    lo, hi = min(s1, s2), max(s1, s2)
    lines = R.read_lines(id_, strip_ansi_=not raw)
    hi = min(hi, len(lines))
    pairs = R.number_lines(lines[lo - 1:hi], start=lo)
    pairs = R.apply_filter(pairs, _resolve_filter(id_, filter_name))
    _write_lines(pairs)


# ---------- marks ----------

@cli.command()
@click.argument('id_', metavar='ID')
@click.argument('name')
@click.option('-m', '--note', default=None)
def mark(id_, name, note):
    """Create a marker at the current end of ID's log."""
    entry = M.add(id_, name, note=note)
    click.echo(f"{entry['name']}\tline {entry['line']}\t{entry['ts']}")


@cli.command()
@click.argument('id_', metavar='ID')
def marks(id_):
    """List markers."""
    for m in M.list_(id_):
        note = f"\t{m['note']}" if m.get('note') else ''
        click.echo(f"{m['name']}\tline {m['line']}\t{m['ts']}{note}")


@cli.command()
@click.argument('id_', metavar='ID')
@click.argument('name')
def unmark(id_, name):
    """Remove a marker."""
    if not M.remove(id_, name):
        raise click.ClickException(f"no such marker: {name}")


# ---------- search (rg) ----------

@cli.command(context_settings={'ignore_unknown_options': True, 'allow_extra_args': True})
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def search(args):
    """Regex search via rg. Usage: search PATTERN | search ID PATTERN [rg-args...]."""
    args = list(args)
    if not args:
        raise click.UsageError("need a pattern")
    # If first token is a known id, treat as id + pattern; else pattern (search all).
    if args[0] in storage.list_ids():
        id_, pattern, *extra = args
        sys.exit(SEARCH.search_id(id_, pattern, extra))
    else:
        pattern, *extra = args
        sys.exit(SEARCH.search_all(pattern, extra))


# ---------- filters ----------

@cli.group('filter')
def filter_grp():
    """Manage named regex filters per id."""


@filter_grp.command('set')
@click.argument('id_', metavar='ID')
@click.argument('name')
@click.argument('pattern')
def filter_set(id_, name, pattern):
    """Save a named regex filter."""
    storage.require(id_)
    F.set_(id_, name, pattern)


@filter_grp.command('ls')
@click.argument('id_', metavar='ID')
def filter_ls(id_):
    """List named filters for ID."""
    for name, pat in F.list_(id_).items():
        click.echo(f"{name}\t{pat}")


@filter_grp.command('rm')
@click.argument('id_', metavar='ID')
@click.argument('name')
def filter_rm(id_, name):
    """Remove a named filter."""
    if not F.remove(id_, name):
        raise click.ClickException(f"no such filter: {name}")


# ---------- send ----------

@cli.command()
@click.argument('id_', metavar='ID')
@click.argument('text', nargs=-1, required=True)
@click.option('--raw', is_flag=True, help="don't append newline")
def send(id_, text, raw):
    """Send input to ID's running process (writes to its pty master)."""
    payload = ' '.join(text)
    data = payload.encode()
    if not raw:
        data += b'\n'
    SEND.send(id_, data)


# ---------- housekeeping ----------

@cli.command()
@click.argument('id_', metavar='ID')
def rm(id_):
    """Delete an id (log + metadata)."""
    import shutil
    d = storage.require(id_)
    shutil.rmtree(d)


@cli.command()
@click.argument('id_', metavar='ID')
def clear(id_):
    """Truncate an id's log and ts.log."""
    d = storage.require(id_)
    (d / 'log').write_bytes(b'')
    ts = d / 'ts.log'
    if ts.exists():
        ts.write_bytes(b'')


@cli.command()
@click.argument('id_', metavar='ID')
def path(id_):
    """Print the storage path for ID."""
    click.echo(str(storage.require(id_)))


# ---------- entrypoint with bare-command fallback ----------

def main() -> None:
    argv = sys.argv[1:]
    # Bare `introspect <cmd...>` → rewrite to `run -- <cmd...>`
    if argv and argv[0] not in KNOWN and not argv[0].startswith('-'):
        sys.argv = [sys.argv[0], 'run', '--'] + argv
    elif argv and argv[0] == '--id':
        # `introspect --id foo -- cmd...` → `run --id foo -- cmd...`
        sys.argv = [sys.argv[0], 'run'] + argv
    try:
        cli(standalone_mode=False)
    except click.ClickException as e:
        e.show()
        sys.exit(e.exit_code)
    except (FileNotFoundError, RuntimeError, ValueError) as e:
        click.ClickException(str(e)).show()
        sys.exit(1)


if __name__ == '__main__':
    main()
