"""Damage QR codes until they stop decoding, at every error-correction level.

Two damage models, because they end very differently:

- **scatter**: invert a growing fraction of randomly chosen modules. Deadly
  far below the nominal capacity — every Reed-Solomon codeword spans 8
  modules, so each scattered flip tends to wound a *different* codeword,
  corrupting ~8× its share of them.
- **blot**: grow a white square from the center, like a sticker slapped on
  the code. Contiguous modules share codewords, so this tracks the nominal
  L/M/Q/H capacities (roughly halved: errors at unknown positions cost
  Reed-Solomon twice what erasures do).

Usage:
    python damage.py                    # both experiments, all four levels
    python damage.py --mode scatter --levels H --trials 10
    python damage.py --mode blot --payload "any text"
    python damage.py --save-samples out/
"""

import argparse
import io
import random
import sys
from pathlib import Path

import cv2
import numpy as np
import segno

LEVELS = "LMQH"
NOMINAL_RECOVERY = {"L": 7, "M": 15, "Q": 25, "H": 30}  # % of codewords
SCALE = 8    # pixels per module
BORDER = 4   # quiet-zone width in modules (the spec's minimum)


def make_qr_image(payload: str, level: str) -> tuple[np.ndarray, int, int]:
    """Render the payload at one EC level; return (grayscale image, modules
    per side, QR version)."""
    # boost_error=False: segno otherwise silently upgrades the level when the
    # chosen version has spare room, which would muddy the comparison.
    qr = segno.make(payload, error=level.lower(), boost_error=False)
    buffer = io.BytesIO()
    qr.save(buffer, kind="png", scale=SCALE, border=BORDER)
    image = cv2.imdecode(
        np.frombuffer(buffer.getvalue(), np.uint8), cv2.IMREAD_GRAYSCALE
    )
    size = qr.symbol_size(scale=1, border=0)[0]
    return image, size, qr.version


def module_rect(row: int, col: int) -> tuple[int, int]:
    """Top-left pixel of a module, accounting for the quiet zone."""
    return (BORDER + row) * SCALE, (BORDER + col) * SCALE


def flip_modules(
    image: np.ndarray, size: int, fraction: float, rng: random.Random
) -> np.ndarray:
    """Return a copy with `fraction` of all modules inverted (black↔white).

    Inversion is the worst case: a smudged gray module may still threshold
    correctly, an inverted one is a guaranteed wrong bit at an unknown
    position.
    """
    count = min(round(fraction * size * size), size * size)
    damaged = image.copy()
    coords = rng.sample([(r, c) for r in range(size) for c in range(size)], count)
    for row, col in coords:
        y, x = module_rect(row, col)
        block = damaged[y:y + SCALE, x:x + SCALE]
        block[:] = 255 - block
    return damaged


