"""Show what each error-correction level costs.

A QR code reserves part of its codewords for Reed-Solomon error correction.
There are four levels — L, M, Q, H — that can restore roughly 7%, 15%, 25%,
and 30% of damaged codewords. More protection means more redundancy, which
means a bigger symbol for the same payload: this script encodes one payload
at all four levels and prints the size each one needs.

Usage:
    python capacity.py
    python capacity.py --payload "any text you like" --outdir /tmp
"""

import argparse
from pathlib import Path

import segno

LEVELS = "LMQH"
NOMINAL_RECOVERY = {"L": 7, "M": 15, "Q": 25, "H": 30}  # % of codewords


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--payload", default="https://github.com/danielededo/qr-lab",
        help="text to encode at all four levels",
    )
    parser.add_argument(
        "--outdir", type=Path, default=Path("."),
        help="where to save capacity-L/M/Q/H.png (default: current directory)",
    )
    args = parser.parse_args()

    print(f"Payload: {args.payload!r} ({len(args.payload)} characters)\n")
    for level in LEVELS:
        # boost_error=False: segno otherwise silently upgrades the level when
        # the chosen version has spare room, which would muddy the comparison.
        qr = segno.make(args.payload, error=level.lower(), boost_error=False)
        size = qr.symbol_size(scale=1, border=0)[0]
        out = args.outdir / f"capacity-{level}.png"
        qr.save(str(out), scale=8)
        print(
            f"  {level}: version {qr.version:2d} — {size}×{size} modules — "
            f"~{NOMINAL_RECOVERY[level]}% of codewords recoverable — {out}"
        )
    print(
        "\nSame payload, four sizes: the extra modules are pure redundancy —"
        "\nthat redundancy is what damage.py spends."
    )


if __name__ == "__main__":
    main()
