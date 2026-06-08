# ORION Evidence Artifact Protocol Canon

STATUS: INTERNAL_ONLY
VERSION: v0_1
CANON_STATUS: ACCEPTED · PASS
PUBLIC_STATUS: NOT_PUBLIC
BOUNDARY: No runtime, no implementation, no product claim, no public launch claim.

This document is an internal OPS/F evidence artifact.
It preserves protocol governance only.
It does not grant file writes, repo mutation, automation, runtime activation, implementation, public launch, product readiness, trading signal, prediction, or financial advice.

---

## Node Identity

NODE:
ORION_EVIDENCE_ARTIFACT_PROTOCOL_SCOPE_v0_1

ARTIFACT:
ORION_EVIDENCE_ARTIFACT_PROTOCOL_CANON.md

ARTIFACT_CLASS:
INTERNAL_MD_EVIDENCE_ARTIFACT
CANON_PROTOCOL_RECORD
OPS_F_MEMORY_GOVERNANCE_RECORD

SOURCE_CHAIN:
ORION_EVIDENCE_ARTIFACT_PROTOCOL_SCOPE_v0_1
→ ORION_EVIDENCE_ARTIFACT_PROTOCOL_SCOPE_REVIEW_v0_1
→ ORION_EVIDENCE_ARTIFACT_PROTOCOL_SCOPE_RECHECK_v0_1
→ ORION_EVIDENCE_ARTIFACT_PROTOCOL_SCOPE_REVIEW_CLOSURE_v0_1

---

## Canon Status

VERDICT:
PASS

CLOSURE_STATUS:
CLOSED · PASS
CLOSED_SAFE
NO_DRIFT
BOUNDARY_CLEAN

ARTIFACT_DECISION:
ARTIFACT_REQUIRED_MD

---

## Purpose

Preserve the accepted Evidence Artifact Protocol canon closure as an internal evidence artifact.

Purpose:
- prevent future drift in artifact decisions
- define when `.md`, capsule, or map artifacts are required
- preserve memory/index governance without expanding runtime, repo, or public surface
- maintain the OPS/F rule: closure → artifact decision → memory/index update

---

## Core Rule

```text
closure → artifact decision → memory/index update
```

Meaning:
1. Close the node.
2. Classify evidence need.
3. Choose `.md`, capsule, map, memory-only, or no artifact.
4. If file artifact is needed, open separate artifact creation scope.
5. Update Memory Control only when milestone/state class requires it.

---

## Artifact Required Node Classes

```text
1. MILESTONE_CLOSURE
   Major proof state closed PASS.

2. CANON_CLOSURE
   Protocol / canon / operating rule accepted and closed.

3. PUBLIC_BOUNDARY_CHANGE
   Public-safe / not-public / route / launch boundary changes.

4. RUNTIME_OR_IMPLEMENTATION_GATE
   Any node that changes readiness class, even if implementation remains blocked.

5. REPO_OR_GITHUB_STATE_CHANGE
   Commit, branch sync, PR, merge, visibility, repo target confirmation.

6. ATOM_RESULT_CLOSURE
   ATOM pack creation, staging proof, execution result, final proof closure.

7. DRIFT_CORRECTION_ACCEPTED
   Current state corrected against stale memory / archive / worker output.

8. CROSS_CHAT_HANDOFF
   State needs transfer between Master, Worker, Memory, Backup, Archive.

9. VISUAL_CANON_OR_SURFACE_MILESTONE
   Only if visual branch is active and accepted as semantic navigation module.

10. SERVICE_CONTOUR_CHANGE
   Chain changes class: docs → visibility → service path → runtime sandbox → implementation boundary.
```

---

## Artifact Not Required Node Classes

```text
1. SIMPLE_REVIEW
   Review step with no state-class change.

2. SIMPLE_RECHECK
   Recheck step with no drift and no milestone.

3. SCOPE_ONLY_INTERMEDIATE
   Scope definition that does not close a chain or change active class.

4. WORKER_LOCK_CONFIRMATION
   Unless it corrects major drift.

5. ROUTING_ACK
   Navigation / send-to-worker / report received only.

6. STOP_NODE
   If no milestone, no drift, no state change.

7. DUPLICATE_REPORT
   Same content already indexed.

8. TEMPORARY_OPERATOR_CONTEXT
   Short-lived working context not needed after closure.
```

---

## MD Rule

Use `.md` when the artifact must become a stable human-readable proof document.

USE_MD_FOR:
```text
- milestone closure
- public-safe documentation record
- architecture / boundary / protocol canon
- final proof result
- service contour summary
- repo/GitHub sync proof
- launch/runtime boundary record
```

Minimum use case:
```text
Readable by future operator.
Safe to inspect without reconstructing full chat.
Can serve as stable evidence record.
```

---

## Capsule Rule

Use capsule when artifact is for cross-chat state transfer or restart.

USE_CAPSULE_FOR:
```text
- Master → Worker handoff
- Master → Memory milestone compression
- Master → Passive Backup snapshot
- cold-start recovery
- drift repair
- active chain continuation
```