def blot_square(image: np.ndarray, size: int, side: int) -> np.ndarray:
    """Return a copy with a white `side`×`side`-module square over the center
    (the finder corners stay intact until the blot is enormous, so what fails
    is error correction, not symbol detection)."""
    damaged = image.copy()
    y, x = module_rect((size - side) // 2, (size - side) // 2)
    damaged[y:y + side * SCALE, x:x + side * SCALE] = 255
    return damaged


def decodes(image: np.ndarray, payload: str, detector: cv2.QRCodeDetector) -> bool:
    decoded, _, _ = detector.detectAndDecode(image)
    return decoded == payload


def sweep_scatter(
    payload: str,
    level: str,
    args: argparse.Namespace,
    detector: cv2.QRCodeDetector,
    rng: random.Random,
) -> None:
    image, size, version = make_qr_image(payload, level)
    print(
        f"  {level} (version {version}, {size}×{size} modules, "
        f"nominal ~{NOMINAL_RECOVERY[level]}%)"
    )

    bar = []
    last_all_ok = None
    first_all_fail = None
    consecutive_failures = 0
    fraction = 0.0
    while fraction <= args.max_damage:
        successes = sum(
            decodes(flip_modules(image, size, fraction, rng), payload, detector)
            for _ in range(args.trials)
        )
        if successes == args.trials:
            bar.append("#")
            last_all_ok = fraction
        else:
            bar.append("+" if successes else ".")
            if successes == 0 and first_all_fail is None:
                first_all_fail = fraction
        consecutive_failures = 0 if successes else consecutive_failures + 1
        # Three total failures in a row: this level is dead, stop probing it.
        if consecutive_failures >= 3:
            break
        fraction = round(fraction + args.step, 10)

    print(f"    damage 0%→{fraction:.0%} in {args.step:.0%} steps: {''.join(bar)}")
    parts = []
    if last_all_ok is not None:
        parts.append(f"always decodes at ≤ {last_all_ok:.0%}")
    if first_all_fail is not None:
        parts.append(f"first total failure at {first_all_fail:.0%}")
    print(f"    {' · '.join(parts) or 'never decoded'}")


def sweep_blot(
    payload: str,
    level: str,
    args: argparse.Namespace,
    detector: cv2.QRCodeDetector,
) -> None:
    image, size, version = make_qr_image(payload, level)
    survived = 0
    for side in range(1, size):
        if not decodes(blot_square(image, size, side), payload, detector):
            break
        survived = side
        if args.save_samples and side % 4 == 0:
            path = args.save_samples / f"blot-{level}-{side}x{side}.png"
            cv2.imwrite(str(path), blot_square(image, size, side))
    area = survived * survived / (size * size)
    print(
        f"  {level} (version {version}, {size}×{size}): survives up to "
        f"{survived}×{survived} modules — {area:.0%} of the symbol "
        f"(nominal ~{NOMINAL_RECOVERY[level]}% of codewords)"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--payload", default="https://github.com/danielededo/qr-lab",
        help="text to encode",
    )
    parser.add_argument(
        "--mode", choices=("scatter", "blot", "both"), default="both",
        help="damage model to run (default: both)",
    )
    parser.add_argument(
        "--levels", default=LEVELS,
        help=f"which EC levels to sweep (default: {LEVELS})",
    )
    parser.add_argument(
        "--trials", type=int, default=5,
        help="scatter mode: random damage patterns per step (default: 5)",
    )
    parser.add_argument(
        "--step", type=float, default=0.01,
        help="scatter mode: damage-fraction increment (default: 0.01)",
    )
    parser.add_argument(
        "--max-damage", type=float, default=0.40,
        help="scatter mode: highest damage fraction to try (default: 0.40)",
    )
    parser.add_argument(
        "--save-samples", type=Path, default=None, metavar="DIR",
        help="save example damaged images into DIR",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="RNG seed; change it to see run-to-run variance (default: 42)",
    )
    args = parser.parse_args()

    levels = [level for level in args.levels.upper() if level in LEVELS]
    if not levels:
        sys.exit(f"error: --levels must use characters from {LEVELS!r}")
    if args.save_samples:
        args.save_samples.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)
    detector = cv2.QRCodeDetector()
    print(f"Payload: {args.payload!r}\n")

    if args.mode in ("scatter", "both"):
        print(
            f"== Scattered damage: random modules inverted, "
            f"{args.trials} trials per step ==\n"
            "   legend: '#' every trial decodes · '+' some do · '.' none do"
        )
        for level in levels:
            sweep_scatter(args.payload, level, args, detector, rng)
        print(
            "\n   Every level dies far below its nominal capacity: one flipped\n"
            "   module ruins a whole 8-module codeword, so scattered damage\n"
            "   corrupts ~8× its share of codewords.\n"
        )

    if args.mode in ("blot", "both"):
        print("== Contiguous damage: white square growing from the center ==")
        for level in levels:
            sweep_blot(args.payload, level, args, detector)
        print(
            "\n   Contiguous modules share codewords, so the blot follows the\n"
            "   L<M<Q<H ordering — at roughly half the nominal figures, since\n"
            "   errors at unknown positions cost Reed-Solomon twice what\n"
            "   erasures (known positions) do."
        )


if __name__ == "__main__":
    main()
