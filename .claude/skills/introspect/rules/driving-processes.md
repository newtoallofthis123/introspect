# Driving processes with `send` (rare, and only when asked)

`introspect send` writes to the child's stdin via its pty. It's how the user (or you, on their behalf) drives a REPL / interactive process from outside its terminal.

```bash
introspect send ID 'text'        # appends \n (like pressing Enter)
introspect send ID 'text' --raw  # no trailing newline
```

## Ground rules

- **Only when explicitly asked.** `send` mutates the user's live process. It's not a read-only query. Don't use it to "try things" on your own initiative.
- **Only works while the run is `running`.** Check `introspect ls` first. For `exited` runs, `send` silently fails / errors.
- **Only useful if the child reads stdin.** An IEx/pry/python REPL reads stdin; a daemonized server usually doesn't. If the user asks you to `send` to something that ignores stdin, the input will go into the void.
- **Echo round-trip.** After `send`, query the log (`tail`, `since 5s`) to see what the REPL printed in response.

## Typical pattern

```bash
# User has: introspect --id iex -- iex -S mix
introspect send iex 'MyApp.Repo.all(User) |> length()'
introspect since iex 3s
```

## Multi-line / readline

`send` just writes bytes. Multiline input works if the REPL's parser accepts it; otherwise send line by line. Use `--raw` when you need to send control sequences or avoid the implicit newline (e.g. sending `^C` would be `send ID $'\x03' --raw`, though you rarely want this).

## What not to do

- Don't `send` commands that alter external systems (DB writes, API calls) unless the user has green-lit that specific command.
- Don't `send` to processes other than REPLs without thinking through what stdin means to them — e.g. writing random text to a TUI like `vim` can scramble the user's session.
