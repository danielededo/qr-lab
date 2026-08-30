"""TOTP (RFC 6238) implemented from scratch — the point is to see the algorithm.

Only the standard library is used. The stack is two small RFCs:

- HOTP (RFC 4226): code = truncate(HMAC-SHA1(secret, counter)) mod 10^digits,
  where the counter is a big-endian 8-byte integer and "truncate" picks 4 bytes
  from the digest at an offset chosen by the digest's own last nibble
  ("dynamic truncation").
- TOTP (RFC 6238): HOTP where the counter is the number of 30-second steps
  since the Unix epoch. Verifiers accept a small window of neighboring steps
  (±1 here) to absorb clock drift and slow typing.

Usage:
    python verify.py verify  <secret> <code>    # is this code valid right now?
    python verify.py current <secret>           # print the code valid right now
    python verify.py watch   <secret>           # print a fresh code every step
"""

import argparse
import base64
import hashlib
import hmac
import struct
import sys
import time


def decode_secret(secret: str) -> bytes:
    """Decode a base32 secret as authenticator apps accept it: case-insensitive,
    spaces allowed (some sites group the secret in blocks of four), padding
    optional (base64.b32decode insists on it, so we restore it)."""
    normalized = secret.replace(" ", "").upper()
    normalized += "=" * (-len(normalized) % 8)
    try:
        return base64.b32decode(normalized)
    except Exception:
        sys.exit(f"error: {secret!r} is not valid base32")


def hotp(key: bytes, counter: int, digits: int = 6) -> str:
    """RFC 4226: one HMAC-SHA1, then dynamic truncation to a short code."""
    # The counter is hashed as a fixed 8-byte big-endian block.
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    # Dynamic truncation: the last nibble of the digest picks where to read
    # 4 bytes; the top bit is cleared to sidestep signed-integer ambiguity.
    offset = digest[-1] & 0x0F
    (value,) = struct.unpack(">I", digest[offset:offset + 4])
    value &= 0x7FFFFFFF
    # Keep the low `digits` decimal digits, preserving leading zeros.
    return str(value % 10 ** digits).zfill(digits)


def totp(secret: str, at: float | None = None,
         period: int = 30, digits: int = 6) -> str:
    """RFC 6238: HOTP with the counter = Unix time // period."""
    timestamp = time.time() if at is None else at
    return hotp(decode_secret(secret), int(timestamp) // period, digits)


def verify(secret: str, code: str, at: float | None = None,
           period: int = 30, digits: int = 6, tolerance: int = 1) -> bool:
    """Check `code` against the current step and ±`tolerance` neighbors.

    The window absorbs clock drift between the two parties and the time the
    user spends typing. compare_digest keeps the comparison constant-time —
    overkill for a CLI, but it is the habit that matters.
    """
    timestamp = time.time() if at is None else at
    counter = int(timestamp) // period
    key = decode_secret(secret)
    return any(
        hmac.compare_digest(hotp(key, counter + step, digits), code)
        for step in range(-tolerance, tolerance + 1)
    )


def watch(secret: str, period: int = 30, digits: int = 6) -> None:
    """Print the current code every step — hold it next to an authenticator
    app that scanned the generated QR: the codes must match."""
    print("Press Ctrl+C to stop.")
    try:
        while True:
            now = time.time()
            remaining = period - (int(now) % period)
            code = totp(secret, at=now, period=period, digits=digits)
            print(f"{code}  (valid {remaining:2d}s more)")
            time.sleep(remaining)
    except KeyboardInterrupt:
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--period", type=int, default=30,
                        help="time step in seconds (default: 30)")
    parser.add_argument("--digits", type=int, choices=(6, 8), default=6,
                        help="code length (default: 6)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sub = subparsers.add_parser("verify", help="check a code against the secret")
    sub.add_argument("secret")
    sub.add_argument("code")
    sub.add_argument("--at", type=float, default=None,
                     help="Unix timestamp to verify against instead of now "
                          "(handy for testing with the RFC 6238 vectors)")

    sub = subparsers.add_parser("current", help="print the code valid right now")
    sub.add_argument("secret")
    sub.add_argument("--at", type=float, default=None,
                     help="Unix timestamp to compute for instead of now")

    sub = subparsers.add_parser("watch", help="print a fresh code every step")
    sub.add_argument("secret")

    args = parser.parse_args()
    if args.command == "verify":
        if verify(args.secret, args.code, at=args.at,
                  period=args.period, digits=args.digits):
            print("VALID")
        else:
            sys.exit("INVALID")
    elif args.command == "current":
        print(totp(args.secret, at=args.at,
                   period=args.period, digits=args.digits))
    elif args.command == "watch":
        watch(args.secret, period=args.period, digits=args.digits)


if __name__ == "__main__":
    main()
