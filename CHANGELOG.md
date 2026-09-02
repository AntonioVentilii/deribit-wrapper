# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.5](https://github.com/AntonioVentilii/deribit-wrapper/compare/v0.6.4...v0.6.5) (2026-09-02)


### Miscellaneous Chores

* **deps:** bump googleapis/release-please-action from 4.4.0 to 5.0.0 ([#117](https://github.com/AntonioVentilii/deribit-wrapper/issues/117)) ([e260cfd](https://github.com/AntonioVentilii/deribit-wrapper/commit/e260cfd1163b97cd87a9638ad3024cb8b06e5ed5))

## [0.6.4](https://github.com/AntonioVentilii/deribit-wrapper/compare/v0.6.3...v0.6.4) (2026-08-28)


### Continuous Integration

* reject PR titles release-please would silently ignore ([#112](https://github.com/AntonioVentilii/deribit-wrapper/issues/112)) ([a75a8d3](https://github.com/AntonioVentilii/deribit-wrapper/commit/a75a8d3c73de9e60b02a44e302547636a2531e7a))

## [0.6.3](https://github.com/AntonioVentilii/deribit-wrapper/compare/v0.6.2...v0.6.3) (2026-08-28)


### Bug Fixes

* harden the asymmetric signature path ([#107](https://github.com/AntonioVentilii/deribit-wrapper/issues/107)) ([f7ebf5d](https://github.com/AntonioVentilii/deribit-wrapper/commit/f7ebf5d2f8e1845583bb4d65bae0800a69a5475d))
* send a timeout with every HTTP request ([#106](https://github.com/AntonioVentilii/deribit-wrapper/issues/106)) ([b4243bd](https://github.com/AntonioVentilii/deribit-wrapper/commit/b4243bddd70ad08c2581ddc216826b1d09f63493))


### Code Refactoring

* log through a named logger instead of printing ([#108](https://github.com/AntonioVentilii/deribit-wrapper/issues/108)) ([c2d07f3](https://github.com/AntonioVentilii/deribit-wrapper/commit/c2d07f356432b88f28dc0854a7f005f6d9b64217))


### Continuous Integration

* type-check with mypy and fix the annotations it caught ([#109](https://github.com/AntonioVentilii/deribit-wrapper/issues/109)) ([2d22038](https://github.com/AntonioVentilii/deribit-wrapper/commit/2d22038f7f04076818bbb044c8f1e853b37468d9))

## [0.6.2](https://github.com/AntonioVentilii/deribit-wrapper/compare/v0.6.1...v0.6.2) (2026-08-28)


### Features

* ship py.typed so consumers get the type hints ([#97](https://github.com/AntonioVentilii/deribit-wrapper/issues/97)) ([6573f2a](https://github.com/AntonioVentilii/deribit-wrapper/commit/6573f2a363f08f89db31a644fda13a16b1f1d86f))


### Bug Fixes

* bound the temporarily-unavailable retry loop ([#101](https://github.com/AntonioVentilii/deribit-wrapper/issues/101)) ([c616df2](https://github.com/AntonioVentilii/deribit-wrapper/commit/c616df23af999cc9d161bbb876dc8595f329bbf5))
* raise a clear error when an API key id is not found ([#103](https://github.com/AntonioVentilii/deribit-wrapper/issues/103)) ([1682641](https://github.com/AntonioVentilii/deribit-wrapper/commit/168264188bb557ae10db1a31c20cd973ab2a172d))
* simulated cancel/close make no request and match live shapes ([#104](https://github.com/AntonioVentilii/deribit-wrapper/issues/104)) ([e12add6](https://github.com/AntonioVentilii/deribit-wrapper/commit/e12add6d9896b505c9c19bc51a13d81d3292c50b))
* simulated mode also suppresses close_position and cancel_orders ([#100](https://github.com/AntonioVentilii/deribit-wrapper/issues/100)) ([232bfb4](https://github.com/AntonioVentilii/deribit-wrapper/commit/232bfb4ec10a5852c29ecb5a37774813cea5dbba))


### Performance Improvements

* concatenate DataFrames once instead of per iteration ([#102](https://github.com/AntonioVentilii/deribit-wrapper/issues/102)) ([bf0d07b](https://github.com/AntonioVentilii/deribit-wrapper/commit/bf0d07b2ec13af325364c3431ffd4f7510b88e26))


### Documentation

* correct the simulated flag description in the README ([#98](https://github.com/AntonioVentilii/deribit-wrapper/issues/98)) ([fee7483](https://github.com/AntonioVentilii/deribit-wrapper/commit/fee74830ca9dc7faad5c79887a939a4c608b7551))
* simulated mode now covers close_position and cancel_orders ([#105](https://github.com/AntonioVentilii/deribit-wrapper/issues/105)) ([33b207c](https://github.com/AntonioVentilii/deribit-wrapper/commit/33b207c52623be026daa678249cab5ef731368df))

## [0.6.1](https://github.com/AntonioVentilii/deribit-wrapper/compare/v0.6.0...v0.6.1) (2026-08-28)


### Bug Fixes

* tag releases as vX.Y.Z, not deribit_wrapper-vX.Y.Z ([#94](https://github.com/AntonioVentilii/deribit-wrapper/issues/94)) ([80e6ef4](https://github.com/AntonioVentilii/deribit-wrapper/commit/80e6ef4b0836c3fcda7f241e5642fcf966929175))
* use pre-1.0 version bumping for releases ([#96](https://github.com/AntonioVentilii/deribit-wrapper/issues/96)) ([da12cb5](https://github.com/AntonioVentilii/deribit-wrapper/commit/da12cb59f8fe84ebd653524ca9c79ce4744040d9))


### Documentation

* add docstrings to account_management and trading ([#88](https://github.com/AntonioVentilii/deribit-wrapper/issues/88)) ([e99e772](https://github.com/AntonioVentilii/deribit-wrapper/commit/e99e7728b9dbe014efa0f71caaa4235e6a2d01af))
* add docstrings to authentication ([#86](https://github.com/AntonioVentilii/deribit-wrapper/issues/86)) ([0c4e6bc](https://github.com/AntonioVentilii/deribit-wrapper/commit/0c4e6bc0cbd72f9d8cb0f9f834e3a6f9de48e036))
* add docstrings to core modules ([#85](https://github.com/AntonioVentilii/deribit-wrapper/issues/85)) ([cd240e9](https://github.com/AntonioVentilii/deribit-wrapper/commit/cd240e976526cf17d47be6494905738ba8ec503f))
* add docstrings to market_data ([#87](https://github.com/AntonioVentilii/deribit-wrapper/issues/87)) ([66fe509](https://github.com/AntonioVentilii/deribit-wrapper/commit/66fe509db9630f85dd92325a39e66d59cff1a322))


### Continuous Integration

* enforce full docstring coverage ([#89](https://github.com/AntonioVentilii/deribit-wrapper/issues/89)) ([6aeed6e](https://github.com/AntonioVentilii/deribit-wrapper/commit/6aeed6efcf391932445091164b3d9fb1a60d9824))

## [0.6.0](https://github.com/AntonioVentilii/deribit-wrapper/compare/v0.5.0...v0.6.0) (2026-08-28)

### Fixed

- `from_dt_to_ts` interprets naive datetimes as UTC, so timestamps no longer
  depend on the host timezone.
- `get_market_book(currency=...)` actually fetches data instead of returning
  `None`; passing neither or both selectors now raises.
- The invalid-token recovery path retries token acquisition as intended.
- The `env` setter validates its input and no longer blocks for 10 seconds.
- The package no longer imports from `dev_scripts`, which is also no longer
  shipped in the wheel.

### Changed

- Packaging migrated from `setup.py` to `pyproject.toml`; releases build with
  `python -m build`.
- The HTTP session is created once per client and reused, adding an explicit
  `close()`.
- Requirements files match the declared runtime dependencies.

### Added

- Unit tests for `utilities`, `market_data`, `trading`, and
  `account_management`, plus coverage reporting in CI.
- CI gates that actually fail: formatting, docstring style, and Python 3.10 in
  the test matrix.
- `CONTRIBUTING.md` and automated releases via release-please.

## [0.5.0] - 2026-05-29

### Added

- Signature-based authentication (`client_signature` grant): HMAC via client
  secret and asymmetric signing with Ed25519/RSA/EC private keys (#60).
- `cancel_by_label` endpoint integration (#40).
- `cancel_all_by_kind_or_type` endpoint integration (#42).

### Fixed

- `cancel_orders` raises an error on bad values instead of failing silently (#41).

## [0.4.2] - 2025-09-10

### Added

- `get_open_orders` endpoint integration (#34).

## [0.4.1] - 2025-09-10

### Added

- `close_position` endpoint integration (#32).

## [0.4.0] - 2025-01-26

### Added

- Custom exception hierarchy (`RequestError`, `SubaccountError`,
  `PriceUnavailableError`, ...) (#7).
- Full static-checks CI pipeline (#8).

### Changed

- Minimum supported Python raised to 3.10 (#10).

## [0.3.3] - 2024-04-13

### Fixed

- `name_instrument` handles float strikes.

## [0.3.0] - 2024-04-05

### Added

- API key management and subaccount management methods in `AccountManagement`.

### Fixed

- Error handling for temporarily-unavailable service (13028) with bounded
  retries.
- Empty trade history no longer fails when accessing the `id` column.

## [0.2.0] - 2024-04-02

### Added

- First structured release of the wrapper: market data, account management,
  and trading layers on top of the authenticated JSON-RPC client.

[0.6.0]: https://github.com/AntonioVentilii/deribit-wrapper/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/AntonioVentilii/deribit-wrapper/compare/v0.4.2...v0.5.0
[0.4.2]: https://github.com/AntonioVentilii/deribit-wrapper/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/AntonioVentilii/deribit-wrapper/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/AntonioVentilii/deribit-wrapper/compare/v0.3.3...v0.4.0
[0.3.3]: https://github.com/AntonioVentilii/deribit-wrapper/compare/v0.3.0...v0.3.3
[0.3.0]: https://github.com/AntonioVentilii/deribit-wrapper/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/AntonioVentilii/deribit-wrapper/releases/tag/v0.2.0
