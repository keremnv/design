# Prior reuse evidence

This report recovers archived experiments that materially compared fresh consumers of native evidence with consumers of a sealed semantic World or Product representation. Results are not pooled across models, domains, or World quality levels.

## Evidence table

| Campaign | Domain and construction | Consumer design | Native sources unavailable in World arm? | Main result | Classification | Important confounds |
|---|---|---|---|---|---|---|
| `frontier_organic_reuse_v1` | Philips regulatory; GPT-5.6 Sol Medium; F1/F2 organically constructed independently from purpose and sources; no evaluator intervention | RAW x2 versus fresh PRODUCT consumers on F1/F2; 8 analyst tasks | Yes; PRODUCT opened 0 native files; RAW opened 17/18/20 | F1/F2 PRODUCT retained RAW load-bearing correctness and avoided false closure; all fresh PRODUCT runs were source-free | CORRECTNESS_PARITY, SOURCE_INDEPENDENCE, SEMANTIC_RECONSTRUCTION_REMOVED, WORK_CHARACTER_SHIFT | N=2 organic Worlds; 4 PRODUCT consumers; conditional on adequate Worlds; not a general model claim |
| `reuse_raw_vs_product_v1` | Philips regulatory; Composer 2.5; PRODUCT was a predetermined/previously constructed C2 World, with secondary R4 | RAW x3 versus PRODUCT x3 on the same 8 tasks | Yes; PRODUCT opened 0 source files; RAW opened 18/10/20 | RAW preserved stronger serial/date positive closures; C2 PRODUCT was conservative because serial mechanisms were present but required compiled catalog rows were empty. Both arms avoided listed false closures | RAW_ADVANTAGE, SOURCE_INDEPENDENCE, SEMANTIC_RECONSTRUCTION_REMOVED, WORK_CHARACTER_SHIFT, INCONCLUSIVE correctness parity | C2 was inadequate for the load-bearing positive task; not an organic-construction result; tool/token counts were not cost measures |
| BOM `llm_world_programming_v1` / `v3` / `composer25` | BOM programming; Worlds were deliberately prepared rather than organically compared in the consumer campaign; 20 isolated GPT-5.6 high runs in v3 and 10 Composer 2.5 runs in composer25 | Fresh agents program analyses against RAW files or compiled World IR | Yes in World arms; v3 reports 0/40 source/repository leaks | v3: RAW 0/20 exact versus WORLD 18/20; Composer campaign: RAW 1/10 versus WORLD 10/10. World gains concentrated in replacement-state/qualification and source-schema reconciliation | WORLD_ADVANTAGE, SOURCE_INDEPENDENCE, SEMANTIC_RECONSTRUCTION_REMOVED, WORK_CHARACTER_SHIFT | Programming benchmark, not natural-language traceability; v3 and Composer results must not be pooled; prior contamination audit in the Composer campaign affects interpretation of some RAW cells |
| `end_to_end_v1` | Harbor towing, seed grants, makerspace checkout; Composer 2.5; Worlds constructed through the end-to-end pipeline, not a clean organic RAW-vs-World construction comparison | RAW and WORLD, 3 consumers per domain, 6 questions/domain | Yes; WORLD had 0 source reads in 18 runs | RAW 36/36 establishable and 18/18 correctly unresolved; WORLD 32/36 establishable, 15/18 correctly unresolved, 3 unsupported closures. WORLD matched or nearly matched in two domains, but was weaker in harbor towing | RAW_ADVANTAGE, SOURCE_INDEPENDENCE, WORK_CHARACTER_SHIFT, SEMANTIC_RECONSTRUCTION_REMOVED | Small task pack; WORLD failures were grain selection, fail-open handling, and consumer reasoning rather than a demonstrated kernel limit |
| `world_read_programming_v1` | BOM; Composer 2.5; accepted Worlds and ordinary SQL/Python read surface | World-only fresh programs, no RAW comparator | Yes; no source reads | 18/18 programs produced correct outputs over the World; multiple analyses reused one World without rebuild | REUSE_WITHOUT_RAW_COMPARATOR, SOURCE_INDEPENDENCE, WORK_CHARACTER_SHIFT | Cannot establish correctness parity or World advantage without a RAW arm |
| `autonomous_world_exploration_v1` | Three domains; Composer 2.5; accepted Worlds, fresh World consumers | World-only E0/E1 exploration arms, 18 runs | Yes; World consumers had no native sources | 18/18 multi-hop and 18/18 novel tasks correct; establishable correctness 39/45 and 40/45 across arms; explicit exploration did not materially improve aggregate correctness | REUSE_WITHOUT_RAW_COMPARATOR, SOURCE_INDEPENDENCE, WORK_CHARACTER_SHIFT, INCONCLUSIVE | No RAW comparator; persistent grain and false-closure errors were consumer-side |
| NPDES `end_to_end_programmability_v0` | Messy regulatory sources compiled into a World; fresh ordinary SQL/Python consumers | Three source-free World consumers | Yes; true source-free isolation in A/B/C | Consumers reused grounded state, preserved unresolved NODI, and applied enrichments without rereading sources or rebuilding | REUSE_WITHOUT_RAW_COMPARATOR, SOURCE_INDEPENDENCE, SEMANTIC_RECONSTRUCTION_REMOVED | No RAW correctness comparator |
| NIH `nih_public_access_v1` | Two independent GPT-5.6 Sol Medium constructors; accepted Worlds | One source-free consumer per sealed World | Yes; no source leaks | H1: 12 fully established, 2 unresolved, 1 partial; H2: 10 fully established, 3 partial, 2 unresolved; no unsupported closure | REUSE_WITHOUT_RAW_COMPARATOR, SOURCE_INDEPENDENCE | No RAW comparator; one evaluator-side read-only sidecar close PermissionError was an artifact defect, not a World mutation |

