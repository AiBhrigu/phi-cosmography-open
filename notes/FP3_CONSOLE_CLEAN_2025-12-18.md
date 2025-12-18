# FP3 · Console clean · 2025-12-18

Goal: eliminate console 404 on `/theme/*.css` in GitHub Pages (publish root = `site/`).

Fix:
- `site/theme/{system.css,phi_theme.css}` added (published)
- HTML refs normalized so ACTIVE pages resolve to `/theme/*.css` via relative paths (no `/theme` absolute left in ACTIVE scan)

Checks:
- grep: ABS `/theme` in ACTIVE = empty
- python http.server (from `site/`): `/theme/system.css` and `/theme/phi_theme.css` return 200
