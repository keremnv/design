from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def main() -> None:
    audit = json.loads((ROOT / 'direct_computation_audit.json').read_text())['results']
    consumer = json.loads((ROOT / 'consumer_results.json').read_text())
    ag = consumer['aggregates']
    author = {w: json.loads((ROOT / 'application_authoring' / w / 'run.json').read_text())['stream_usage_events'][-1]['usage'] for w in ('OA-G1', 'OA-G2')}

    audit_lines = [
        '# Direct held-out computation audit', '',
        'The frozen bundles were executed on all ten held-out parameter instances. No native evidence, network, LLM, or World mutation was available to the computations. Author-only test fixtures were excluded from the consumer-visible bundles.', '',
        '| World | Directly supported | Supported via composition | Not covered | Incorrect | Unsupported closure |',
        '| --- | ---: | ---: | ---: | ---: | ---: |',
    ]
    for w in ('OA-G1', 'OA-G2'):
        rows = [x for x in audit if x['world'] == w]
        c = {k: sum(x['classification'] == k for x in rows) for k in ('DIRECTLY_SUPPORTED','SUPPORTED_VIA_COMPOSITION','NOT_COVERED','INCORRECT','UNSUPPORTED_CLOSURE')}
        audit_lines.append(f"| {w} | {c['DIRECTLY_SUPPORTED']} | {c['SUPPORTED_VIA_COMPOSITION']} | {c['NOT_COVERED']} | {c['INCORRECT']} | {c['UNSUPPORTED_CLOSURE']} |")
    audit_lines += ['', 'The repeated uncovered cases are custody-at-time propagation and the South House 14 inspection-to-receipt consequence. The former is scope-sensitive: the World has a ticket-scoped holder record and a movement-scoped Northstar handoff, while the held-out gold asks for a material-level answer. The latter relies on treating “South House 14 cargo” as the later HFM-IN-604 movement; conservative refusal is defensible because the sample does not name that receipt. These are retained as frozen evaluator outcomes, not repaired.', '', '### Holdout integrity caveat', '', 'The development task file and gold were physically excluded from authoring workspaces, and the frozen consumer bundles contain no evaluator-task IDs, gold, or held-out answer tables. The Worlds themselves contain all operational identifiers, however, and the authoring hosts were permitted to inspect them freely. OA-G2’s author-only test fixture consequently exercised several held-out-looking parameter values. Those test fixtures were preserved as authoring artifacts but excluded from the frozen consumer-visible bundle. This preserves computation-shape testing rather than answer caching, but strict parameter-value blindness is not claimed.', '', '### Per-instance classifications', '']
    for x in audit:
        audit_lines.append(f"- {x['world']} / {x['task_id']}: **{x['classification']}**")
    (ROOT / 'direct_computation_audit.md').write_text('\n'.join(audit_lines) + '\n')

    def row(key: str) -> dict:
        return ag[key]
    lines = ['# Fresh held-out consumer results', '', 'Three fresh Cursor CLI consumers were run per World and condition. Native evidence was physically unavailable in all twelve workspaces; native-source reads were zero.', '', '| Metric | OA-G1 Synopsis | OA-G1 Durable | OA-G2 Synopsis | OA-G2 Durable |', '| --- | ---: | ---: | ---: | ---: |']
    for label, fn in [
        ('Correct', lambda x: x['question_counts'].get('CORRECT', 0)),
        ('Partial', lambda x: x['question_counts'].get('PARTIAL', 0)),
        ('Unsupported closure', lambda x: 0),
        ('Mean input tokens', lambda x: round(x['mean_input'], 1)),
        ('Mean reported total', lambda x: round(x['mean_reported_total'], 1)),
        ('Mean tool actions', lambda x: round(x['mean_tool_actions'], 2)),
        ('Mean ad hoc semantic queries', lambda x: round(x['mean_ad_hoc_semantic_queries'], 2)),
        ('Mean computation invocations', lambda x: 'n/a' if 'Synopsis' in label else round(x['mean_application_invocations'], 2)),
    ]:
        vals = [('n/a' if label == 'Mean computation invocations' and 'SYNOPSIS' in k else fn(row(k))) for k in ('OA-G1-SYNOPSIS','OA-G1-DURABLE','OA-G2-SYNOPSIS','OA-G2-DURABLE')]
        lines.append('| ' + label + ' | ' + ' | '.join(map(str, vals)) + ' |')
    lines += ['', '## Per-run results', '']
    lines.append('| Run | Condition | Correct | Partial | Input | Output | Reported total | Tools | Ad hoc queries | App invocations | Reuse class |')
    lines.append('| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |')
    for r in consumer['records']:
        counts = {v: sum(x['verdict'] == v for x in r['questions'].values()) for v in ('CORRECT','PARTIAL')}
        u = r['usage']
        lines.append(f"| {r['run_id']} | {r['condition']} | {counts['CORRECT']} | {counts['PARTIAL']} | {u['input']} | {u['output']} | {u['reported_total']} | {r['tool_actions']} | {r['ad_hoc_semantic_query_actions']} | {r['application_invocations']} | {r['reuse_class'] or 'n/a'} |")
    lines += ['', 'All durable runs adopted the bundle at least once, but all were `DURABLE_PLUS_WORLD`: they invoked computations and also inspected the World or authored additional semantic queries. No run qualified as `PURE_DURABLE`; no run was `WORLD_FALLBACK`.', '', 'The gold-sensitive partials are concentrated in ownership/custody scope and South House 14 inspection linkage. No unsupported closure was observed in manual review.', '']
    (ROOT / 'consumer_results.md').write_text('\n'.join(lines))

    token_lines = ['# Application-layer token amortization', '', 'Cursor result usage supplied `inputTokens`, `outputTokens`, `cacheReadTokens`, and `cacheWriteTokens`. No separate reasoning-output or provider-certified non-cached-input field was present, so this report does not derive a billable/non-cached sensitivity curve. Reported total is the descriptive sum `inputTokens + outputTokens`, matching the prior experiment’s descriptive convention but not a billing receipt.', '', '| World | Author input | Author output | Author reported total | Synopsis mean total | Durable mean total | Durable mean input | Synopsis mean input | Break-even total n |', '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    curves = {}
    for w in ('OA-G1','OA-G2'):
        au = author[w]
        s = row(f'{w}-SYNOPSIS'); d = row(f'{w}-DURABLE')
        author_total = au['inputTokens'] + au['outputTokens']
        diff = s['mean_reported_total'] - d['mean_reported_total']
        be = author_total / diff if diff > 0 else None
        linestr = f"| {w} | {au['inputTokens']} | {au['outputTokens']} | {author_total} | {s['mean_reported_total']:.1f} | {d['mean_reported_total']:.1f} | {d['mean_input']:.1f} | {s['mean_input']:.1f} | {be:.2f} |" if be is not None else f"| {w} | {au['inputTokens']} | {au['outputTokens']} | {author_total} | {s['mean_reported_total']:.1f} | {d['mean_reported_total']:.1f} | {d['mean_input']:.1f} | {s['mean_input']:.1f} | none |"
        token_lines.append(linestr)
        curves[w] = {'author_reported_total': author_total, 'synopsis_mean_reported_total': s['mean_reported_total'], 'durable_mean_reported_total': d['mean_reported_total'], 'synopsis_mean_input': s['mean_input'], 'durable_mean_input': d['mean_input'], 'break_even_n': be, 'values': {}}
        for n in (1,2,5,10,25,100):
            curves[w]['values'][str(n)] = {'synopsis': n*s['mean_reported_total'], 'durable': author_total+n*d['mean_reported_total']}
    token_lines += ['', '## Curves', '']
    token_lines.append('| n | OA-G1 Synopsis | OA-G1 Durable | OA-G2 Synopsis | OA-G2 Durable |')
    token_lines.append('| ---: | ---: | ---: | ---: | ---: |')
    for n in (1,2,5,10,25,100):
        token_lines.append(f"| {n} | {curves['OA-G1']['values'][str(n)]['synopsis']:.1f} | {curves['OA-G1']['values'][str(n)]['durable']:.1f} | {curves['OA-G2']['values'][str(n)]['synopsis']:.1f} | {curves['OA-G2']['values'][str(n)]['durable']:.1f} |")
    token_lines += ['', 'OA-G1 durable consumers used more reported tokens than synopsis consumers, so there is no break-even. OA-G2 durable consumers used slightly fewer reported tokens than synopsis consumers; the one-time application authoring cost yields an empirical break-even of approximately 64.9 repeated uses. This is descriptive token amortization only, not monetary amortization.', '']
    (ROOT / 'token_amortization.md').write_text('\n'.join(token_lines))
    (ROOT / 'token_amortization.json').write_text(json.dumps({'authoring_usage': author, 'curves': curves, 'telemetry_semantics': {'reported_total': 'inputTokens + outputTokens', 'noncached_input': 'unavailable for Cursor provider result', 'reasoning_output': 'unavailable'}, 'verdict': 'PARTIALLY_SUPPORTED'}, indent=2) + '\n')

    prior = json.loads((ROOT.parent / 'grain-traceability-v1-world-context-20260909/results.json').read_text())['records']
    prior_summary = {}
    for w in ('OA-1','OA-2'):
        for c in ('DISCOVERY','SYNOPSIS'):
            rs = [x for x in prior if x['world'] == w and x['condition'] == c]
            prior_summary[f'{w}-{c}'] = {'mean_input': statistics.mean(x['usage']['input_tokens'] for x in rs), 'mean_total': statistics.mean(x['usage']['reported_total_tokens'] for x in rs), 'mean_tools': statistics.mean(x['tool_actions'] for x in rs)}
    final = ['# Final findings', '', '## Experiment identity', '', '- Experiment: `grain-traceability-v1-durable-computation-20260909`.', '- Product: Cursor CLI 3.19.13, `cursor-grok-4.6-medium`, medium reasoning; agent package `2026.09.02-c22c1a3`.', '- Benchmark and sealed World inputs remain unchanged. The prior GPT-6-Astra artifacts were used only as historical comparators.', '', '## Main result', '', 'The computation-authoring boundary generalized imperfectly but usefully. Both bundles exposed the four requested computation families and were invoked by every durable consumer. However, durable consumers still inspected the World and wrote ad hoc semantic queries. OA-G2 showed a small consumer-token reduction relative to synopsis, while OA-G1 did not; therefore the primary token result is representation-dependent in this small workload.', '', '## Grok result table', '', '| Metric | OA-G1 Synopsis | OA-G1 Durable | OA-G2 Synopsis | OA-G2 Durable |', '| --- | ---: | ---: | ---: | ---: |']
    for label, key in [('Correct','question_counts'),('Partial','question_counts'),('Mean input tokens','mean_input'),('Mean reported total','mean_reported_total'),('Mean tools','mean_tool_actions'),('Mean ad hoc semantic queries','mean_ad_hoc_semantic_queries'),('Mean computation invocations','mean_application_invocations')]:
        vals=[]
        for k in ('OA-G1-SYNOPSIS','OA-G1-DURABLE','OA-G2-SYNOPSIS','OA-G2-DURABLE'):
            x=ag[k]
            vals.append(x['question_counts'].get(label.upper(),0) if label in ('Correct','Partial') else ('n/a' if label=='Mean computation invocations' and 'SYNOPSIS' in k else round(x[key],2)))
        final.append('| '+label+' | '+' | '.join(map(str,vals))+' |')
    final += ['', '## GPT-6-Astra comparison where available', '', 'The earlier GPT-6-Astra World-context experiment used a different downstream question set and no durable computation bundle, so it is not a matched causal comparison. Its historical three-run means were:', '', '| Historical condition | Mean input | Mean reported total | Mean tools |', '| --- | ---: | ---: | ---: |']
    for k,v in prior_summary.items(): final.append(f"| GPT-6-Astra {k} | {v['mean_input']:.1f} | {v['mean_total']:.1f} | {v['mean_tools']:.2f} |")
    final += ['', 'Cursor/Grok durable mean reported totals were 143,058.7 for OA-G1 and 134,229.7 for OA-G2; matched current synopsis means were 134,688.7 and 137,867.0. The Grok current workload is not numerically pooled with the GPT-6-Astra historical workload because task wording and World lineage differ.', '', '## Frozen judgments', '', '- DURABLE COMPUTATION GENERALIZATION: **PARTIALLY_SUPPORTED**. Both bundles generalized across held-out parameters, but both had uncovered application consequences and several output-shape limitations.', '- SEMANTIC NON-INFERIORITY: **INDETERMINATE**. OA-G1 preserved its synopsis count; OA-G2 declined from 28/30 to 25/30 under the frozen heuristic audit, while several partials are scope-sensitive.', '- CONSUMER TOKEN REDUCTION: **PARTIALLY_SUPPORTED**. OA-G2 reduced mean reported total by about 2.6%; OA-G1 increased it by about 6.2%.', '- AD HOC QUERY REDUCTION: **SUPPORTED** as a directional process result: mean ad hoc semantic-query actions fell from 5.00 to 2.00 for OA-G1 and 3.67 to 2.67 for OA-G2, but did not reach zero.', '- APPLICATION-LEVEL TOKEN AMORTIZATION: **PARTIALLY_SUPPORTED**. No OA-G1 break-even; OA-G2 break-even is about 64.9 repeated uses under reported-total accounting.', '- REPRESENTATION-INDEPENDENT REUSE: **PARTIALLY_SUPPORTED**. Both schemas accepted and executed durable computations, but the token benefit appeared only for OA-G2.', '- KERNEL PRESSURE: **NONE**. All required computation outputs were representable as ordinary parameterized programs over read-only SQLite Worlds; observed gaps are authoring/interface/evaluator-scope issues.', '', '## Interpretation boundary', '', 'The frozen gold contains at least two scope-sensitive obligations. `CUST-001` asks for Northstar custody of WB-390 although the evidence records Northstar custody for aggregate OUT-5002 and leaves individual quantity allocation unresolved. `CUST-002` promotes intake owner and physical storage into a point-in-time custody result without a covering ownership event. `SMP-604Q` similarly links “South House 14 cargo” to HFM-IN-604 by path/timing rather than an explicit sample-to-receipt identifier. These remain frozen scoring outcomes and are disclosed rather than used to repair the experiment.', '', '## Holdout integrity caveat', '', 'The held-out task file and gold were physically hidden from authoring and consumer hosts, and the frozen bundles contain no held-out literals or answer maps. Because authoring hosts could inspect their complete Worlds, they could infer and test some held-out-looking identifiers; OA-G2’s author-only tests did so. Those tests were excluded from the consumer-visible bundles. The experiment therefore supports computation-shape reuse, but not a stronger claim of strict parameter-value blindness.', '', '## Reuse-history boundary', '', 'The preserved execution receipts contain development, direct held-out audit, and durable-consumer invocation records. They are not exposed to any consumer. The history is sufficient for a future experiment on capability/history discovery, which was not run here.', '']
    (ROOT / 'final_findings.md').write_text('\n'.join(final))

    # Hash all frozen experiment artifacts and result outputs, excluding this hash file.
    paths = [p for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name != 'output_hashes.sha256' and '__pycache__' not in p.parts]
    (ROOT / 'output_hashes.sha256').write_text('\n'.join(f'{sha(p)}  {p.relative_to(ROOT)}' for p in paths) + '\n')


if __name__ == '__main__':
    main()
