# qr-lab

A learning-focused monorepo for exploring QR code technology — encoding,
decoding, and error correction — through two small, concrete, verifiable use
cases. It is meant to be read and understood, not just executed: small scripts,
no frameworks, and the interesting algorithms (payload escaping, RFC 6238
TOTP) implemented by hand instead of imported.

[![CI](https://github.com/danielededo/qr-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/danielededo/qr-lab/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Subprojects

| Subproject | What it demonstrates |
| --- | --- |
| [wifi-qr](wifi-qr/) | Generate and decode WiFi credential QR codes (`WIFI:` payload format, character escaping, OS-specific credential auto-detection) |
| [totp-qr](totp-qr/) | Generate TOTP/2FA enrollment QR codes (`otpauth://` URIs) and verify codes with a from-scratch RFC 6238 implementation |
| [qr-damage](qr-damage/) | Break QR codes on purpose: measure where each Reed-Solomon error-correction level (L/M/Q/H) actually stops decoding |

Shared QR generation helpers live in [common/](common/); each subproject is
otherwise standalone, with its own `requirements.txt` and `README.md`.

## Quick start

```sh
git clone https://github.com/danielededo/qr-lab.git
cd qr-lab/wifi-qr            # or qr-lab/totp-qr
pip install -r requirements.txt
python generate.py --ssid "My Network" --password "hunter2"   # wifi-qr
python decode.py wifi-qr.png
```

Requirements: Python 3.11+. Each subproject's README documents its commands,
expected output, and the underlying format or algorithm.

## Structure

```
qr-lab/
├── wifi-qr/            # WiFi credential QR codes: generate, decode, --auto detection
├── totp-qr/            # TOTP setup QR codes + RFC 6238 verifier (stdlib-only)
├── qr-damage/          # error-correction lab: damage QR codes until they fail
├── common/
│   └── qr_utils.py     # shared payload-to-image helper (segno)
├── docs/               # conventions and ADRs inherited from the scaffold template
└── .github/            # CI (lint + smoke tests), issue/PR templates, Dependabot
```

## Development

```sh
pip install -r wifi-qr/requirements.txt -r totp-qr/requirements.txt -r qr-damage/requirements.txt ruff
ruff check .
```

There is no unit-test framework by design: CI smoke-tests the scripts
end-to-end and pins TOTP correctness to the RFC 6238 test vectors — see
[.github/workflows/ci.yml](.github/workflows/ci.yml). See
[CONTRIBUTING.md](CONTRIBUTING.md) for the contribution workflow and
[docs/COMMIT-CONVENTION.md](docs/COMMIT-CONVENTION.md) for commit messages.

## Status

A hands-on learning repo, not a product: CLI only, no persistence, no
production security hardening. Don't use it as your actual 2FA system.

## License

Distributed under the MIT License — see [LICENSE](LICENSE).
