# Crypto-Astro Surface Truth Harness

This module records deterministic baseline evidence for the static Crypto-Astro public surface.

## Local run

```bash
python3 -m pip install selenium==4.34.2
python3 -m http.server 4173 --directory site >/tmp/crypto-astro-surface-truth.log 2>&1 &
python3 tools/crypto_astro_surface_truth/surface_truth.py \
  --url http://127.0.0.1:4173/crypto-astro/index.html \
  --out artifacts/crypto-astro-surface-truth
```

## Evidence

The runner emits:

- `surface-truth-report.json`
- `dom-structure.json` and SHA-256
- `visible-text.txt` and SHA-256
- `public-value-map.json`
- `anchor-href-map.json`
- `computed-style-fingerprint.json` and SHA-256
- `bounding-box-report.json`
- `motion-report.json`
- `overflow-report.json`
- desktop and mobile screenshots
- `sha256_manifest.txt`

## Boundary

The harness is test-only. It does not edit HTML, CSS, snapshots, runtime state, backend, payment, or protected ORION internals.
