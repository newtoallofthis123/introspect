# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv sync                              # install deps from uv.lock
uv run introspect --help             # run the CLI from source
uv run python -m unittest            # full test suite
uv run python -m unittest tests.test_run_integration            # single module
uv run python -m unittest tests.test_run_integration.TestRun.test_basic   # single test
```

No linter/formatter is configured. Only runtime dep is `click`; everything else is stdlib. Python 3.11+. macOS/Linux only (pty + Unix sockets).

## Architecture

`introspect` is a pty-based flight recorder: wrap a command, capture every byte it writes to its terminal, and query the capture later from any shell. Source lives in `src/introspect/`, one module per concern. `cli.py` (Click) is the only entry point and dispatches to the other modules.

**Per-run data lives at `~/.introspect/<id>/`** and is the contract between the live process and any later query:

| File          | Role                                                                  |
|---------------|-----------------------------------------------------------------------|
| `log`         | Raw pty bytes verbatim (ANSI escapes preserved).                      |
| `ts.log`      | Fixed-width nanosecond timestamp per `log` line — enables fast time slicing without scanning content. |
| `marks.jsonl` | Append-only named bookmarks (`name`, line number, optional message).  |
| `meta.json`   | `cmd`, `pid`, `exited`, exit status, saved named filters.             |
| `ctl.sock`    | Unix socket for `introspect send` (exists only while the run is live).|

`storage.py` owns this layout and id validation. **Any new file under `<id>/` should go through `storage.py`.**

**Live capture (`run.py`)** forks a pty, execs the child with its stdio on the slave, and runs a select loop on the master fd, the user's stdin, and `ctl.sock`. Bytes from the master are written to both the user's stdout and `log`; for each newline written, a timestamp is appended to `ts.log` so the two files stay line-aligned. `meta.json` is updated on start and exit. The fixed-width-timestamp invariant is what makes `since`/`between` cheap — do not break line alignment between `log` and `ts.log`.

**Query path (read-only, runs in a separate process from the live one):**
- `reader.py` — slice by line number / tail / follow.
- `timestamps.py` — parse `SPEC` (duration like `10m`, absolute time, or marker name) and binary-search `ts.log` to map time → line number, which then feeds `reader`.
- `marks.py` — read/write `marks.jsonl`; markers are also valid time specs.
- `filters.py` — named regexes stored in `meta.json`, applied as a post-filter on streamed lines.
- `search.py` — shells out to `rg`; passes through user flags. Optional dep.
- `send.py` — connects to `ctl.sock` and writes bytes, so the live process's select loop forwards them into the child's stdin.

Queries never touch the live process directly; they only read files (plus the socket for `send`). This is the property the README's "agent-ready" pitch depends on — preserve it.

## Conventions

- One concept per module; `cli.py` stays a thin dispatcher. New subcommands wire to a function in the relevant module rather than embedding logic in `cli.py`.
- Ids are validated by `storage.validate_id` (`[A-Za-z0-9._-]+`, not `.`/`..`). Never build paths under `~/.introspect/` without going through `storage.id_dir`.
- Tests use stdlib `unittest`. Pty-touching integration tests must stay small and deterministic (see `CONTRIBUTING.md`).
- Scope discipline: per `CONTRIBUTING.md`, this tool is deliberately not a supervisor, log-rotator, or framework-specific parser. Decline scope creep in that direction.

## Agent skill

`.claude/skills/introspect/` ships a skill that teaches Claude Code how to query captures of long-running processes the user started under `introspect`. If you change CLI surface (command names, flags, output shape), update that skill in the same change.
