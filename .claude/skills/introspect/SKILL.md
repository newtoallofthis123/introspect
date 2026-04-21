---
name: introspect
description: Query the stdout/stderr history of long-lived commands (dev servers, REPLs, watchers, builds, pipelines) that the user launched under the `introspect` pty flight-recorder. Use when the user asks you to debug a running process, investigate an error from earlier, compare output before/after a change, find an intermittent log line, or inspect what a background command has been doing. Read-only investigation: list runs, tail, slice by time or marker, search with ripgrep, follow live output.
metadata:
  tags: introspect, debugging, logs, pty, observability, dev-server
---

## What introspect is (for you, the agent)

`introspect` is an **introspection tool for you**. The user runs their own commands under it (`introspect mix phx.server`, etc.), which captures every byte the command writes to its terminal into `~/.introspect/<id>/log`, with timestamps and named markers. From any other shell — including yours — you can **query that log** while the process keeps running.

Your job with this skill is to **read**, not to run. Use it to answer the user's questions about what their processes have been doing: find errors, bracket events in time, tail live output, search across runs, etc.

## Responsibility split

**The user attaches commands.** They decide what to run under `introspect` and when. You should not launch long-lived processes yourself via `introspect` — that's the user's call (they're the one with the terminal). If no run exists for what you need to investigate, say so and ask them to start one.

**You investigate.** Freely use the read-only query commands:

- `introspect ls` — discover what's running
- `introspect tail ID [N] [-f]` — last N lines, optionally follow
- `introspect get-lines ID N..M` — slice by absolute line numbers
- `introspect since ID SPEC` — lines since a duration / time / marker
- `introspect between ID A B` — lines between two specs
- `introspect search [ID] PATTERN [rg-args...]` — regex search via ripgrep
- `introspect marks ID` / `introspect filter ls ID` — list markers / saved filters
- `introspect path ID` — print the storage directory

**Ask before mutating.** These commands change user state — confirm first:

- `introspect send ID '...'` — injects input into the running child's stdin. Only use when the user has explicitly asked you to drive their REPL/process.
- `introspect mark` / `introspect unmark` — writes to the user's marker set. Prefer asking, unless they've told you to bracket a workflow.
- `introspect filter set` / `filter rm` — persists regex filters per run.
- `introspect clear` / `introspect rm` — destructive. Never do this without explicit instruction.

## First move on any investigation

```bash
introspect ls
```

This lists every known run with status (`running` / `exited`), line count, and the command. Pick the id that matches what the user is asking about. Ids are stable across sessions — remember the one you used if the conversation continues.

If `ls` is empty or the relevant run isn't there, the user hasn't attached the process under `introspect`. Tell them, and suggest the command they'd run (e.g. `introspect mix phx.server`) — but let *them* run it.

## Output format

Line-returning commands print `N: <line>` where `N` is the absolute line number in the log. This is useful: if a `search` hit is on line 3154, you can immediately `introspect get-lines ID 3134..3174` to read the surrounding context verbatim. Don't lose those numbers.

Common flags on query commands:

- `--raw` — keep ANSI escapes (default: stripped, which is almost always what you want).
- `--filter NAME` — apply a named regex filter the user has saved for this id.
- `--grep REGEX` — ad-hoc regex on `get-lines`.

## Rule files (load the one that matches the task)

- [rules/discovery.md](rules/discovery.md) — `ls`, ids, status, picking the right run.
- [rules/time-queries.md](rules/time-queries.md) — `since` / `between` with durations (`5m`, `2h`), absolute times (`09:00`), and marker names.
- [rules/searching.md](rules/searching.md) — `search` (ripgrep passthrough), combining with line-range re-reads for context.
- [rules/tailing.md](rules/tailing.md) — `tail`, follow mode, when to use it vs. slice queries.
- [rules/line-ranges.md](rules/line-ranges.md) — `get-lines` and the `100..500` / `100_500` / `100 500` forms; using absolute line numbers from search hits.
- [rules/markers-and-filters.md](rules/markers-and-filters.md) — reading `marks` / saved filters; when to *suggest* the user create one.
- [rules/driving-processes.md](rules/driving-processes.md) — `send` (only when explicitly asked). Works while the child is `running`; writes to its pty.
- [rules/storage-layout.md](rules/storage-layout.md) — what's in `~/.introspect/<id>/` if you need to peek directly.

## Non-goals (don't reach for introspect for these)

- **Not a supervisor.** It doesn't restart the child.
- **No structured-log parsing.** Everything is byte-level; use `search` or named filters for "level" semantics.
- **No live multi-terminal view.** `tail -f` on the log is near-live, but you're not sharing the user's terminal.
- **No rotation.** Logs grow until the user runs `clear` / `rm`.
