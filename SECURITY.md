# Security

## Supported Versions

`introspect` is pre-1.0. Security fixes target the latest public source release.

## Reporting a Vulnerability

Please report security issues privately through GitHub security advisories if available, or by opening a minimal public issue that asks for a private contact path without disclosing exploit details.

## Notes

`introspect` stores command output under `~/.introspect/<id>/`. Treat those logs as sensitive if the wrapped process prints tokens, credentials, private paths, or customer data.
