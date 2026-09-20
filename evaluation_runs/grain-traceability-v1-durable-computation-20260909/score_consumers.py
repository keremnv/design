from __future__ import annotations

import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUNS = json.loads((ROOT / 'consumer_run_index.json').read_text())
TASK_IDS = [x['task_id'] for x in json.loads((ROOT / 'evaluation_tasks.json').read_text())['tasks']]


def section(text: str, task_id: str) -> str:
    m = re.search(rf'(?ms)^#+\s*{re.escape(task_id)}\b.*?(?=^#+\s*EVAL-|\Z)', text)
    return m.group(0) if m else text


def has(s: str, *terms: str) -> bool:
    low = s.lower()
    return all(t.lower() in low for t in terms)


def verdict(task_id: str, text: str) -> tuple[str, str, bool]:
    s = section(text, task_id)
    low = s.lower()
    unresolved = any(x in low for x in ('unresolved', 'not established', 'not recorded', 'no validated', 'not allocated', 'no mill'))
    if task_id == 'EVAL-SRC-001':
        ok = has(s, 'WB-390', 'EF-18') and ('bin-12' in low or 'north house 12' in low) and unresolved
        return ('CORRECT' if ok else 'PARTIAL', 'named WB-390/EF-18, bin, and unresolved allocation' if ok else 'missing contributor or allocation consequence', unresolved)
    if task_id == 'EVAL-SRC-002':
        ok = has(s, 'PGE-OUT-5003', 'N3', 'EF-18?', 'HFM-E') and ('bin-12' in low or 'north house 12' in low) and any(x in low for x in ('none', 'no established', 'not established', 'no inbound material identity'))
        return ('CORRECT' if ok else 'PARTIAL', 'preserved missing source identity and missing receipt' if ok else 'did not preserve missing linkage', True)
    if task_id == 'EVAL-SRC-003':
        over = bool(re.search(r'established (?:contributing|source|inbound).{0,120}(?:MCR-118|S-52)', s, re.I)) or 'contributing pool' in low
        ok = has(s, 'MCR-118', 'S-52') and ('bin-14' in low or 'south house 14' in low) and unresolved
        if over:
            return ('PARTIAL', 'treated bin occupants as a contributing pool while preserving allocation uncertainty', True)
        return ('CORRECT' if ok else 'PARTIAL', 'preserved bin candidates and unresolved allocation' if ok else 'missing source-bin consequence', True)
    if task_id == 'EVAL-PROV-001':
        ok = has(s, 'PGE-OUT-5002', 'HFM-IN-602', 'FEED-2207', 'WB-390', 'EF-18') and unresolved
        return ('CORRECT' if ok else 'PARTIAL', 'complete path, contributors, output, and unresolved split' if ok else 'incomplete receipt provenance', True)
    if task_id == 'EVAL-PROV-002':
        ok = has(s, 'PGE-OUT-5004', 'HFM-IN-604') and ('no mill' in low or 'not recorded' in low or 'no processing' in low) and unresolved
        return ('CORRECT' if ok else 'PARTIAL', 'receipt path and missing source/process output preserved' if ok else 'incomplete receipt provenance', True)
    if task_id == 'EVAL-CUST-001':
        owner = 'grainlink merchants' in low
        northstar = 'northstar bulk transport' in low
        prairie = 'prairie gate elevator' in low
        if owner and northstar and ('custod' in low or 'holder' in low):
            # The answer is correct only if Northstar is presented as the requested
            # moment's custody consequence, not merely as an alternative caveat.
            if re.search(r'(custod|holder).{0,100}northstar', low) or re.search(r'northstar.{0,100}(custod|holder)', low):
                return ('CORRECT', 'owner and Northstar custody consequence stated', False)
        return ('PARTIAL' if owner and prairie else 'INCORRECT', 'owner correct but ticket-level Prairie Gate custody retained instead of gold movement custody' if owner and prairie else 'missing owner/custody consequence', False)
    if task_id == 'EVAL-CUST-002':
        ok = has(s, 'East Fork Co-op', 'Prairie Gate Elevator') and any(x in low for x in ('owner', 'custodian', 'holder'))
        return ('CORRECT' if ok else 'PARTIAL', 'owner and facility custody stated' if ok else 'intake/storage owner or custody not promoted', False)
    if task_id == 'EVAL-INSP-001':
        ok = has(s, 'PGE-OUT-5002', 'HFM-IN-602', 'FEED-2207') and unresolved
        return ('CORRECT' if ok else 'PARTIAL', 'shipment, receipt, output, and combined-sample uncertainty stated' if ok else 'missing inspection downstream consequence', True)
    if task_id == 'EVAL-INSP-002':
        ok = has(s, 'PGE-OUT-5004', 'HFM-IN-604') and ('no' in low or 'not recorded' in low or 'unresolved' in low)
        return ('CORRECT' if ok else 'PARTIAL', 'shipment/receipt, no output, and source uncertainty stated' if ok else 'did not establish sample downstream path', True)
    if task_id == 'EVAL-INSP-003':
        ok = has(s, 'SMP-UNLISTED', 'N3', 'EF-18?') and any(x in low for x in ('unresolved', 'not established', 'not validated'))
        return ('CORRECT' if ok else 'PARTIAL', 'kept unvalidated route/ticket hint unresolved' if ok else 'closed ambiguous sample identity', True)
    return ('PARTIAL', 'unscored task', unresolved)


