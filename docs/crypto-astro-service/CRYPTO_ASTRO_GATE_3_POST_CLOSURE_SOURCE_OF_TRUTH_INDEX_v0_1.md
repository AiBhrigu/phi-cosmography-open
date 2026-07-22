# Crypto-Astro Gate 3 Post-Closure Source-of-Truth Index v0.1

## Purpose

Freeze the accepted evidence chain for the Crypto-Astro Gate 3 owner-authenticated public HTTP proof corridor.

This index separates review evidence, safe diagnostic failures, accepted repairs, and the sole post-merge production proof. It prevents later work from reopening completed repairs or treating a fail-closed diagnostic request as a successful public proof.

## Locked closure state

- Repository: `AiBhrigu/phi-cosmography-open`
- Gate: `PUBLIC_HTTP_PROOF_DISPATCH`
- Gate 3 status: `PASS`
- Production state: `OWNER_AUTHENTICATED_DISPATCH_BRIDGE_LIVE_VERIFIED`
- Current accepted `main`: `4f00ec234b1bb3db43c5687cf678b77ff5d98eaa`
- Canonical snapshot timestamp: `2026-07-22T08:02:05Z`
- Operator F manual actions: `NONE`
- Boundary: `CLEAN`

## Accepted pull-request chain

| PR | Role | Reviewed head | Squash-merge SHA | Review evidence |
|---:|---|---|---|---|
| #158 | Read-only public HTTP proof foundation | `ba798b436accae805d326dc78977a3af05da4dfd` | `4fc4d460587ef434563b0b17b05c68f9caf0ced0` | run `29908527608`, artifact `8524857301` |
| #159 | Owner-authenticated dispatch bridge foundation | `23cb754ec4c2b4c7de487d19918c58123dd413a9` | `a2da529c075699c82c963befb34f946ba211c1b0` | run `29910847407`, artifact `8525796620` |
| #162 | Current-issue and other-open-request preflight repair | `2cd1a43d2004334621a2b5f496d6efa0ce68a418` | `a5d9183da68cfec93eb9fdbaeb57a7469d8454a9` | run `29911860762`, artifact `8526199787` |
| #164 | Exact preflight reason callback repair | `350b899500dfa27abc10aa80e070833468afa11f` | `ce499d0176b05cacde550f7d3ecf430dc6d1b704` | run `29912803447`, artifact `8526579181` |
| #166 | Deterministic target-workflow visibility repair | `5c0d68fbcc2d7cb34eddb924bfaf84935fd31a26` | `4f00ec234b1bb3db43c5687cf678b77ff5d98eaa` | run `29913813145`, artifact `8526996352` |

PR review proofs are evidence for implementation review. They are not substitutes for the final post-merge owner-dispatch production proof.

## Safe diagnostic issue chain

| Issue | Request | Expected `main` | Outcome | Exact reason | Target proof dispatched |
|---:|---|---|---|---|---|
| #160 | `CA-HTTP-20260722-01` | `a2da529c075699c82c963befb34f946ba211c1b0` | `FAIL_PREFLIGHT` | unavailable | `NO` |
| #161 | `CA-HTTP-20260722-02` | `a2da529c075699c82c963befb34f946ba211c1b0` | `FAIL_PREFLIGHT` | unavailable | `NO` |
| #163 | `CA-HTTP-20260722-03` | `a5d9183da68cfec93eb9fdbaeb57a7469d8454a9` | `FAIL_PREFLIGHT` | unavailable | `NO` |
| #165 | `CA-HTTP-20260722-04` | `ce499d0176b05cacde550f7d3ecf430dc6d1b704` | `FAIL_PREFLIGHT` | `FAIL_TARGET_WORKFLOW_VIEW` | `NO` |

These four issues are `SAFE_FAIL_CLOSED_DIAGNOSTIC`. They prove boundary preservation and repair discovery. They do not prove public-route failure and must never be relabelled as production PASS.

## Accepted repair interpretation

1. PR #162 repaired current-issue and other-open-request counting. Issue #163 proved that a shared preflight blocker remained.
2. PR #164 added exact public-safe preflight reason codes. Issue #165 proved `FAIL_TARGET_WORKFLOW_VIEW`.
3. PR #166 replaced the failing API visibility probe with deterministic verification of the fixed target file and its `workflow_dispatch` trigger while preserving the fixed `gh workflow run`, SHA lock, identity lock, issue lock, zero-active-run lock and fail-closed dispatch boundary.

## Sole post-merge production proof

The only accepted production proof for this closure is:

- Issue: `#167`
- Request: `CA-HTTP-20260722-05`
- Operator reference: `COSMOGRAPHER-HTTP-20260722-05`
- Dispatch result: `DISPATCH_ACCEPTED`
- Workflow run: `29914563042`
- Workflow: `crypto-astro-public-http-proof.yml`
- Event/ref: `workflow_dispatch` / `main`
- Expected SHA: `4f00ec234b1bb3db43c5687cf678b77ff5d98eaa`
- Actual head SHA: `4f00ec234b1bb3db43c5687cf678b77ff5d98eaa`
- Job status: `success`
- Final outcome: `PUBLIC_HTTP_PROOF_PASS`
- Proof artifact: `8527304778`
- Artifact digest: `sha256:b692458b3c1fc9ff16d9962d7464326606b4dc251d748ea52913463982e511e9`
- HTTP targets: `6`
- HTTP 200: `6`
- Redirects: `0`
- Issue closure: `closed / completed`

## Source-of-truth files

- `.github/workflows/crypto-astro-public-http-proof.yml`
- `.github/workflows/crypto-astro-public-http-proof-dispatch.yml`
- `.github/workflows/crypto-astro-public-http-proof-dispatch-pr.yml`
- `tools/crypto_astro_public_http_proof/verify_public_http_proof.py`
- `tools/crypto_astro_public_http_proof/verify_public_http_proof_dispatch.py`
- `docs/crypto-astro-service/CRYPTO_ASTRO_PUBLIC_HTTP_PROOF_DISPATCH_v0_1.md`
- `docs/crypto-astro-service/crypto_astro_public_http_proof_dispatch_v0_1.json`

## Memory handoff

Machine-readable capsule:

`docs/crypto-astro-service/crypto_astro_gate_3_post_closure_memory_handoff_v0_1.json`

Memory rules:

1. Only issue #167 and run `29914563042` are the post-merge owner-dispatch production PASS.
2. Issues #160, #161, #163 and #165 remain safe diagnostic failures.
3. Gate 3 did not refresh market values and did not mutate public HTML or JSON.
4. No cron, backend, public API, payment, A/E, Temporal, forecast, trading signal, price target or ORION scope was opened.
5. The next refresh requires separate explicit authorization and a new SHA-locked proof chain.

## Hold state

```text
STATE=HOLD_UNTIL_NEXT_AUTHORIZED_CRYPTO_ASTRO_REFRESH
AUTOMATIC_REFRESH=NO
AUTOMATIC_DISPATCH=NO
OPERATOR_ACTION_REQUIRED=NO
BOUNDARY=CLEAN
```
