# Crypto-Astro Local Truth LT-1

This wrapper runs the existing surface-truth harness against a local static server and verifies the emitted SHA-256 manifest.

## One-command local run

```bash
bash tools/crypto_astro_local_truth/run_local_truth.sh \
  . \
  artifacts/crypto-astro-local-truth-lt1
```

The runner starts and stops its own local HTTP server. It does not edit the site, CSS, snapshot data, backend, payment, or protected ORION internals.

## Import graph verification

Before normalization, `system.css` is loaded by both a direct HTML link and the `phi_theme.css` import. After normalization, the direct HTML link is absent while the single `phi_theme.css` import remains.

```bash
python3 tools/crypto_astro_local_truth/verify_import_graph.py --mode after
```

The verification is fail-closed: missing or duplicate `system.css` imports fail the gate.

The PR gate records exact-base LT-1 evidence, normalized-head evidence, import-route counts, and base/head screenshot parity in one artifact.
