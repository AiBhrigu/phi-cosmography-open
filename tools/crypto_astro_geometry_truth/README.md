# Crypto-Astro Geometry Truth

This verifier enforces the public geometry classes accepted for the Crypto-Astro surface:

- `DATA_BOUND` — geometry is tied to a published value and source binding.
- `SEMANTIC` — geometry communicates relation or state without implying magnitude.
- `DECORATIVE` — geometry provides atmosphere only and carries no scale.

## Local verification

```bash
python3 tools/crypto_astro_geometry_truth/verify_geometry_truth.py \
  --out artifacts/crypto-astro-geometry-truth-report.json
```

The gate fails closed if unsupported percentage-like rails, ambiguous magnitude rings, unbound sample bars, or placeholder trend-memory geometry return.

The immutable eight-module CSS base remains byte-bound to the original extracted source. Geometry repair is appended as one ordered, SHA-256-bound extension module.