Capsule minimum fields:
```text
NODE
STATUS
CURRENT_STATE
NEXT_SAFE_NODE
LOCKS
BOUNDARY
```

No full history unless correcting drift.

---

## Map Rule

Use map when relationships matter more than a linear report.

USE_MAP_FOR:
```text
- Master / Worker / Memory / Archive routing
- service contour
- launch class ladder
- dependency gates
- public/private surface classification
- proof → memory → output flow
```

Map boundary:
```text
MAP_NOT_UI
MAP_NOT_RUNTIME
MAP_NOT_DASHBOARD
MAP_NOT_DECORATION
```

---

## Minimum Preserved Fields

Every evidence artifact must preserve:

```text
NODE
VERSION
STATUS
VERDICT
SOURCE
DESTINATION
REPORT_BACK_TO
CURRENT_STATE
ACCEPTED_FACTS
BOUNDARY_LOCKS
NEXT_SAFE_NODE
PROVEN / NOT_PROVEN status
BLOCKED_ACTIONS
DRIFT_CORRECTION_IF_ANY
DATE_OR_RUN_ID_IF_AVAILABLE
```

For repo/runtime/service nodes, also preserve:

```text
REPO_TARGET_STATUS
ROOT_PATH_STATUS
RUNTIME_STATUS
IMPLEMENTATION_STATUS
PUBLIC_LAUNCH_STATUS
```

For ATOM nodes, also preserve:

```text
PACK_NAME
RUNNER_NAME
SHA256
RUN_STATUS
OUTPUT_REPORTS
FILE_MODIFICATION_STATUS
GITHUB_MUTATION_STATUS
```

---

## Memory-Only Fields

Keep inside memory only:

```text
1. transient active chat routing
2. intermediate review/recheck steps with no state change
3. operator rhythm / working preference notes
4. stale NEXT_SAFE_NODE history after correction
5. private tactical reasoning
6. unproven candidate vectors
7. temporary blocked-safe branches
8. non-public coordination details
9. detailed cross-chat cleanup mechanics
10. internal ambition beyond public boundary
```

Memory Control should index milestones, not every step.

---

## Public-Blocked Fields

Never write publicly:

```text
1. private mechanism internals
2. implementation internals not public-safe
3. runtime architecture before approval
4. API keys / secrets / tokens
5. wallet addresses if not explicitly public-safe
6. market/wallet/live-data traces
7. trading signals
8. prediction claims
9. financial advice
10. buy / sell / hold language
11. private local operator paths unless artifact is internal-only
12. unreviewed logs with accidental sensitive content
13. Frey / Reading / X4 protected internals
14. public launch or product readiness claims unless proven and approved
```

---

## Closure Decision Rule

```text
closure → artifact decision → memory/index update
```

Decision flow:
```text
1. Close node.
2. Classify node:
   ARTIFACT_REQUIRED / ARTIFACT_NOT_REQUIRED / MEMORY_ONLY.

3. If artifact required:
   choose MD / CAPSULE / MAP.

4. If file artifact is needed:
   open separate artifact creation scope.
   no automatic file write.

5. Update Memory Control only if:
   milestone proven,
   chain closes,
   active node changes class,
   major drift correction accepted,
   launch/runtime boundary changes.
```

Artifact decision labels:
```text
ARTIFACT_REQUIRED_MD
ARTIFACT_REQUIRED_CAPSULE
ARTIFACT_REQUIRED_MAP
MEMORY_ONLY_INDEX
NO_ARTIFACT_REQUIRED
BLOCKED_SAFE
```

---

## Memory / Index Relation

Master owns active chain state.
Memory Control stores milestone indexes only.
Worker receives one exact task and returns one report.
Archive chats do not receive new work.
Passive Backup stores emergency snapshot only.

Priority:
```text
1. live active Master state
2. latest Worker report accepted by Master
3. latest Memory Control milestone
4. Passive Backup snapshot
5. Archive/Reserve history
```

On conflict, live active Master state wins.

---

## Worker / Master Boundary

Worker may define scope or return report only.
Master reviews, rechecks, closes, and chooses next node.
No worker opens new vector automatically.
No archive chat receives new work.

---

## +++ Canon Relation

```text
+++ = one safe continuation step along accepted NEXT_SAFE_NODE only.
```

`+++` does not grant:
```text
new vector
runtime
terminal
implementation
repo mutation
public launch
visual branch
runner execution
file write
```

---

## Boundary Locks

```text
NO_RUNTIME
NO_IMPLEMENTATION
NO_PRODUCT_CLAIM
NO_PUBLIC_LAUNCH_CLAIM
NO_TRADING_SIGNAL
NO_PREDICTION_CLAIM
NO_FINANCIAL_ADVICE
NO_REPO_GITHUB_MUTATION_UNLESS_SEPARATELY_GRANTED
NO_FILE_WRITE_UNLESS_SEPARATELY_GRANTED
NO_FREY_TOUCH
NO_READING_TOUCH
NO_X4_TOUCH
```

---

## Next Safe Node

After this artifact exists, next safe node should be selected by Master based on current live state.

Default:

```text
MASTER_VECTOR_SELECTION
or
STOP
```

