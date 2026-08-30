"""Generate a QR code that encodes WiFi credentials.

Phones understand a de-facto standard payload (originally from the ZXing
project) of the form:

    WIFI:S:<ssid>;T:<auth>;P:<password>;H:<true|false>;;

Scanning it offers to join the network directly. The interesting part is the
escaping: `\\`, `;`, `,` and `:` are structural characters of the payload, so
they must be backslash-escaped inside the SSID and password.

Usage:
    python generate.py --ssid "My Network" --password "hunter2" --auth WPA
    python generate.py --auto                    # detect the current network
    python generate.py --ssid Cafe --auth nopass --output cafe.svg
"""

import argparse
import getpass
import sys
from pathlib import Path

# Make the repo-level `common` package importable when running this script
# directly from anywhere (each subproject stays standalone, no packaging).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.qr_utils import save_qr  # noqa: E402
from network_detect import DetectionError, detect  # noqa: E402

AUTH_TYPES = ("WPA", "WEP", "nopass")


def escape(value: str) -> str:
    """Backslash-escape the characters that are structural in a WIFI: payload.

    The backslash itself must go first, or we would double-escape the
    backslashes introduced for the other characters.
    """
    for char in ("\\", ";", ",", ":"):
        value = value.replace(char, "\\" + char)
    return value


def build_wifi_payload(ssid: str, password: str, auth: str, hidden: bool) -> str:
    """Assemble the WIFI: string exactly per the de-facto spec."""
    return (
        f"WIFI:S:{escape(ssid)};"
        f"T:{auth};"
        f"P:{escape(password)};"
        f"H:{'true' if hidden else 'false'};;"
    )


def prompt_manually() -> tuple[str, str, str]:
    """Interactive fallback when --auto fails: ask for the three inputs."""
    try:
        ssid = input("SSID: ").strip()
        auth = input(f"Auth type {AUTH_TYPES} [WPA]: ").strip() or "WPA"
        if auth not in AUTH_TYPES:
            sys.exit(f"error: auth type must be one of {AUTH_TYPES}, got {auth!r}")
        password = "" if auth == "nopass" else getpass.getpass("Password: ")
    except (EOFError, KeyboardInterrupt):
        sys.exit("\nerror: no input available — pass --ssid/--password instead")
    return ssid, password, auth


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ssid", help="network name (required unless --auto)")
    parser.add_argument("--password", default="", help="network password")
    parser.add_argument(
        "--auth", choices=AUTH_TYPES, default="WPA",
        help="authentication type (default: WPA; covers WPA2/WPA3-personal too)",
    )
    parser.add_argument(
        "--hidden", action="store_true",
        help="mark the network as hidden (not broadcasting its SSID)",
    )
    parser.add_argument(
        "--auto", action="store_true",
        help="detect the currently connected network's SSID and password "
             "instead of passing them manually (OS-specific, see README)",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("wifi-qr.png"),
        help="output image; extension picks the format, .png (default) or .svg",
    )
    parser.add_argument(
        "--scale", type=int, default=8,
        help="pixels per QR module (default: 8)",
    )
    args = parser.parse_args()

    ssid, password, auth = args.ssid, args.password, args.auth
    if args.auto:
        try:
            ssid, password = detect()
            # An empty password from detection means an open network.
            auth = args.auth if password else "nopass"
            print(f"Detected network: {ssid!r}")
        except DetectionError as exc:
            print(f"Auto-detection failed: {exc}", file=sys.stderr)
            print("Falling back to manual input.", file=sys.stderr)
            ssid, password, auth = prompt_manually()
    elif not ssid:
        parser.error("--ssid is required (or use --auto)")

    if auth != "nopass" and not password:
        parser.error(f"auth type {auth} needs a --password (or use --auth nopass)")

    payload = build_wifi_payload(ssid, password, auth, args.hidden)
    output = save_qr(payload, args.output, scale=args.scale)
    print(f"Payload: {payload}")
    print(f"Saved QR code to {output}")


if __name__ == "__main__":
    main()
