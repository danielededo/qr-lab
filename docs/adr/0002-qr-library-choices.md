# ADR 0002: Use segno for QR generation and OpenCV for decoding

- **Status:** Accepted
- **Date:** 2026-08-30
- **Deciders:** danielededo

## Context

Both subprojects need to render QR codes, and wifi-qr also needs to decode
them from images. This is a learning repository: dependencies should install
with a plain `pip install -r requirements.txt` on Linux, macOS, and Windows,
and the libraries should stay out of the way of the parts we implement by
hand (payload escaping, WIFI: parsing, RFC 6238).

## Decision

We will use **segno** to generate QR codes and **opencv-python-headless**
(`cv2.QRCodeDetector`) to decode them. segno is pure Python with zero
dependencies and writes both PNG and SVG natively; OpenCV's wheel bundles
everything it needs, so neither requires an OS package manager.

## Options considered

### Option 1: segno + OpenCV (chosen)

- Pros: pip-only installation everywhere; segno has no transitive
  dependencies; one decoder API (`detectAndDecode`) with webcam capture
  included for free.
- Cons: the OpenCV wheel is large (~50 MB); its detector is somewhat less
  robust on damaged or low-contrast codes than zbar.

### Option 2: qrcode + pyzbar

- Pros: pyzbar's zbar backend is the most robust common decoder; `qrcode` is
  the most widely known generator.
- Cons: both lean on native libraries users must install themselves (zbar via
  apt/brew, Pillow for PNG output), breaking the "clone, pip install, run"
  flow — a real cost in a repo meant to be tried out quickly.

### Option 3: one full-featured library for both (e.g. OpenCV only)

- Pros: single dependency.
- Cons: OpenCV cannot *generate* QR codes portably across the versions in the
  wild; abusing it for generation obscures the encoding side we want to study.

## Consequences

- `pip install -r requirements.txt` is the entire setup on every platform.
- Decoding badly damaged codes may fail where zbar would succeed; acceptable
  here, since we decode images we generated ourselves. Anyone experimenting
  with error-correction limits can swap in pyzbar locally.
- totp-qr only needs segno, keeping its requirements to a single pure-Python
  package (verify.py is standard-library-only by design).

## References

- https://segno.readthedocs.io/
- https://docs.opencv.org/4.x/de/dc3/classcv_1_1QRCodeDetector.html
