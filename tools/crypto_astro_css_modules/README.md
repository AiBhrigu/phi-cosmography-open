# Crypto-Astro deterministic CSS modules

This layer converts the mechanically extracted legacy stylesheet into ordered source modules while preserving the exact public rendering.

## Canonical files

- `site/theme/crypto_astro/css_order_manifest.json` — module order, source block index, byte count, and SHA-256.
- `site/theme/crypto_astro/modules/*.css` — exact original style blocks.
- `site/theme/crypto_astro_surface.css` — generated runtime bundle.
- `site/theme/crypto_astro_inline_legacy.css` — immutable PR-02 parity reference until the later legacy-removal gate.

## Verify locally

```bash
python3 -m unittest discover -s tools/crypto_astro_css_modules -p "test_*.py" -v
python3 tools/crypto_astro_css_modules/build_css_modules.py --verify-source-base
```

## Rebuild

```bash
python3 tools/crypto_astro_css_modules/build_css_modules.py --write --verify-source-base
```

The builder fails closed when module order, byte count, SHA-256, original style-block binding, generated bundle, or legacy parity differs.

## Boundary

This module does not rename selectors, alter declarations, reorder rules, edit visible copy, change data bindings, repair geometry, activate runtime, or expose protected ORION internals.
