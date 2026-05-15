# introspect

**Run any command. Query its output later.**

`introspect` is a tiny CLI that wraps any command in a pseudo-terminal, captures every byte it prints, and lets you slice, search, and replay that output from another pane — minutes or hours later — without ever interrupting the process.

Think of it as a flight recorder for your shell.

![python](https://img.shields.io/badge/python-3.11%2B-blue)
![deps](https://img.shields.io/badge/deps-click-lightgrey)
![status](https://img.shields.io/badge/status-alpha-yellow)

---

## Why?

You've been here:

- Your dev server has been running for an hour. Something broke 20 minutes ago. Your scrollback only goes back 10.
- You want to grep your Rails logs but they scroll past too fast.
- You're running IEx and want to poke it from another terminal with a one-liner.
- You want to compare "before migration" and "after migration" output. There is no good way.

`introspect` fixes all of those in one small tool.

```bash
introspect mix phx.server        # run normally — colors, prompts, TUI all work
# ... 3 hours later, from any terminal:
introspect since api 10m --filter error
introspect between api before-deploy after-deploy
introspect send api 'Logger.configure(level: :debug)'
```

---

## Install

From GitHub:

```bash
uv tool install git+https://github.com/newtoallofthis123/introspect
```

For local development:

```bash
git clone https://github.com/newtoallofthis123/introspect
cd introspect
uv tool install ./introspect
```

Requires Python 3.11+. Install [`rg`](https://github.com/BurntSushi/ripgrep) if you want `search` (most people already have it).

Platform support: macOS and Linux. Windows is not supported by the current pty / Unix-socket design.

---

## Quick tour

```bash
# Run anything under introspect. An id is auto-generated (e.g. mix-a3f2).
$ introspect mix phx.server
[introspect id=mix-a3f2]
...

# In another terminal:
$ introspect ls
mix-a3f2   running   4821L   mix phx.server

# Tail it, optionally follow:
$ introspect tail mix-a3f2 -f

# Go back 5 minutes:
$ introspect since mix-a3f2 5m

# Bookmark an interesting moment:
$ introspect mark mix-a3f2 before-deploy -m "about to ship"
$ introspect since mix-a3f2 before-deploy

# Regex search (powered by ripgrep):
$ introspect search mix-a3f2 'timeout' -C 3

# Inject input into a running process (IEx, REPLs, servers that read stdin):
$ introspect send mix-a3f2 'Logger.configure(level: :debug)'

# Define your own filters — "error", "slow", whatever matters to you:
$ introspect filter set mix-a3f2 error '\b(ERROR|FATAL)\b'
$ introspect tail mix-a3f2 -f --filter error
```

---

## For coding agents

`introspect` gives agents a stable way to inspect long-running processes without taking over your terminal.

Run your server under `introspect`:

```bash
introspect --id web -- npm run dev
introspect --id api -- mix phx.server
introspect --id worker -- python -m celery -A app worker
```

Then a coding agent can query the captured logs from another shell:

```bash
introspect tail web 80
introspect search api 'ERROR|Exception|500' -C 5
introspect since worker 10m
```

That means your Next.js server, Elixir/Phoenix server, watcher, REPL, build, or pretty much any long-running command can keep running normally while the agent checks recent output, searches for failures, compares before/after behavior, or reads around an error.

This repo includes a Claude skill at `.claude/skills/introspect/` so compatible agents know how to discover runs, tail logs, search with context, and use markers/filters safely.

---

## Features

- **Zero-ceremony capture.** Just prefix any command with `introspect`. Auto-generates an id, shows it on the first line, runs normally.
- **True terminal behavior.** Runs the child under a real pty — colors, prompts, line editing, progress bars, IEx, `vim` all work exactly as they should.
- **Flight-recorder logs.** Every byte written to the terminal is captured to `~/.introspect/<id>/log` and preserved verbatim.
- **Time-based queries.** `since 5m`, `since 09:00`, `between <spec> <spec>`. Backed by a fixed-width timestamp sidecar — fast even on huge logs.
- **Markers.** `mark`, `marks`, `since <name>`, `between <a> <b>` — bookmarks for the moments that matter.
- **Named filters.** Define what "error" or "slow" means for *your* process, once. Reuse everywhere.
- **Full-text search.** `introspect search` shells to `rg` — pass through `-C`, `-i`, anything.
- **Input injection.** `introspect send` writes to a running process's stdin via a per-run unix socket. Drive your REPL from another pane.
- **Agent-ready.** The included `.claude` skill teaches agents how to inspect captured runs without interrupting your server.
- **One dep.** Just `click`. Everything else is stdlib.

---

## Commands at a glance

| Command | What it does |
|---|---|
| `introspect <cmd...>` | Run a command under introspect (bare form, auto id). |
| `introspect --id NAME -- <cmd...>` | Run with an explicit id. |
| `introspect ls` | List all known runs. |
| `introspect tail ID [N] [-f]` | Last N lines, optionally follow. |
| `introspect get-lines ID N M` | Slice by line range (`100 500`, `100_500`, `100..500` all work). |
| `introspect since ID SPEC` | Lines since a duration, absolute time, or marker. |
| `introspect between ID SPEC1 SPEC2` | Lines between two specs. |
| `introspect mark ID NAME [-m note]` | Drop a marker at the current line. |
| `introspect marks ID` | List markers. |
| `introspect unmark ID NAME` | Remove a marker. |
| `introspect search [ID] PATTERN` | Regex search via ripgrep (single id or all). |
| `introspect filter set ID NAME REGEX` | Save a named filter. |
| `introspect filter ls ID` / `filter rm ID NAME` | Manage filters. |
| `introspect send ID 'text'` | Send input to a running process via unix socket. |
| `introspect clear ID` | Truncate the log. |
| `introspect rm ID` | Delete everything for an id. |
| `introspect path ID` | Print the storage directory. |

Common flags: `--raw` (keep ANSI escapes), `--filter NAME` (apply a named filter).

---

## How it works (the short version)

Every run creates a directory at `~/.introspect/<id>/`:

```
log          raw pty bytes
ts.log       one fixed-width timestamp per log line
marks.jsonl  named bookmarks
meta.json    cmd, pid, exit status, saved filters
ctl.sock     unix socket for `send` (while running)
```

`introspect run` forks a pseudo-terminal, wires the child's stdio to the slave end, and holds the master. A `select` loop copies bytes between:

- the pty master and your stdout (so you see it),
- the pty master and the log (so we capture it),
- your stdin and the pty master (so typing works),
- the unix socket and the pty master (so `send` works).

Every `\n` in the child's output appends one fixed-width wall-clock record to `ts.log`. Because records are fixed width, line → timestamp is `O(1)` seek and `since 5m` is an `O(log N)` binary search.

That's the whole design.

---

## Non-goals

A short list of things `introspect` deliberately doesn't try to do:

- **Not a supervisor.** Use `systemd`, `tmux`, or `overmind` to keep things alive across crashes.
- **No log rotation.** Logs grow until you `introspect clear`.
- **No live multi-terminal viewing.** Other terminals can query and `send`, but don't get a live byte stream of the child.
- **No framework-specific log parsing.** Everything is byte-level. Use named filters if you want "level" semantics.

These are load-bearing omissions — they keep the tool small and composable.

---

## Project layout

```
src/introspect/
  cli.py          click commands + bare-command fallback
  run.py          pty fork + select loop + ts.log writer + ctl.sock
  reader.py       log bytes → lines, ANSI strip, filter application
  timestamps.py   ts.log format, spec parsing, bsearch
  marks.py        marks.jsonl CRUD
  filters.py      named regexes in meta.json
  search.py       rg shell-out
  send.py         unix-socket client
  storage.py      directory layout and meta.json helpers
```

~950 lines. Python 3.11+. One dep.

---

## Contributing

Small tool, opinionated scope. Bug reports and pull requests welcome — open an issue first if you're proposing a sizeable feature so we can talk about fit.

```bash
uv sync
uv run python -m unittest
uv run introspect --help
```

Good starter ideas if you want to hack on it:

- `introspect attach ID` — live tail + `send` in one interactive terminal.
- JSON output mode (`--json`) on query commands for agent use.
- Per-id process metrics sidecar (RSS, CPU) sampled every 1s.
- Structured-log awareness (`--field level=error` when `log` is JSON-lines).

---

## License

MIT.
