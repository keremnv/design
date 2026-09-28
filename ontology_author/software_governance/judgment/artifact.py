"""Judgment artifacts live outside the sealed Construction World."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ARTIFACT_FIELDS = (
    "case_id",
    "world_id",
    "revision",
    "method",
    "applicability",
    "program_findings",
    "conformance",
    "context_requests",
)


def method_record(
    *,
    method_id: str,
    version: str,
    rule: dict[str, Any],
    implementation_source: str,
) -> dict[str, Any]:
    """Identify one evaluator without hashing paths or timestamps.

    ``implementation_source`` is the evaluator function source. ``rule`` is
    the parameter record copied into the artifact. Both enter the fingerprint.
    """

    payload = json.dumps(
        {
            "id": method_id,
            "implementation": implementation_source.strip(),
            "rule": rule,
            "version": version,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "id": method_id,
        "version": version,
        "fingerprint": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "rule": rule,
    }


def artifact_shell(
    case: dict[str, Any],
    *,
    method: dict[str, Any],
    applicability: dict[str, Any],
    program_findings: list[dict[str, Any]],
    conformance: dict[str, Any] | None,
    context_requests: list[dict[str, Any]],
) -> dict[str, Any]:
    artifact = {
        "case_id": case["case_id"],
        "world_id": case["world_id"],
        "revision": case["revision"],
        "method": method,
        "applicability": applicability,
        "program_findings": program_findings,
        "conformance": conformance,
        "context_requests": context_requests,
    }
    missing = [field for field in ARTIFACT_FIELDS if field not in artifact]
    if missing:
        raise KeyError(missing)
    return artifact


def write_artifact(path: Path, artifact: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_artifact(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def consumer_reads(case: dict[str, Any], artifact: dict[str, Any]) -> dict[str, Any]:
    """Answer the judgment questions from the case and the artifact."""

    propositions = [fact for fact in case["facts"] if fact["relation"] == "governance_proposition"]
    subjects = [fact for fact in case["facts"] if fact["relation"] == "software_subject"]
    cited = [
        assertion_id
        for finding in artifact["program_findings"]
        for assertion_id in finding["assertion_ids"]
    ]
    return {
        "proposition": [row["values"]["statement"] for row in propositions],
        "subject": [row["values"]["subject"] for row in subjects],
        "applicability": artifact["applicability"],
        "program_findings": artifact["program_findings"],
        "finding_evidence": [_fact_by_assertion(case, assertion_id) for assertion_id in cited],
        "conformance": artifact["conformance"],
        "method": artifact["method"],
        "unknown": {
            "applicability": artifact["applicability"]["result"] == "UNKNOWN",
            "conformance": (artifact["conformance"] or {}).get("result") == "UNKNOWN",
            "requests": artifact["context_requests"],
        },
        "context_requests": artifact["context_requests"],
        "world": {
            "world_id": artifact["world_id"],
            "revision": artifact["revision"],
            "address": case["world_address"],
        },
    }


def _fact_by_assertion(case: dict[str, Any], assertion_id: str) -> dict[str, Any]:
    matches = [fact for fact in case["facts"] if fact["assertion_id"] == assertion_id]
    if len(matches) != 1:
        raise KeyError(assertion_id)
    return matches[0]
