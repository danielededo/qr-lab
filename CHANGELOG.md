# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
How to use this file:

- Add every user-visible change under "Unreleased", in the appropriate category:
  Added, Changed, Deprecated, Removed, Fixed, Security.
- When releasing, rename "Unreleased" to the new version and date
  (e.g. "[1.2.0] - 2026-08-23"), then start a fresh "Unreleased" section on top.
- Keep entries short, in plain language, written for users — not commit messages.
- Link versions to the corresponding GitHub compare/tag URLs at the bottom.
-->

## [Unreleased]

### Added

- `wifi-qr` subproject: generate and decode WiFi credential QR codes, with
  optional auto-detection of the currently connected network (`--auto`).
- `totp-qr` subproject: generate TOTP/2FA setup QR codes and verify codes with
  a from-scratch RFC 6238 implementation.
- `qr-damage` subproject: an error-correction lab that measures where each
  Reed-Solomon level (L/M/Q/H) actually stops decoding, under scattered and
  contiguous damage.

<!--
## [0.1.0] - YYYY-MM-DD

### Added

- Initial release.
-->

[Unreleased]: https://github.com/danielededo/qr-lab/commits/main
<!-- After the first release, switch to:
[Unreleased]: https://github.com/danielededo/qr-lab/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/danielededo/qr-lab/releases/tag/v0.1.0
-->
