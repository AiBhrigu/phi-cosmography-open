MODE: OPS/F

NODE=BTC_POSTER_CPU_AND_ANIMATION_BUDGET_REPAIR_v0_1
STATUS=IMPLEMENTATION_CONTOUR_OPEN
ISSUE=125
REPORT_BACK_TO=AiBhrigu/phi-cosmography-open#126

SOURCE_ANCHORS:
- site/theme/btc_poster_grade.css
- site/theme/phi_theme.css
- site/crypto-astro/index.html
- .github/workflows/crypto-astro-static-refresh-pr-visual.yml

IMPLEMENTATION:
1. Limit visible desktop BTC continuous motion to two lightweight layers.
2. Make mobile BTC and Aspect-Cycle geometry static by default.
3. Pause all scoped motion when the BTC module is outside the viewport.
4. Pause all scoped motion while the document is hidden.
5. Remove continuous motion from large masked or repaint-heavy layers.
6. Add scoped containment and content-visibility with intrinsic-size fallback.
7. Preserve poster-grade hierarchy, the single-Phi threshold, BTC dominance binding, and Aspect-Cycle depth.
8. Extend permanent browser CI with animation-state assertions.

PASS_GATE:
- desktop visible running animations <= 2
- desktop offscreen running animations = 0
- hidden-state simulation running animations = 0
- mobile running animations = 0
- reduced-motion running animations = 0
- no horizontal overflow
- no severe browser errors
- desktop/mobile visual evidence PASS

BOUNDARY:
NO_HTML_COPY_EXPANSION
NO_DATA_CHANGE
NO_SNAPSHOT_CHANGE
NO_PROOF_CHANGE
NO_REFRESH_FORMULA_CHANGE
NO_BTC_ROUTE_CHANGE
NO_A_E_ACTIVATION
NO_C_T_RUNTIME_EXPANSION
NO_BACKEND
NO_PAYMENT
NO_ORION_CORE_EXPOSURE
NO_VISUAL_DOWNGRADE_TO_GENERIC_CARDS

TEMP_PACKET_REMOVE_BEFORE_MERGE=YES
NEXT_SAFE_NODE=BTC_POSTER_CPU_AND_ANIMATION_BUDGET_CODE_IMPLEMENTATION_v0_1
