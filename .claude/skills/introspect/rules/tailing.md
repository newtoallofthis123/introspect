# Tailing

```bash
introspect tail ID [N]        # last N lines (default 20)
introspect tail ID [N] -f     # follow: stream new lines as they arrive
introspect tail ID --filter NAME
```

## When to use `tail` vs. a slice query

- **`tail ID`** — quick "what's the current state at the end of the log?" peek. Use it as a sanity check before diving deeper.
- **`tail ID -f`** — live streaming. Useful when the user asks you to *watch* for a specific event (a request, a log line, an error during a reproduction). Combine with `--filter` to cut noise.
- **`since` / `between`** (see [time-queries.md](time-queries.md)) — for anything retrospective. Deterministic and bounded; doesn't hang.

## Follow mode caveats

`tail -f` blocks until you stop it. Agent-wise, this means:

- **Don't** run `tail -f` without a filter or a clear exit plan; you'll wait on a potentially silent stream.
- **Do** prefer a time query (`since 30s`) if you just want "what showed up recently".
- **Do** background it (`run_in_background: true`) when you genuinely need to watch live while doing other work — then read the output stream later.

## Filtered follow

Combining `-f` with a saved filter is the sweet spot for watching a live process for specific events:

```bash
introspect tail api -f --filter error
```

Only lines matching the `error` regex (saved for this id) are printed. Quiet until something happens; noisy when it does.

If no filter is defined yet, list what's available:
```bash
introspect filter ls api
```

and pick the one that matches the user's intent. If the user hasn't saved one, see [markers-and-filters.md](markers-and-filters.md) before saving a new one yourself.
