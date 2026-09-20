from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def tree_hashes(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*')) if p.is_file()}


def main() -> None:
    frozen_inputs = [
        'workload_spec.md', 'development_tasks.json', 'evaluation_tasks.json',
        'gold.json', 'authoring_instruction.txt', 'consumer_instruction.txt',
    ]
    contexts = {
        w: {
            'world_hash': json.loads((ROOT.parent / 'grain-traceability-v1-cursor-grok-medium-20260909/world_context/contexts/context_manifest.json').read_text())[w]['world_hash'],
            'context_path': str(ROOT.parent / 'grain-traceability-v1-cursor-grok-medium-20260909/world_context/contexts' / f'{w}-world-context.md'),
            'context_sha256': json.loads((ROOT.parent / 'grain-traceability-v1-cursor-grok-medium-20260909/world_context/contexts/context_manifest.json').read_text())[w]['renderer_output']['sha256'],
        }
        for w in ('OA-G1', 'OA-G2')
    }
    manifest = {
        'experiment': 'grain-traceability-v1-durable-computation-20260909',
        'benchmark': 'grain-traceability-v1',
        'benchmark_commit': '17e1314f10d8b491b4462f821876a0a42642f1f8',
        'product': {'name': 'Cursor CLI', 'version': '3.19.13', 'model': 'cursor-grok-4.6-medium', 'reasoning': 'medium', 'agent_package': '2026.09.02-c22c1a3'},
        'protocol': {'replicates_per_world_condition': 3, 'conditions': ['SYNOPSIS', 'DURABLE'], 'raw_secondary': False},
        'authoring_instruction': 'authoring_instruction.txt',
        'consumer_instruction': 'consumer_instruction.txt',
        'frozen_input_sha256': {name: sha(ROOT / name) for name in frozen_inputs},
        'contexts': contexts,
        'computation_bundles': {w: tree_hashes(ROOT / 'frozen_application_bundles' / w) for w in ('OA-G1', 'OA-G2')},
        'authoring_run_metadata': {w: json.loads((ROOT / 'application_authoring' / w / 'run.json').read_text()) for w in ('OA-G1', 'OA-G2')},
        'held_out_tasks_hidden_from_authoring': True,
        'gold_hidden_from_authoring_and_consumers': True,
        'frozen_before_consumer_execution': True,
    }
    (ROOT / 'freeze_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
