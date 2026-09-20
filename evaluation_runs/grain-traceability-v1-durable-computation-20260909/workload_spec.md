# Grain traceability durable-computation workload

This is a separately versioned evaluator layer over the sealed `grain-traceability-v1` Worlds. It does not modify the benchmark or either World.

The workload tests whether application-specific deterministic computations authored once over a sealed World generalize from visible development parameter instances to held-out parameter instances.

## Operation families

The workload uses four recurring application operations:

1. Determine the material-source status of an outbound dispatch, preserving blended or missing source allocation as unresolved.
2. Summarize upstream provenance for a processor receipt, including downstream processing and unresolved upstream allocation.
3. Determine owner and custodian for a material at a supplied timestamp.
4. Determine the downstream scope of an inspection sample, including receipt, processing output, and unresolved attribution.

These are parameterized semantic computations, not cached benchmark answers. Development and held-out parameter values are disjoint within each family.

## Evidence discipline

Gold was adjudicated against the frozen host-visible evidence, not canonical truth alone. In particular, the 26,000 kg `WB-390 / EF-18` blended movement does not uniquely establish a 15,000 kg / 11,000 kg split, so the durable workload expects contributor identities while preserving individual quantity allocation as unresolved.

The held-out workload includes underdetermined cases. A correct computation may return an explicit unresolved result; it must not manufacture an identity or allocation.

## Conditions

One Cursor CLI authoring context receives each sealed World, its deterministic synopsis, the frozen purpose, and development tasks only. Fresh held-out consumers receive the synopsis and held-out tasks either with no application bundle (`SYNOPSIS`) or with the frozen computation bundle and catalog (`DURABLE`).

## Frozen protocol

The computation author may choose names, SQL/Python structure, and composition. Computations must be deterministic, parameterized, World-bound, source-independent, network-free, and free of evaluator-task or gold leakage. Held-out tasks and gold are physically excluded from authoring workspaces.
