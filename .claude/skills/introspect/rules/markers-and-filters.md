# Markers and named filters

Both live per-id. Both are **user state**. You mostly *read* them; you *create* them only when asked.

## Reading

```bash
introspect marks ID        # list markers: name, line, timestamp, optional note
introspect filter ls ID    # list saved filters: name → regex
```

Use marks as spec inputs to `since` / `between` (see [time-queries.md](time-queries.md)):
```bash
introspect since api deploy
introspect between api before-fix after-fix
```

Use named filters with any query command:
```bash
introspect tail api -f --filter error
introspect since api 1h --filter slow
```

## When to *suggest* creating one (vs. doing it yourself)

Default: suggest, let the user decide. Markers and filters are notes the user writes about their own process — persisting your guess of what "error" means for their app crosses into opinion.

Exceptions where you can create them directly:

- The user explicitly says "mark this" / "bookmark here" / "save a filter for X".
- You're mid-workflow that the user has scoped as "bracket this change" — creating `before-X` / `after-X` markers is the mechanism they asked for.

Otherwise, say something like:

> "If you want to come back to this moment later, run `introspect mark api baseline -m 'before refactor'`."
> "You'll probably grep this pattern again — consider `introspect filter set api slow 'took \d{4,}ms'`."

## Creating (when appropriate)

```bash
introspect mark ID NAME [-m "note"]          # drops at current end of log
introspect unmark ID NAME

introspect filter set ID NAME 'REGEX'        # regex is a Python `re` pattern
introspect filter rm  ID NAME
```

Filter regexes are Python `re` syntax (not ripgrep). Keep them simple and anchored to what the user cares about; don't over-engineer.