## What the archive establishes

### A. Can a World retain RAW correctness?

Yes, conditionally. The strongest direct evidence is the Philips frontier campaign: two organically constructed Worlds retained RAW load-bearing consequences in fresh source-free consumers. The BOM and grain results add further parity/advantage cells, while the end-to-end Composer campaign shows that an inadequate World or a weak consumer can be worse than RAW. The defensible claim is conditional on adequate semantic coverage and sound consumer interpretation, not `WORLD >= RAW` universally.

### B. Can a World outperform RAW?

Yes in specific tasks and configurations. The BOM programming campaigns report large World advantages, and some prior World-only programming tasks were easier to execute over compiled semantic relations. These are task- and setup-specific advantages, not a universal accuracy theorem.

### C. Can RAW outperform an inadequate World?

Yes. The Philips C2 PRODUCT arm under-closed compiled serial positives, and the Composer end-to-end campaign had RAW 36/36 versus WORLD 32/36 on establishable answers plus unsupported World closures. This is a central boundary condition.

### D. Has repeated native-source interpretation been eliminated?

Yes operationally in the isolated World arms: Philips frontier, Philips reuse, BOM, end-to-end, NPDES, NIH, and grain all record zero native-source reads for the relevant World/Product consumers. “Eliminated” means the consumer did not reopen the native files; it does not mean the World contains every meaning or that the consumer has no schema-orientation work.

### E. Has work character shifted?

Yes repeatedly. RAW traces perform source discovery, parsing, source-schema interpretation, identifier reconciliation, and source-specific rule reconstruction. World/Product traces perform relation/schema discovery, SQL/Python or semantic querying, grounding inspection, and task reasoning. World consumers can still spend substantial effort learning an independently chosen World schema; fewer tool calls are not the measured claim.

### F. Has prior work compared an organically constructed World with a deliberately engineered reference semantic representation?

Not cleanly. The Philips frontier compared organic Worlds with RAW, not with a conventional engineered reference. Earlier Product arms used predetermined Worlds, not a reference semantic layer. Grain is the first campaign in this corpus with an explicit REFERENCE consumer arm, although its reference instance has the evaluator-materialization caveat documented in the grain comparison report.

## Compact appendix conclusion

Prior research supports: source-free World reuse is repeatable; semantic reconstruction can move out of fresh consumers; an adequate World can preserve RAW consequences and sometimes improve downstream programming; and an inadequate World can be less accurate than RAW. It does not support a general World accuracy superiority claim, a universal cost reduction claim, or a claim that independent Worlds expose a portable common query API.
