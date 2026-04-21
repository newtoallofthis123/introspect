# Storage layout

Every run lives at `~/.introspect/<id>/`. You usually don't need to peek — the CLI covers the common cases — but knowing the layout helps when you want to read files directly.

```
~/.introspect/<id>/
  log            raw pty bytes (everything the child wrote to the terminal)
  ts.log         fixed-width timestamps, one record per newline in `log`
  marks.jsonl    named markers: {name, line, ts, note?}
  meta.json      {cmd, pid, started_at, exit_status?, filters: {name: regex}}
  ctl.sock       unix socket for `send` (only while the child is running)
```

Get the path:
```bash
introspect path ID
```

## When to read files directly (vs. using the CLI)

Prefer the CLI. Reach for direct file reads only when:

- You want `meta.json` details the CLI doesn't surface (exact pid, start time, exit status).
- You want the full list of filters as JSON rather than the tabular `filter ls` output.
- You're scripting something the CLI doesn't express cleanly.

`log` in particular is a raw pty byte stream — it may contain ANSI escapes, `\r\n`, cursor-move sequences, etc. The CLI's `--raw`-off default strips these; direct reads will not.

## Destructive commands (don't run without explicit instruction)

```bash
introspect clear ID   # truncates log and ts.log (keeps the run, loses history)
introspect rm ID      # deletes the entire directory
```

Both are irreversible. Only run when the user has specifically asked. If they're trying to "reset" something, confirm which.