def usage(meta: dict) -> dict:
    u = meta['telemetry'].get('usage') or {}
    inp = u.get('inputTokens')
    out = u.get('outputTokens')
    cache = u.get('cacheReadTokens')
    return {'input': inp, 'cached_input': cache, 'noncached_input': inp, 'output': out, 'reported_total': (inp + out) if inp is not None and out is not None else None}


def main() -> None:
    records = []
    for meta in RUNS:
        final = ROOT / 'consumer_runs' / meta['run_id'] / 'final_answer.md'
        text = final.read_text(errors='replace') if final.exists() else ''
        q = {}
        for tid in TASK_IDS:
            v, reason, unres = verdict(tid, text)
            q[tid] = {'verdict': v, 'reason': reason, 'correctly_unresolved_consequence': unres and v == 'CORRECT'}
        u = usage(meta)
        tel = meta['telemetry']
        durable = meta['condition'] == 'DURABLE'
        if durable:
            if tel['application_invocations'] and tel['ad_hoc_semantic_query_actions'] == 0 and not tel['computation_source_reads']:
                reuse = 'PURE_DURABLE'
            elif tel['application_invocations']:
                reuse = 'DURABLE_PLUS_WORLD'
            else:
                reuse = 'WORLD_FALLBACK'
        else:
            reuse = None
        records.append({
            'run_id': meta['run_id'], 'world': meta['world'], 'condition': meta['condition'], 'replicate': meta['replicate'],
            'duration_seconds': meta['duration_seconds'], 'usage': u, 'tool_actions': tel['tool_actions'],
            'sqlite_actions': tel['sqlite_actions'], 'python_actions': tel['python_actions'],
            'application_invocations': tel['application_invocations'], 'ad_hoc_semantic_query_actions': tel['ad_hoc_semantic_query_actions'],
            'catalog_reads': tel['catalog_reads'], 'computation_source_reads': tel['computation_source_reads'],
            'native_source_reads': tel['native_source_reads'], 'reuse_class': reuse, 'questions': q,
        })
    aggregates = {}
    for key in [('OA-G1','SYNOPSIS'),('OA-G1','DURABLE'),('OA-G2','SYNOPSIS'),('OA-G2','DURABLE')]:
        rows = [r for r in records if (r['world'], r['condition']) == key]
        counts = Counter(r['questions'][tid]['verdict'] for r in rows for tid in TASK_IDS)
        aggregates[f'{key[0]}-{key[1]}'] = {
            'runs': len(rows), 'question_counts': dict(counts),
            'mean_input': statistics.mean(r['usage']['input'] for r in rows),
            'mean_output': statistics.mean(r['usage']['output'] for r in rows),
            'mean_reported_total': statistics.mean(r['usage']['reported_total'] for r in rows),
            'mean_tool_actions': statistics.mean(r['tool_actions'] for r in rows),
            'mean_ad_hoc_semantic_queries': statistics.mean(r['ad_hoc_semantic_query_actions'] for r in rows),
            'mean_application_invocations': statistics.mean(r['application_invocations'] for r in rows),
            'mean_duration_seconds': statistics.mean(r['duration_seconds'] for r in rows),
            'native_source_reads': sum(r['native_source_reads'] for r in rows),
            'reuse_classes': dict(Counter(r['reuse_class'] for r in rows if r['reuse_class'])),
        }
    payload = {'experiment': 'grain-traceability-v1-durable-computation-20260909', 'records': records, 'aggregates': aggregates, 'scoring_note': 'Frozen gold was used; CUST-001 remains a scope-sensitive case and is scored against its precommitted gold while flagged in the report.'}
    (ROOT / 'consumer_results.json').write_text(json.dumps(payload, indent=2) + '\n')


if __name__ == '__main__':
    main()
