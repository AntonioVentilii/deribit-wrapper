# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0](https://github.com/AntonioVentilii/deribit-wrapper/compare/deribit_wrapper-v0.5.0...deribit_wrapper-v0.6.0) (2026-08-28)


### Features

* add custom exceptions ([#7](https://github.com/AntonioVentilii/deribit-wrapper/issues/7)) ([d06727d](https://github.com/AntonioVentilii/deribit-wrapper/commit/d06727d52cb6666df0deb79ba3a3d59b71948999))
* created custom DeribitClientWarning ([20ec46f](https://github.com/AntonioVentilii/deribit-wrapper/commit/20ec46f2fcf7f0153cd19692afbc3d541bb8c1ac))
* created method for portfolio margin calculation ([29e9c18](https://github.com/AntonioVentilii/deribit-wrapper/commit/29e9c18649be6933fc58ced09d37d74beebd8d01))
* enable Dependabot ([b94c1cb](https://github.com/AntonioVentilii/deribit-wrapper/commit/b94c1cbc8be73324c6916ee41ce4a6299f78b0e5))
* enable Dependabot ([ddf3630](https://github.com/AntonioVentilii/deribit-wrapper/commit/ddf3630d843a42a5261f2161a223420b5b136cf0))
* implement signature-based authentication ([#60](https://github.com/AntonioVentilii/deribit-wrapper/issues/60)) ([87e13ab](https://github.com/AntonioVentilii/deribit-wrapper/commit/87e13abf21d18e9d2a542e810255f5f82b13f5b4))
* include instance name as parameter for the Base class ([7ace524](https://github.com/AntonioVentilii/deribit-wrapper/commit/7ace52417928f6630f6e1ea1012878865b712150))
* included error_handler method ([7348686](https://github.com/AntonioVentilii/deribit-wrapper/commit/7348686912f61debec30e39c190ed10e81e22327))
* included get_margin_model method in class AccountManagement ([a9d55c3](https://github.com/AntonioVentilii/deribit-wrapper/commit/a9d55c3721393c5b09eae871d8d71cd16a5ca1a3))
* included more methods in class AccountManagement about API keys management and subaccounts management ([0e737a9](https://github.com/AntonioVentilii/deribit-wrapper/commit/0e737a9c7133210fe3fc3bdd27914ede340e6fef))
* included separate method to add order data ([1b603c4](https://github.com/AntonioVentilii/deribit-wrapper/commit/1b603c4b07a28e03fea25fa49476ca829b9b6ff3))
* integrate `cancel_all_by_kind_or_type` endpoint ([#42](https://github.com/AntonioVentilii/deribit-wrapper/issues/42)) ([7c7c664](https://github.com/AntonioVentilii/deribit-wrapper/commit/7c7c664db474ed6faef63ecce9947c7816622241))
* integrate `cancel_by_label` endpoint ([#40](https://github.com/AntonioVentilii/deribit-wrapper/issues/40)) ([60f1192](https://github.com/AntonioVentilii/deribit-wrapper/commit/60f1192873d32b6cb048665c556ac3ac5014df63))
* integrate `close_position` endpoint ([#32](https://github.com/AntonioVentilii/deribit-wrapper/issues/32)) ([c731b68](https://github.com/AntonioVentilii/deribit-wrapper/commit/c731b68dc91cbf8b8bc54e651b13dcd1ecc68861))
* integrate get_open_orders endpoint ([#34](https://github.com/AntonioVentilii/deribit-wrapper/issues/34)) ([e2828c3](https://github.com/AntonioVentilii/deribit-wrapper/commit/e2828c37cabc6d762f54022464cf871d22705054))
* modified the Authentication class to use the same token until it expires and request a new one via the refresh_token ([97a53f8](https://github.com/AntonioVentilii/deribit-wrapper/commit/97a53f8b6adcbee71e965f351192482db3d94536))


### Bug Fixes

* env setter no longer blocks for 10 seconds ([#80](https://github.com/AntonioVentilii/deribit-wrapper/issues/80)) ([315a7cb](https://github.com/AntonioVentilii/deribit-wrapper/commit/315a7cb6d2e99d92b7c00f446861aa7854724219))
* handling error 13028 (temporarily unavailable) ([bdcb6f9](https://github.com/AntonioVentilii/deribit-wrapper/commit/bdcb6f9e83733db2a91d5eb1d8806c165d05619b))
* implement get_market_book by-currency branch ([#84](https://github.com/AntonioVentilii/deribit-wrapper/issues/84)) ([1156922](https://github.com/AntonioVentilii/deribit-wrapper/commit/1156922a9985b8f61d6090bad08cf28b98066eb9))
* interpret naive datetimes as UTC in from_dt_to_ts ([#83](https://github.com/AntonioVentilii/deribit-wrapper/issues/83)) ([3dd9714](https://github.com/AntonioVentilii/deribit-wrapper/commit/3dd97140f969e4a710d3c5faa22e08ecfa9a8928))
* make the invalid-token retry loop actually retry ([#82](https://github.com/AntonioVentilii/deribit-wrapper/issues/82)) ([b990d1d](https://github.com/AntonioVentilii/deribit-wrapper/commit/b990d1d3405608e2d9b99a85b5e6226ef311f7f5))
* method last_price will try to get the values and raise the error afterwards ([b2f1642](https://github.com/AntonioVentilii/deribit-wrapper/commit/b2f1642983eeb6a92d49c1fee90df9dcacb59758))
* method name_instruments considers float strikes now ([44c1435](https://github.com/AntonioVentilii/deribit-wrapper/commit/44c1435cd29fda9c561d25366c04e9145cf1cee2))
* method name_instruments considers float strikes now ([38eb305](https://github.com/AntonioVentilii/deribit-wrapper/commit/38eb3053860392b27fd2520b561d82ab34d67e7c))
* method name_instruments considers float strikes now ([c13b006](https://github.com/AntonioVentilii/deribit-wrapper/commit/c13b0066786a8cbc47d4be8ed5eee24617ca71a0))
* Raise error for bad value on cancel_orders ([#41](https://github.com/AntonioVentilii/deribit-wrapper/issues/41)) ([d075d21](https://github.com/AntonioVentilii/deribit-wrapper/commit/d075d21da07048b343f74a423a4ae5894796cdee))
* raising Exception when service is unavailable after 1 hour of attempts ([0359bc4](https://github.com/AntonioVentilii/deribit-wrapper/commit/0359bc485ec8570af6f9702e7e859f9207837d1a))
* remove append and use concat ([82a432d](https://github.com/AntonioVentilii/deribit-wrapper/commit/82a432d2c1f4cb3fef592d193641d75217817457))
* remove append and use concat ([9048610](https://github.com/AntonioVentilii/deribit-wrapper/commit/904861004272febdea84c8104f699f8d49fc6368))
* remove invalid job-level if from the release workflow ([#92](https://github.com/AntonioVentilii/deribit-wrapper/issues/92)) ([8dc0173](https://github.com/AntonioVentilii/deribit-wrapper/commit/8dc0173ee942dc4e578344deb9486522f11c85c1))
* remove package dependency on dev_scripts ([#70](https://github.com/AntonioVentilii/deribit-wrapper/issues/70)) ([fad10f2](https://github.com/AntonioVentilii/deribit-wrapper/commit/fad10f20e69ba5fc58ac2cf5a2cc3ef94eb80766))
* removed direct request in get_currencies method, now it will use the _request internal method ([3a23eef](https://github.com/AntonioVentilii/deribit-wrapper/commit/3a23eef6e34dd91a5d11b80806ada2e0598f2e8b))
* small bug when calling caloum 'id' for empty trade history ([16cd376](https://github.com/AntonioVentilii/deribit-wrapper/commit/16cd376376a93bc380abef1fc6e9b9d44d636f9a))
* tests were outdated ([a5e87f5](https://github.com/AntonioVentilii/deribit-wrapper/commit/a5e87f5e8b8bc5a04539afdeaf515ad7ed678fda))
* tests were outdated ([63d32a0](https://github.com/AntonioVentilii/deribit-wrapper/commit/63d32a078fbba11a91b9108830d19ad9fd89796b))
* unbreak the release-please workflow ([#91](https://github.com/AntonioVentilii/deribit-wrapper/issues/91)) ([a018824](https://github.com/AntonioVentilii/deribit-wrapper/commit/a018824858539ec3cdde1e4638638a0362af7583))


### Performance Improvements

* reuse the HTTP session across requests ([#81](https://github.com/AntonioVentilii/deribit-wrapper/issues/81)) ([51f8d32](https://github.com/AntonioVentilii/deribit-wrapper/commit/51f8d32c1a1b0e84594fceda4a902981e5b55346))


### Documentation

* add CHANGELOG and CONTRIBUTING ([#79](https://github.com/AntonioVentilii/deribit-wrapper/issues/79)) ([acb5f12](https://github.com/AntonioVentilii/deribit-wrapper/commit/acb5f1254068e7f0125e47334ef99e16f355c7a8))

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
