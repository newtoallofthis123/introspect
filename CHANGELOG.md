# Changelog

## Unreleased

- `introspect shell` — record an interactive shell session ($SHELL under the pty); exit the shell to stop. Refuses to nest inside an existing session.
- Wrapped commands now get `INTROSPECT_ID` in their environment, set to the run's id.

## 0.1.0

- Initial source-only public release.
- Run commands under a pty and capture output.
- Query captured logs by line range, tail, time window, marker, named filter, or ripgrep search.
- Send input to running processes over a per-run Unix socket.
