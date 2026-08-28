# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/AntonioVentilii/deribit-wrapper/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/AntonioVentilii/deribit-wrapper/compare/v0.4.2...v0.5.0
[0.4.2]: https://github.com/AntonioVentilii/deribit-wrapper/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/AntonioVentilii/deribit-wrapper/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/AntonioVentilii/deribit-wrapper/compare/v0.3.3...v0.4.0
[0.3.3]: https://github.com/AntonioVentilii/deribit-wrapper/compare/v0.3.0...v0.3.3
[0.3.0]: https://github.com/AntonioVentilii/deribit-wrapper/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/AntonioVentilii/deribit-wrapper/releases/tag/v0.2.0
