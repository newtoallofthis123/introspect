# Line ranges

`get-lines` is the "give me exactly these lines" primitive. Pair it with any other query to expand context around a hit.

```bash
introspect get-lines ID N M         # inclusive range, space-separated
introspect get-lines ID N..M        # inclusive range, `..` form
introspect get-lines ID N_M         # inclusive range, `_` form (single token — shell-friendly)
introspect get-lines ID N           # single line
```

All three range forms are equivalent. Pick whichever composes cleanly with the shell / variables you're using.

## The absolute-line-number trick

Every line-returning command prefixes output with `N: `, where `N` is the line's absolute position in the log. These numbers are **stable** (lines are append-only; the log doesn't reshuffle), so:

```bash
# Search says line 8421 is the panic.
introspect search api 'panic:' -C 1

# Pull 50 lines of context around it.
introspect get-lines api 8371..8471
```

This is how you turn a search hit into a real investigation — always expand.

## Combining with filters

```bash
introspect get-lines api 8000..9000 --filter error
introspect get-lines api 8000..9000 --grep 'took \d{4,}ms'
```

`--filter` uses a saved named regex; `--grep` is ad-hoc. Both apply *after* slicing, so the output is "lines in this range that also match the pattern".

## Total line count

Not a dedicated command; `introspect ls` shows it in the `NNNL` column. Or:

```bash
introspect tail ID 1        # prints one line + the absolute number
```
