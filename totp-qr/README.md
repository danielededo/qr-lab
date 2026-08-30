# totp-qr

Generate a QR code that enrolls an account in an authenticator app (Google
Authenticator, Aegis, 1Password, ...), and verify the resulting 6-digit codes
with a from-scratch implementation of RFC 6238 — no TOTP library, that's the
point.

## Setup

```sh
cd totp-qr
pip install -r requirements.txt   # segno only; verify.py is stdlib-only
```

## Generate

```sh
python generate.py --label "alice@example.com" --issuer qr-lab
```

Expected output (the secret is random every run):

```
URI:    otpauth://totp/alice%40example.com?secret=JBSWY3DPEHPK3PXP...&issuer=qr-lab&algorithm=SHA1&digits=6&period=30
Secret: JBSWY3DPEHPK3PXP...
Saved QR code to totp-qr.png
Scan the QR with an authenticator app, or enter the secret manually;
then cross-check with: python verify.py watch JBSWY3DPEHPK3PXP...
```

Scan `totp-qr.png` with any authenticator app; the printed secret is the same
value for manual entry.

## Verify

Check a code you read from the authenticator app:

```sh
python verify.py verify <secret> 123456
# prints VALID (exit 0) or INVALID (exit 1)
```

Print the code that is valid right now, or watch codes roll over every 30
seconds and compare them against the app that scanned the QR:

```sh
python verify.py current <secret>
python verify.py watch <secret>
```

`verify` and `current` also take `--at <unix-timestamp>` to compute against a
fixed moment — useful for deterministic tests, e.g. the RFC 6238 test vector:
secret `GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ` (base32 of `12345678901234567890`)
at time `59` yields code `287082`.

## How TOTP works

TOTP is two small RFCs stacked:

1. **HOTP (RFC 4226)** turns a shared secret and a counter into a short code:
   compute `HMAC-SHA1(secret, counter)` (counter as 8 big-endian bytes), let
   the digest's last nibble pick an offset, read 4 bytes there ("dynamic
   truncation"), clear the top bit, and keep the low 6 decimal digits.
2. **TOTP (RFC 6238)** replaces the counter with time: `counter =
   unix_time // 30`. Both sides derive the same counter from their clocks, so
   the same code appears on both — no communication needed after sharing the
   secret. Verifiers accept ±1 step to absorb clock drift and typing time.

Everything therefore rests on the shared secret: whoever has it can mint valid
codes forever.

## Secret hygiene

The base32 secret is the credential — treat it like a password. Don't commit
real secrets (or QR images encoding them) to git; generated images are
git-ignored here on purpose, and `generate.py` always creates a fresh random
secret rather than accepting one, so nothing in this repo is ever a live
credential.
