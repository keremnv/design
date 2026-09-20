# Benchmark Adaptation

## Source use case

`grain-traceability-v1` instantiates the grain-elevator-to-processor traceability problem described in Ameri, Wallace, Yoder, and Riddick's 2023 NIST publication. It retains the operational setting and question themes while using a new controlled evidence instance.

## Adaptation boundary

The published problem supplies the scenario and competency-question lineage. The operational data in this directory are not copied from the publication and are not a reproduction of its original simulated dataset, RDF graph, ontology, mappings, or queries. They were generated for this experiment and projected from an evaluator-only ledger.

The adaptation adds explicit tests for heterogeneous identifier reconciliation, bulk-material mixing, ownership/custody separation, missing links, ambiguous source accounts, temporal ordering, unresolved candidates, and completeness-sensitive absence. These additions are benchmark extensions, not claims about the scope of the original publication.

## Construction condition

The constructor receives the purpose and ordinary operational evidence only. It is not shown the published question texts, question-to-gold mapping, canonical ledger, reference semantic model, standards URLs, or semantic vocabulary. The evaluator and reference directories are outside the host-visible mount.

## Reference condition

The separate reference model records human decisions about concepts, relations, identity mappings, transformations, derivations, query semantics, and unresolvedness. It is a comparator for deliberate semantic engineering, not a structural target for an eventual World.

## Freeze rule

This benchmark is not revised in response to constructor behavior. Any defect discovered after construction begins requires a new version and a documented change; it may not silently alter `grain-traceability-v1`.
