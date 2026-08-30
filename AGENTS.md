# qr-lab

A learning-focused Python monorepo that explores QR code technology (encoding,
decoding, error correction) through two standalone subprojects: `wifi-qr`
(WiFi credential QR codes) and `totp-qr` (TOTP/2FA setup QR codes with a
from-scratch RFC 6238 implementation). Optimized for clarity and hands-on
understanding, not production use. Python 3.11+.

This file is the single source of truth for agent instructions, as prescribed
by [docs/AI-AGENTS.md](docs/AI-AGENTS.md); `CLAUDE.md` is a pointer to it.

## Commands

- Setup: `pip install -r wifi-qr/requirements.txt -r totp-qr/requirements.txt`
- Lint: `ruff check .`
- Smoke test (no test framework — round-trip the real scripts):
  - `python wifi-qr/generate.py --ssid "Test Net" --password 'p@ss;word' --auth WPA --output /tmp/wifi.png`
  - `python wifi-qr/decode.py /tmp/wifi.png` (must print back the same credentials)
  - `python totp-qr/generate.py --label demo --output /tmp/totp.png` (prints a secret)
  - `python totp-qr/verify.py current <secret>` then `python totp-qr/verify.py verify <secret> <code>`

## Conventions

- Commits: Conventional Commits — see [docs/COMMIT-CONVENTION.md](docs/COMMIT-CONVENTION.md).
- Branching: trunk-based — see [docs/BRANCHING-STRATEGY.md](docs/BRANCHING-STRATEGY.md)
  and [ADR 0001](docs/adr/0001-trunk-based-development.md).
- All code, comments, and docs are written in English, no exceptions.
- Prefer small, readable scripts over frameworks or abstraction layers — this
  repo is meant to be read and understood, not just executed.
- Each subproject stays runnable standalone (own `requirements.txt` and
  `README.md`); shared code goes in `common/` only when genuinely reused by both.

## Layout

- `wifi-qr/` — generate/decode WiFi credential QR codes (`WIFI:` payload format)
- `totp-qr/` — generate TOTP setup QR codes (`otpauth://` URIs) and verify codes
- `common/` — QR helpers shared by both subprojects
- `docs/` — repo-level conventions and ADRs

## Boundaries

- Never commit directly to `main`; every change goes through a pull request.
- Never commit real WiFi credentials, TOTP secrets, or generated QR images that
  encode them — outputs are git-ignored on purpose.
- `LICENSE` is a canonical third-party text: never reword it.
- No web UI, API, database, or production security hardening — out of scope by
  design; keep it CLI-only.
- When adding, renaming, or removing files, update the structure tree in
  `README.md` in the same pull request.
