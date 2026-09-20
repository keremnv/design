# Evaluation specification

## Unit of evaluation

The unit is a semantic consequence, not an exact string. A submission may use different identifiers, tables, relation names, or reasoning paths if it yields the same established consequences and preserves the adjudicated uncertainty.

For each hidden question, score four dimensions:

1. **Answer coverage** — expected established tuples are returned or are computably available.
2. **Evidence grounding** — each committed tuple can be tied to host-visible records.
3. **Unresolvedness** — underdetermined or unsupported candidates remain marked as such rather than being silently merged.
4. **Completeness discipline** — absence is treated as a negative only inside an explicit complete scope.

Suggested per-consequence labels are `correct_established`, `correct_unresolved`, `correct_not_recorded`, `unsupported_closure`, `missing`, and `contradicted`. The evaluator may report micro-averages and question-level pass rates; the precommitted gold files define the admissible consequence set.

## Acceptable representation variation

- Local aliases may be normalized to the same referent when the evidence basis supports the mapping.
- A source may return a canonical identifier, host identifier, or both.
- Interval endpoints may use an explicitly declared open/closed convention.
- A response may include more provenance context than the gold answer if it does not assert unsupported facts.
- A reference model is not a structural target. Shape, vocabulary, and graph layout are not scored.

## Unsupported closure

Unsupported closure includes silently choosing one of the two Meadow Creek accounts, treating the question-marked `N3 / EF-18?` note as a source identity, allocating all South House 14 output to one inbound receipt, inventing a processor receipt for OUT-5003, or turning absence in an incomplete HFM-E extract into a negative fact.

## Readiness gate

The benchmark is frozen only if the validation script reports zero structural errors, every gold answer has evidence basis, every unresolved consequence is supported by a host-visible gap or conflict, no host-visible file contains evaluator/reference paths or standards terminology, and all host-visible file hashes are recorded.
