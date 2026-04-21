# Time-based queries

`since` and `between` are the fastest way to scope an investigation to "what happened around the event the user cares about".

```bash
introspect since ID SPEC
introspect between ID SPEC_A SPEC_B
```

## Spec forms

All three spec forms are interchangeable — `since`, `between`, and their args mix freely.

| Form | Example | Meaning |
|---|---|---|
| Duration | `5m`, `90s`, `2h` | Relative to now. |
| Absolute time | `09:00`, `14:30:05` | Wall-clock today. |
| Marker name | `before-deploy` | The line where that marker was dropped. |

Backed by a fixed-width timestamp sidecar (`ts.log`) — `since 2h` is an O(log N) binary search even on huge logs, so don't hesitate to use it.

## Common patterns

**"What happened in the last 5 minutes?"**
```bash
introspect since api 5m
```

**"What happened between when the user deployed and now?"**
```bash
introspect since api deploy
```

**"Between these two events."** Mix any spec forms:
```bash
introspect between api 10m now               # last 10 minutes (well, `now` isn't a spec — see below)
introspect between api deploy 2m             # from marker `deploy` until 2 minutes ago
introspect between api 09:00 10:00           # a wall-clock window
introspect between api before-fix after-fix  # two markers
```

There's no `now` keyword — use `since X` when the upper bound is "now". For a fixed window ending recently, use a small duration as the upper spec (`between api 10m 0s`).

## Layering filters

Every time query accepts `--filter NAME` (user-saved regex) or you can pipe into `rg` / `grep` for ad-hoc work:

```bash
introspect since api 15m --filter error
introspect between api before-fix after-fix | rg -i 'timeout|refused'
```

## When to pick `since` vs `search`

- **You know roughly *when*** — use `since` / `between`. Deterministic, bounded, chronological.
- **You know roughly *what*** (a string / pattern) but not when — use `search` (see [searching.md](searching.md)), then use the line number from the hit to pull surrounding context with `get-lines`.
- **Both** — `search` within a time window by combining: `introspect between api 1h 0s | rg -C3 panic`.
