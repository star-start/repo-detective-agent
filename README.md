# 🕵️ Repo Detective Agent

A zero-API-key Python agent that investigates a codebase, reasons about the clues it finds,
and produces a prioritized action report.

It is intentionally deterministic and safe: the detective only reads your project and never
changes the repository it investigates.

## What makes it an agent?

The project follows a small but real agent loop:

1. **Observe** — discover files, detect the technology stack, and run focused inspection tools.
2. **Reason** — classify findings by severity and calculate a repository health score.
3. **Act** — turn the evidence into a prioritized remediation plan and report.

## Clues it can find

- hard-coded API keys, access tokens, passwords, and secrets
- `TODO`, `FIXME`, `HACK`, and `XXX` work markers
- missing tests
- missing README, license, or `.gitignore`
- files larger than 1 MB that may not belong in Git
- Python, JavaScript/TypeScript, Rust, Go, Swift, and Docker stack signals

## Quick start

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone git@github.com:star-start/repo-detective-agent.git
cd repo-detective-agent
uv sync --dev --no-editable
uv run repo-detective .
```

Scan another repository and save a report:

```bash
uv run repo-detective ~/Documents/my-project --output detective-report.md
```

Generate JSON for another tool or CI pipeline:

```bash
uv run repo-detective . --json --output report.json
```

## Example output

```text
# Repo Detective Report

Health score: 58/100
Files scanned: 24
Detected stack: Python, Docker

Findings
- CRITICAL possible-secret at app/config.py:8 — Possible hard-coded api_key
- HIGH testing at project — Source code exists, but no test files were detected
- LOW work-marker at app/main.py:17 — TODO: add retry handling
```

## Development

```bash
uv sync --dev --no-editable
uv run ruff check .
uv run pytest
```

CI runs both checks on every push and pull request.

## License

MIT
