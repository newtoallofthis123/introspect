# Discovering runs

Always start here. `ls` is cheap and answers "what does the user have attached right now?".

```bash
introspect ls
# mix-a3f2   running   4821L   mix phx.server
# build-91x  exited      132L   cargo build --release
# iex        running    1204L   iex -S mix
```

Columns: **id**, **status** (`running` / `exited`), **line count** (`NNNL`), **command**.

## Picking the right id

- Match against the **command column**, not just the id prefix — the id is auto-generated from the first argv token (`mix-a3f2` for `mix …`), but the full cmd disambiguates.
- `running` means the child is still alive; `send` works, new lines will keep arriving.
- `exited` means the process is done; the log is frozen. `since`, `between`, `search`, `get-lines` all still work.

## If `ls` is empty or missing the process

The user hasn't started the process under `introspect`. Do **not** start it yourself. Tell the user what you'd like them to run, e.g.:

> "I can't see any capture for your dev server. If you restart it as `introspect mix phx.server` in its terminal, I'll be able to query its output from here."

## Remembering ids

Ids are stable across sessions — they persist until the user `rm`s them. If an investigation spans multiple turns, keep using the same id rather than re-running `ls` every turn (but do re-check if the conversation is about "what's it doing *now*").

## Inspecting the storage directly

```bash
introspect path mix-a3f2
# /Users/.../.introspect/mix-a3f2
```

Useful when you want to `Read` the raw log, `marks.jsonl`, or `meta.json` with your file tools rather than going through the CLI. Prefer the CLI for queries; reach for the raw files only if the CLI can't express what you need.
