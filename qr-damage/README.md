# qr-damage

Break QR codes on purpose to see error correction actually work. Two scripts:
one shows what each error-correction level *costs* (bigger symbols), the other
damages codes until they stop decoding and compares where each level gives up.

## Setup

```sh
cd qr-damage
pip install -r requirements.txt
```

## capacity.py — what redundancy costs

```sh
python capacity.py
```

Expected output:

```
Payload: 'https://github.com/danielededo/qr-lab' (37 characters)

  L: version  3 — 29×29 modules — ~7% of codewords recoverable — capacity-L.png
  M: version  3 — 29×29 modules — ~15% of codewords recoverable — capacity-M.png
  Q: version  4 — 33×33 modules — ~25% of codewords recoverable — capacity-Q.png
  H: version  5 — 37×37 modules — ~30% of codewords recoverable — capacity-H.png
```

Same payload, four sizes: everything beyond the L symbol is pure redundancy.

## damage.py — spending that redundancy

```sh
python damage.py                 # both experiments, all four levels
python damage.py --mode blot     # just the sticker experiment
python damage.py --save-samples out/   # keep example damaged images
```

Expected output (abridged — `--seed` makes it reproducible):

```
== Scattered damage: random modules inverted, 5 trials per step ==
  L (version 3, 29×29 modules, nominal ~7%)
    damage 0%→4% in 1% steps: #+...
    always decodes at ≤ 0% · first total failure at 2%
  H (version 5, 37×37 modules, nominal ~30%)
    damage 0%→6% in 1% steps: #+++...
    always decodes at ≤ 0% · first total failure at 4%

== Contiguous damage: white square growing from the center ==
  L (version 3, 29×29): survives up to 6×6 modules — 4% of the symbol
  M (version 3, 29×29): survives up to 8×8 modules — 8% of the symbol
  Q (version 4, 33×33): survives up to 11×11 modules — 11% of the symbol
  H (version 5, 37×37): survives up to 17×17 modules — 21% of the symbol
```

## What the two experiments teach

A QR code's data is split into 8-bit **codewords**, and Reed-Solomon error
correction adds redundant codewords: level L can restore roughly 7% of them,
M 15%, Q 25%, H 30%. The catch is that those figures count *codewords*, while
physical damage hits *modules* (the individual black/white cells) — and how
the damaged modules cluster changes everything:

- **Scattered damage is catastrophic.** Each codeword spans 8 modules, so
  each randomly scattered flip tends to land in a *different* codeword —
  wounding one codeword per module, ~8× the damage share. Even level H dies
  around 3–4% of modules flipped. This is why a QR printed on a rough surface
  that speckles evenly fails long before "30% damage".
- **Contiguous damage is what the nominal figures are about.** A sticker-like
  blot concentrates its modules into few codewords, so the survivable area
  cleanly follows L < M < Q < H (4% / 8% / 11% / 21% of the symbol here).
  It still tops out around *half* the nominal capacity: Reed-Solomon can fix
  twice as many **erasures** (corruptions at known positions) as **errors**
  (unknown positions), and a decoder reading a white blot doesn't know which
  modules are wrong — it pays the full error price.

Other details worth noticing in the code: the experiment pins
`boost_error=False` (segno silently upgrades the EC level when the symbol has
spare room, which would muddy the comparison), the blot grows from the center
so the *finder patterns* stay intact (damage them and the decoder fails to
even locate the symbol, regardless of Reed-Solomon), and module inversion is
used rather than graying-out because it guarantees a wrong bit instead of
leaving it to the decoder's thresholding.
