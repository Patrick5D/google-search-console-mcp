# Contributing

Start with the source installation in [README.md](README.md), then run:

```sh
.venv/bin/python -m pytest -q
.venv/bin/python tests/smoke_http.py
```

Tests must not require real Google credentials. Use small API fixtures that expose the failure being fixed, and cover tool-level behavior when a protocol changes.

Keep API reads, deterministic analysis, and MCP registration separate. Preserve pagination/provenance metadata. Do not replace missing metrics with zeros, mix Web/Image baselines, or imply a cause that the returned data cannot establish.

Source files have INPUT/OUTPUT/POS contracts. Update the file header and the nearest `CLAUDE.md` map when dependencies, exports, or responsibilities change. Architecture maps are written in Chinese; user-facing setup documentation is in English.

For pull requests, explain the behavior change, validation performed, and any response-schema compatibility impact. Keep patches focused. Do not include tokens, OAuth clients, private properties, logs, snapshots, generated package metadata, or machine-specific configuration.

When reporting a bug, include Python/package versions, the tool name, sanitized arguments, and the error type. Use `example.com` and synthetic metrics instead of sharing private search data. Never paste access tokens, refresh tokens, or credential files into an issue.
