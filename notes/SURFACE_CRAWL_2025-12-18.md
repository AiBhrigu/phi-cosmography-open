# SURFACE_CRAWL · 2025-12-18
Branch: wip/fp1-surface-crawl-2025-12-18
Scope: FP1 notes only (NO-TOUCH core/routing/formulas)

## Method
- Repo/static scan: ./tools/surface_status.sh (saved: /tmp/surface_status_2025-12-18.txt)
- Browser/UI run: NOT TESTED (no local server run in FP1)

## Links
- Internal link check via browser: NOT TESTED
- Repo scan: no explicit broken-link report in tools output

## Console
- NOT TESTED (no browser run)

## Layout
- NOT TESTED (no browser run)
- Note: CSS “hotlist” observed in surface_status output (phi/floors, suncore, nav, mobile, layers, text, etc.) — see /tmp/surface_status_2025-12-18.txt

## Focus / UX
- NOT TESTED (no browser run)

## Next atoms (strict order)
FP2 Link Integrity:
- Run browser click-walk on routes; record any 404/broken anchors; fix only links (no routing changes)
FP3 Console Clean:
- Run browser; capture exact console errors; fix only surface-level JS/HTML/CSS (no core)
FP4 Focus/Keyboard:
- Tab-path + focus-visible audit; fix focus styles/aria labels where needed
FP5 Responsive micro-fix:
- Narrow-width overflow/collisions; micro CSS only

## STOP flags
- Any “rewrite routing / refactor architecture / touch formulas/core” => STOP + CONTROL ROOM
