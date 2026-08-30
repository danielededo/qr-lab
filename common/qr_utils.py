"""Shared QR generation helpers used by both subprojects.

Both wifi-qr and totp-qr boil down to "turn this string payload into a QR
image", so that one step lives here. Decoding is only needed by wifi-qr and
stays in its own script.
"""

from pathlib import Path

import segno

SUPPORTED_FORMATS = (".png", ".svg")


def save_qr(payload: str, output: Path, scale: int = 8) -> Path:
    """Encode `payload` as a QR code and save it as PNG or SVG.

    The output format is chosen from the file extension. QR codes carry one of
    four error-correction levels (L ~7%, M ~15%, Q ~25%, H ~30% of codewords
    recoverable); we pin M, a common default that balances density against
    resilience to smudges and glare.
    """
    output = Path(output)
    if output.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValueError(
            f"unsupported output format {output.suffix!r}: use one of {SUPPORTED_FORMATS}"
        )
    qr = segno.make(payload, error="m")
    # `scale` is the size of a single QR module in pixels (PNG) or units (SVG);
    # segno picks the smallest QR version that fits the payload.
    qr.save(str(output), scale=scale)
    return output
