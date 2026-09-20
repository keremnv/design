# Human semantic specification for the comparator

The reference condition requires deliberate work before querying:

1. Choose referents for inbound portions, outbound shipments, processor receipts, samples, observations, places, bins, trucks, organizations, and processed outputs.
2. Choose event types for receiving, storage movement, loadout, transport, processor receipt, sampling, inspection, title change, custody change, and processing.
3. Define identifiers as context-bound values rather than assuming one universal key.
4. Normalize facility, bin, spout, carrier, and processor aliases.
5. Reconcile carrier bills to mill receiving slips and elevator dispatch references.
6. Preserve the aggregate composition of OUT-5002 with two source contributions.
7. Represent OUT-5004 as a shipment linked to BIN-14 while leaving individual source allocation open.
8. Represent OUT-5003 as a departure-only chain with no processor receipt and no source allocation.
9. Separate source ownership, later title, and custody, each with temporal intervals.
10. Map sample and observation records to material using direct references, alias rules, time, and bounded operational context.
11. Store evidence grounding for each assertion and candidate identity.
12. Implement derivations for event history, location-at-time, upstream/downstream composition, custody and ownership intervals, and completeness-sensitive absence.
13. Define query semantics for the ten standard-backed and ten novel questions, including whether a question requests established answers, candidates, or justified negatives.
14. Declare that a missing link yields `not_established` and that an explicit competing identity remains unresolved.

This list is the human-authored semantic specification being compared with the construction-agent condition. The final World need not contain these names, tables, or relations.
