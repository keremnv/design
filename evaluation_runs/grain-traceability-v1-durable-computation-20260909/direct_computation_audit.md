# Direct held-out computation audit

The frozen bundles were executed on all ten held-out parameter instances. No native evidence, network, LLM, or World mutation was available to the computations. Author-only test fixtures were excluded from the consumer-visible bundles.

| World | Directly supported | Supported via composition | Not covered | Incorrect | Unsupported closure |
| --- | ---: | ---: | ---: | ---: | ---: |
| OA-G1 | 6 | 1 | 3 | 0 | 0 |
| OA-G2 | 5 | 2 | 3 | 0 | 0 |

The repeated uncovered cases are custody-at-time propagation and the South House 14 inspection-to-receipt consequence. The former is scope-sensitive: the World has a ticket-scoped holder record and a movement-scoped Northstar handoff, while the held-out gold asks for a material-level answer. The latter relies on treating “South House 14 cargo” as the later HFM-IN-604 movement; conservative refusal is defensible because the sample does not name that receipt. These are retained as frozen evaluator outcomes, not repaired.

### Holdout integrity caveat

The development task file and gold were physically excluded from authoring workspaces, and the frozen consumer bundles contain no evaluator-task IDs, gold, or held-out answer tables. The Worlds themselves contain all operational identifiers, however, and the authoring hosts were permitted to inspect them freely. OA-G2’s author-only test fixture consequently exercised several held-out-looking parameter values. Those test fixtures were preserved as authoring artifacts but excluded from the frozen consumer-visible bundle. This preserves computation-shape testing rather than answer caching, but strict parameter-value blindness is not claimed.

### Per-instance classifications

- OA-G1 / EVAL-SRC-001: **DIRECTLY_SUPPORTED**
- OA-G1 / EVAL-SRC-002: **DIRECTLY_SUPPORTED**
- OA-G1 / EVAL-SRC-003: **DIRECTLY_SUPPORTED**
- OA-G1 / EVAL-PROV-001: **DIRECTLY_SUPPORTED**
- OA-G1 / EVAL-PROV-002: **DIRECTLY_SUPPORTED**
- OA-G1 / EVAL-CUST-001: **NOT_COVERED**
- OA-G1 / EVAL-CUST-002: **NOT_COVERED**
- OA-G1 / EVAL-INSP-001: **SUPPORTED_VIA_COMPOSITION**
- OA-G1 / EVAL-INSP-002: **NOT_COVERED**
- OA-G1 / EVAL-INSP-003: **DIRECTLY_SUPPORTED**
- OA-G2 / EVAL-SRC-001: **DIRECTLY_SUPPORTED**
- OA-G2 / EVAL-SRC-002: **DIRECTLY_SUPPORTED**
- OA-G2 / EVAL-SRC-003: **DIRECTLY_SUPPORTED**
- OA-G2 / EVAL-PROV-001: **SUPPORTED_VIA_COMPOSITION**
- OA-G2 / EVAL-PROV-002: **DIRECTLY_SUPPORTED**
- OA-G2 / EVAL-CUST-001: **NOT_COVERED**
- OA-G2 / EVAL-CUST-002: **NOT_COVERED**
- OA-G2 / EVAL-INSP-001: **SUPPORTED_VIA_COMPOSITION**
- OA-G2 / EVAL-INSP-002: **NOT_COVERED**
- OA-G2 / EVAL-INSP-003: **DIRECTLY_SUPPORTED**
