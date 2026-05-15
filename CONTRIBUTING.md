# Contributing

Thanks for helping improve `introspect`.

## Setup

```bash
uv sync
uv run introspect --help
uv run python -m unittest
```

The lockfile is committed so contributors and CI use the same dependency set.

## Scope

`introspect` is intentionally small: run a command under a pty, capture its output, and query it later. Before opening a large feature PR, open an issue so the design can be discussed first.

Good changes include:

- Bug fixes with focused tests.
- Better CLI errors.
- Small query or filtering improvements.
- Documentation that makes existing behavior clearer.

Avoid changes that turn `introspect` into a supervisor, log rotation system, or framework-specific log parser.

## Tests

Use the standard library test runner:

```bash
uv run python -m unittest
```

Integration tests that touch ptys should stay small and deterministic. The current implementation targets macOS and Linux.
