"""Production Inspect surface for ``config.routes/v1`` sealed Worlds.

Every read takes one exact publication address and opens it read-only. No
caller-supplied IDs are needed to start: :func:`inspect_config_world`
lists everything discoverable. Unknown propositions, subjects, or
incompatible/unsealed addresses fail explicitly.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from ontology_author.config_routes.rules import (
    EVALUATOR_METHOD_ID,
    EVALUATOR_RULE,
    EVALUATOR_VERSION,
    PROFILE_ID,
    evaluator_for_statement,
)
from ontology_author.software_governance import open_governance_world
from ontology_author.software_governance.reads import GovernanceView


def inspect_config_world(world: Path | str) -> dict[str, Any]:
    """Inventory everything discoverable in one exact sealed World."""
    view, address = open_config_world_view(world)
    try:
        subjects = [
            _subject_summary(view, str(row["subject"]))
            for row in view.world.relation_rows("software_subject")
        ]
        propositions = [
            {
                "proposition": str(row["proposition"]),
                "statement": str(row["statement"]),
                "domain_relation": str(row["domain_relation"]),
            }
            for row in view.world.relation_rows("governance_proposition")
        ]
        return {
            "address": address,
            "sealed": True,
            "profile_id": PROFILE_ID,
            "snapshot": _snapshot(view),
            "software_revisions": _software_revisions(view),
            "governance_revisions": _governance_revisions(view),
            "subjects": subjects,
            "propositions": propositions,
            "bindings": [
                {
                    "proposition": str(row["proposition"]),
                    "software_subject": str(row["software_subject"]),
                }
                for row in view.world.relation_rows("governance_binding")
            ],
            "candidates": [
                {
                    "proposition": str(row["proposition"]),
                    "software_subject": str(row["software_subject"]),
                }
                for row in view.world.relation_rows("governance_candidate")
            ],
            "questions": [
                {
                    "proposition": str(row["proposition"]),
                    "state": str(row["state"]),
                    "question": str(row["question"]),
                }
                for row in view.world.relation_rows("governance_question")
            ],
            "coverage": view.completeness(),
        }
    finally:
        view.world.close()


def inspect_proposition(world: Path | str, proposition: str) -> dict[str, Any]:
    """Explain one proposition: meaning, source, concern, and judgeability."""
    view, address = open_config_world_view(world)
    try:
        try:
            inspected = view.inspect_governance_proposition(proposition)
        except KeyError:
            raise ValueError(f"unknown proposition {proposition!r} in {address}") from None
        detail = view.binding_candidates_for_proposition(proposition)
        status, route_id, reason = evaluator_for_statement(
            inspected["statement"], inspected.get("establishment_rule") or ""
        )
        evaluator: dict[str, Any] = {
            "status": status,
            "route_id": route_id,
        }
        if status == "covered":
            evaluator.update({
                "method_id": EVALUATOR_METHOD_ID,
                "version": EVALUATOR_VERSION,
                "rule": dict(EVALUATOR_RULE),
            })
        else:
            evaluator["reason"] = reason
        return {
            "address": address,
            "proposition": proposition,
            "statement": inspected["statement"],
            "domain_relation": inspected["domain_relation"],
            "establishment_rule": inspected.get("establishment_rule"),
            "profile_id": inspected.get("profile_id"),
            "evidence": inspected["evidence"],
            "source_revisions": sorted({
                str(item["native_handle"]).rsplit("@sha256:", 1)[1]
                for item in inspected["evidence"]
                if "@sha256:" in str(item["native_handle"])
            }),
            "bound_subjects": detail["established_subjects"],
            "candidates": detail["candidates"],
            "questions": detail["questions"],
            "evaluator": evaluator,
            "coverage": view.completeness(),
        }
    finally:
        view.world.close()


def inspect_subject(world: Path | str, subject: str) -> dict[str, Any]:
    """Explain one software subject without implying cross-World continuity."""
    view, address = open_config_world_view(world)
    try:
        receipts = [
            row for row in view.world.relation_rows("software_subject")
            if str(row["subject"]) == subject
        ]
        if len(receipts) != 1:
            raise ValueError(f"unknown software subject {subject!r} in {address}")
        receipt = receipts[0]
        candidate_propositions = sorted({
            str(row["proposition"])
            for row in view.world.relation_rows("governance_candidate")
            if str(row["software_subject"]) == subject
        })
        bound = view.propositions_for_subject(subject)
        involved = sorted(set(bound) | set(candidate_propositions))
        questions = [
            {
                "proposition": str(row["proposition"]),
                "state": str(row["state"]),
                "question": str(row["question"]),
            }
            for row in view.world.relation_rows("governance_question")
            if str(row["proposition"]) in involved
        ]
        return {
            "address": address,
            "subject": subject,
            "identity_scope": "snapshot-local; no cross-publication continuity",
            "snapshot": str(receipt["snapshot"]),
            "kind": str(receipt["kind"]),
            "producer": f"{receipt['capability']}/{receipt['version']}",
            "mechanical_facts": view.mechanical_facts_for_subject(subject),
            "manifestation": view.local_manifestation_for_subject(subject),
            "bound_propositions": bound,
            "candidate_propositions": candidate_propositions,
            "questions": questions,
        }
    finally:
        view.world.close()


def inspect_binding(
    world: Path | str, proposition: str, subject: str
) -> dict[str, Any]:
    """Answer why proposition P concerns subject S from retained evidence."""
    view, address = open_config_world_view(world)
    try:
        try:
            binding = view.inspect_governance_binding(proposition, subject)
        except KeyError:
            raise ValueError(
                f"no established binding {proposition!r} to {subject!r} in {address}"
            ) from None
        binding["address"] = address
        return binding
    finally:
        view.world.close()


def open_config_world_view(world: Path | str) -> tuple[GovernanceView, str]:
    """Open one exact sealed config.routes World read-only, or raise."""
    target = Path(world)
    if not target.exists():
        raise ValueError(f"world address does not exist: {target}")
    database = target / "world.sqlite" if target.is_dir() else target
    if not database.is_file():
        raise ValueError(f"world address has no world.sqlite: {target}")
    bundle = database.parent
    if bundle.stat().st_mode & 0o222 or database.stat().st_mode & 0o222:
        raise ValueError(f"world address is not sealed (writable): {target}")
    try:
        view = open_governance_world(bundle)
    except Exception as exc:
        raise ValueError(f"world address is not a readable World: {exc}") from exc
    try:
        for relation in (
            "governance_proposition",
            "governance_binding",
            "software_subject",
        ):
            try:
                view.world.relation_schema(relation)
            except Exception:
                raise ValueError(
                    f"world address is not a Software Governance World: {target}"
                ) from None
        receipts = list(view.world.relation_rows("software_subject"))
        if not any(
            str(row["capability"]) == "config.routes" and str(row["version"]) == "v1"
            for row in receipts
        ):
            raise ValueError(
                f"world address is not a {PROFILE_ID} World: {target}"
            )
    except Exception:
        view.world.close()
        raise
    return view, str(bundle.resolve())


def database_fingerprint(world: Path | str) -> str:
    """SHA-256 of the sealed ``world.sqlite`` bytes at one exact address.

    This authenticates exactly the relational database bytes — not the
    retained evidence blobs beside it. Blob integrity is checked per item:
    every reconstruction verifies the blob's SHA-256 against the digest in
    its handle, and guarded Judgment refuses any Case whose relied support
    is not ``OK``. Sidecars such as ``world.admission.json`` are read by
    neither Inspect nor Judge and are outside the authenticated set.
    """
    target = Path(world)
    database = target / "world.sqlite" if target.is_dir() else target
    return hashlib.sha256(database.read_bytes()).hexdigest()


def _subject_summary(view: GovernanceView, subject: str) -> dict[str, str]:
    receipt = next(
        row for row in view.world.relation_rows("software_subject")
        if str(row["subject"]) == subject
    )
    route = next(
        (
            row for row in view.world.relation_rows("config_route")
            if str(row["subject"]) == subject
        ),
        None,
    )
    summary = {
        "subject": subject,
        "snapshot": str(receipt["snapshot"]),
        "kind": str(receipt["kind"]),
        "producer": f"{receipt['capability']}/{receipt['version']}",
    }
    if route is not None:
        summary.update({
            "route_id": str(route["record_id"]),
            "path": str(route["path"]),
            "handler": str(route["handler"]),
        })
    return summary


def _snapshot(view: GovernanceView) -> str:
    snapshots = {
        str(row["snapshot"]) for row in view.world.relation_rows("software_subject")
    }
    return next(iter(sorted(snapshots))) if len(snapshots) == 1 else ""


def _software_revisions(view: GovernanceView) -> list[str]:
    return _revisions_for_relation(view, "software_subject")


def _governance_revisions(view: GovernanceView) -> list[str]:
    return _revisions_for_relation(view, "governance_proposition")


def _revisions_for_relation(view: GovernanceView, relation: str) -> list[str]:
    store = view.world._inner._store
    revisions: set[str] = set()
    for row in view.world.relation_rows(relation):
        values = {str(key): row[key] for key in row}
        try:
            assertion_id = store.assertion_id_for_tuple(relation, values)
            warrant = view.world.warrant_for_assertion(assertion_id)
        except (KeyError, ValueError):
            continue
        for base in warrant["bases"]:
            detail = base.get("detail")
            if not isinstance(detail, dict):
                continue
            for item in detail.get("observations") or []:
                if isinstance(item, dict) and item.get("source_revision"):
                    revisions.add(str(item["source_revision"]))
    return sorted(revisions)
