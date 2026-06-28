# A/E Source Semantics Source File Patch Plan v0.1

STATUS: PATCH_PLAN_ARTIFACT_ONLY
TARGET_BRANCH: crypto-astro-a-e-source-semantics-v0-1
TARGET_FILE: site/crypto-astro/index.html
MAIN_PUSH: NO
A_E_NUMERIC_ACTIVATION: NO
RUNTIME: NO
BACKEND_API: NO
BOUNDARY: CLEAN

## Intended source-file changes

Replace public UI copy that may imply active A/E signals with pending source-class semantics.

### Scoring matrix

Current:
- A → Attention / activity
- E → Engagement signal
- M → Market momentum

Target:
- A → Astro-context source class · pending
- E → Ephemerides / evidence source class · pending
- M → 24h market movement context · active

### Signal inputs

Current:
- A · Attention → Attention source slot / pending calibration
- E · Engagement → Public discussion source slot / pending calibration
- M · Market Momentum → Market context / price · 24h change from CoinGecko

Target:
- A · Astro Context → Source class prepared / calibration pending / no current effect
- E · Ephemerides / Evidence Context → Source class prepared / calibration pending / no current effect
- M · Market Context → Active 24h market movement context / price · 24h change

### Preparation copy

Current:
- A/E, Φ Balance, Φ Resonance, and phase context remain calibration layers.
- prepared A/E slots · market context · calibration layers
- A = attention slot / E = engagement slot / M = market context
- Market context active · A/E pending · Not a trading signal.

Target:
- A/E source classes, Φ Balance, Φ Resonance, and phase context remain calibration layers.
- prepared A/E source classes · market context · calibration layers
- A = astro-context source class / E = ephemerides/evidence source class / M = market context
- Market context active · A/E source classes pending · Not a trading signal.

### Runtime render copy

Current:
- A/E pending · Not a trading signal
- Market context active · A/E pending · Not a trading signal.

Target:
- A/E source classes pending · Not a trading signal
- Market context active · A/E source classes pending · Not a trading signal.

## Non-changes

Do not change:
- JSON values
- M formula
- A/E numeric values
- schema guard
- backend/API
- runtime
- live adapter claims
- trading / forecast / investment boundary
