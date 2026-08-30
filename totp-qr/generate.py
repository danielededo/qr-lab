"""Generate a QR code for TOTP/2FA enrollment.

Authenticator apps (Google Authenticator, Aegis, 1Password, ...) enroll a new
account by scanning a QR code that encodes a Key URI:

    otpauth://totp/<label>?secret=<secret>&issuer=<issuer>&algorithm=SHA1&digits=6&period=30

The secret is the only real payload — everything else tells the app how to
derive codes from it (see verify.py for the actual algorithm). A fresh random
secret is generated on every run: the whole scheme's security rests on this
one shared value, so never reuse or commit one.

Usage:
    python generate.py --label "alice@example.com" --issuer qr-lab
"""

import argparse
import base64
import secrets
import sys
from pathlib import Path
from urllib.parse import quote

# Make the repo-level `common` package importable when running this script
# directly from anywhere (each subproject stays standalone, no packaging).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.qr_utils import save_qr


def generate_secret(num_bytes: int = 20) -> str:
    """Return a fresh random secret, base32-encoded as the URI scheme requires.

    20 bytes = 160 bits, matching SHA-1's block-friendly key size and RFC 4226's
    recommended minimum of 128 bits. Base32 (A-Z, 2-7) survives being typed by
    hand, which is why authenticator apps use it for manual entry.
    """
    return base64.b32encode(secrets.token_bytes(num_bytes)).decode("ascii")


def build_otpauth_uri(label: str, secret: str, issuer: str,
                      digits: int, period: int) -> str:
    """Assemble the otpauth:// Key URI understood by authenticator apps."""
    return (
        f"otpauth://totp/{quote(label)}"
        f"?secret={secret}"
        f"&issuer={quote(issuer)}"
        f"&algorithm=SHA1&digits={digits}&period={period}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--label", default="demo@qr-lab",
        help="account label shown in the authenticator app (default: demo@qr-lab)",
    )
    parser.add_argument(
        "--issuer", default="qr-lab",
        help="issuer name shown in the authenticator app (default: qr-lab)",
    )
    parser.add_argument(
        "--digits", type=int, choices=(6, 8), default=6,
        help="code length (default: 6)",
    )
    parser.add_argument(
        "--period", type=int, default=30,
        help="time step in seconds (default: 30)",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("totp-qr.png"),
        help="output image; extension picks the format, .png (default) or .svg",
    )
    parser.add_argument(
        "--scale", type=int, default=8,
        help="pixels per QR module (default: 8)",
    )
    args = parser.parse_args()

    secret = generate_secret()
    uri = build_otpauth_uri(args.label, secret, args.issuer,
                            args.digits, args.period)
    output = save_qr(uri, args.output, scale=args.scale)

    print(f"URI:    {uri}")
    print(f"Secret: {secret}")
    print(f"Saved QR code to {output}")
    print("Scan the QR with an authenticator app, or enter the secret manually;")
    print(f"then cross-check with: python verify.py watch {secret}")


if __name__ == "__main__":
    main()
