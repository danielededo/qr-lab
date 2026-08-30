"""Decode a WiFi QR code image back into its credentials.

Reads the QR code with OpenCV's built-in detector, then parses the WIFI:
payload by hand — the parsing is the learning exercise here: fields are
`K:V` pairs separated by `;`, and a backslash escapes the next character
(so SSIDs and passwords may legitimately contain `;`, `,`, `:`, `\\`).

Usage:
    python decode.py wifi-qr.png
    python decode.py --webcam          # scan with the default camera
"""

import argparse
import sys
import time

import cv2


def split_unescaped(text: str, separator: str) -> list[str]:
    """Split on `separator`, honoring backslash escapes.

    A backslash makes the following character literal — including another
    backslash — so we walk the string once instead of using str.split().
    The escapes are resolved in the same pass.
    """
    parts, current, escaped = [], [], False
    for char in text:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == separator:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return parts


def parse_wifi_payload(payload: str) -> dict[str, str]:
    """Parse `WIFI:S:<ssid>;T:<auth>;P:<password>;H:<hidden>;;` into a dict."""
    if not payload.startswith("WIFI:"):
        raise ValueError(f"not a WIFI: payload: {payload!r}")
    fields = {}
    for part in split_unescaped(payload[len("WIFI:"):], ";"):
        if not part:
            continue  # the trailing ";;" produces empty parts
        key, _, value = part.partition(":")
        fields[key] = value
    return fields


def decode_image(path: str) -> str:
    image = cv2.imread(path)
    if image is None:
        sys.exit(f"error: could not read image {path!r}")
    payload, _, _ = cv2.QRCodeDetector().detectAndDecode(image)
    if not payload:
        sys.exit(f"error: no QR code found in {path!r}")
    return payload


def decode_webcam(timeout_seconds: int = 30) -> str:
    """Grab frames from the default camera until one contains a QR code."""
    capture = cv2.VideoCapture(0)
    if not capture.isOpened():
        sys.exit("error: could not open the webcam")
    detector = cv2.QRCodeDetector()
    print(f"Point the camera at a QR code ({timeout_seconds}s timeout)...")
    deadline = time.monotonic() + timeout_seconds
    try:
        while time.monotonic() < deadline:
            ok, frame = capture.read()
            if not ok:
                continue
            payload, _, _ = detector.detectAndDecode(frame)
            if payload:
                return payload
    finally:
        capture.release()
    sys.exit("error: no QR code seen before the timeout")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("image", nargs="?", help="path to the QR code image")
    parser.add_argument(
        "--webcam", action="store_true",
        help="capture from the default camera instead of reading an image file",
    )
    args = parser.parse_args()
    if bool(args.image) == args.webcam:
        parser.error("pass either an image path or --webcam")

    payload = decode_webcam() if args.webcam else decode_image(args.image)
    print(f"Raw payload: {payload}")

    try:
        fields = parse_wifi_payload(payload)
    except ValueError:
        print("The QR code decoded fine, but it is not a WiFi payload.")
        return
    print(f"SSID:     {fields.get('S', '')}")
    print(f"Auth:     {fields.get('T', 'nopass')}")
    print(f"Password: {fields.get('P', '')}")
    print(f"Hidden:   {fields.get('H', 'false')}")


if __name__ == "__main__":
    main()
