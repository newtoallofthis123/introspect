# Searching

`introspect search` shells out to `ripgrep` against the (ANSI-stripped) log.

```bash
introspect search ID PATTERN [rg-args...]
introspect search PATTERN [rg-args...]          # no id → searches every run
```

Any `rg` flag passes through: `-C N` (context), `-i` (case-insensitive), `-n` (line numbers — on by default in `rg`), `--multiline`, `-U`, etc.

## Investigation loop

This is the bread-and-butter pattern. Don't stop at the first hit — pull its surroundings.

```bash
# 1. Find candidates.
introspect search api '(ERROR|FATAL|panic)' -C 2

# 2. A hit on line 3154 looks interesting. Pull ±20 lines around it:
introspect get-lines api 3134..3174

# 3. Still need more? Widen:
introspect get-lines api 3050..3200
```

The `N: ` line-number prefix on every output line is the key — carry those numbers into `get-lines` for deterministic context expansion.

## Scoping to a time window

`search` doesn't take a spec directly. Compose:

```bash
# Errors in the last hour only:
introspect since api 1h | rg -C2 -i error

# Between two markers:
introspect between api before-fix after-fix | rg -n panic
```

When piped, you lose the `search`-command's own output formatting but `rg` gives you its own `file:line:match` output (well, just `line:match` here because stdin has no filename).

## Cross-run search

When you don't know which run the event is in, drop the id:

```bash
introspect search 'ECONNREFUSED' -C 1
```

Good for "which of my services logged this?" questions. Reads every run in `~/.introspect/`.

## Regex tips

- Pass patterns in single quotes to keep your shell from eating `\b`, `$`, etc.
- `rg` uses Rust regex syntax — most things work, but no lookaround. Use `rg -P` (PCRE2) if you really need lookbehind.
- Very noisy pattern? The user may already have a saved named filter — check with `introspect filter ls ID` first (see [markers-and-filters.md](markers-and-filters.md)).
