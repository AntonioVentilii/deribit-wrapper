# Contributing to deribit-wrapper

Thanks for your interest in contributing! This document explains how to set up
a development environment and what is expected of a pull request.

## Development setup

Requires Python 3.10+.

```bash
git clone https://github.com/AntonioVentilii/deribit-wrapper.git
cd deribit-wrapper
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

## Running the checks

The `Makefile` mirrors what CI runs:

```bash
make format        # auto-format the codebase
make check-format  # verify formatting (what CI runs)
make lint          # pylint on the package
make test          # pytest with coverage
make docs          # docstring style (pydocstyle)
make all           # everything CI gates on
```

All of these must pass before a PR can merge (the `may-merge` CI job enforces
it across Python 3.10–3.13).

## Tests

- Tests live in `tests/` and run with plain `pytest`.
- Unit tests must not hit the network: mock at the `_request` boundary (see
  `tests/test_market_data.py` for the pattern).
- A few authentication tests can exercise the real Deribit **test**
  environment; they are skipped unless `TEST_CLIENT_ID` / `TEST_CLIENT_SECRET`
  are set (via environment or a local `.env`, which is gitignored). Never use
  production credentials.

## Pull requests

- Keep PRs small and focused on one change.
- Use conventional-commit style titles (`feat:`, `fix:`, `chore:`, `ci:`,
  `test:`, `docs:`, `build:`), matching the existing history.
- Add or update tests for behavior you change.
- Update `CHANGELOG.md` under `[Unreleased]` for user-visible changes.

## Releases

Releases are cut by tagging `v<version>` (after bumping the package version);
the publish workflow builds and uploads the package to PyPI automatically.

## Reporting issues

Use the [issue tracker](https://github.com/AntonioVentilii/deribit-wrapper/issues).
Include the library version, Python version, and a minimal reproduction —
never include real API credentials in an issue.
