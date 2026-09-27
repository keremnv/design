"""Reads over a sealed Software Governance World.

Acceptance navigation uses these functions. It does not issue SQL.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from ontology_author.evidence.program_source import (
    program_source_observations,
    reconstruct_program_observation,
)
from ontology_author.software_governance.evidence import reconstruct_governance_observation
from ontology_author.software_governance.validation import BINDINGS_CAPABILITY
from ontology_author.world.runtime.world import ConstructionWorld

CALL_CAPABILITY = "spine.calls/v1"
SOURCE_MANIFESTATION_SCHEME = "source-token-range"
SOURCE_MANIFESTATION_CAPABILITY = "spine.source_evidence/v1"


class GovernanceView:
    def __init__(self, world: ConstructionWorld) -> None:
        self.world = world

    def propositions_for_subject(self, subject: str) -> list[str]:
        return sorted(
            str(row["proposition"])
            for row in self.world.relation_rows("governance_binding")
            if row["software_subject"] == subject
        )

    def subjects_for_proposition(self, proposition: str) -> list[str]:
        return sorted(
            str(row["software_subject"])
            for row in self.world.relation_rows("governance_binding")
            if row["proposition"] == proposition
        )

    def inspect_governance_proposition(self, proposition: str) -> dict[str, Any]:
        rows = [
            row for row in self.world.relation_rows("governance_proposition")
            if row["proposition"] == proposition
        ]
        if len(rows) != 1:
            raise KeyError(proposition)
        row = rows[0]
        basis = _basis(self.world, "governance_proposition", dict(row))
        return {
            "proposition": proposition,
            "statement": str(row["statement"]),
            "domain_relation": str(row["domain_relation"]),
            "evidence": basis["evidence"],
            "construction_method": basis["construction_method"],
            "origin": basis["origin"],
            "establishment_rule": basis["extra"].get("establishment_rule"),
            "profile_id": basis["extra"].get("profile_id"),
            "semantic_subject": self.semantic_subject_for(proposition),
        }

    def inspect_governance_binding(self, proposition: str, subject: str) -> dict[str, Any]:
        values = {"proposition": proposition, "software_subject": subject}
        rows = [
            row for row in self.world.relation_rows("governance_binding")
            if row["proposition"] == proposition and row["software_subject"] == subject
        ]
        if len(rows) != 1:
            raise KeyError((proposition, subject))
        basis = _basis(self.world, "governance_binding", values)
        return {
            "proposition": proposition,
            "software_subject": subject,
            "evidence": basis["evidence"],
            "construction_method": basis["construction_method"],
            "origin": basis["origin"],
            "relation_support": basis["extra"].get("relation_support"),
            "endpoint_resolution": basis["extra"].get("endpoint_resolution"),
            "software_evidence": basis["extra"].get("software_evidence"),
            "establishment_rule": basis["extra"].get("establishment_rule"),
            "contract": basis["extra"].get("contract"),
            "profile_id": basis["extra"].get("profile_id"),
            "subject_manifestation": self.local_manifestation_for_subject(subject),
            "roles": sorted(values),
        }

    def binding_candidates_for_proposition(self, proposition: str) -> dict[str, Any]:
        candidates = []
        for row in self.world.relation_rows("governance_candidate"):
            if row["proposition"] != proposition:
                continue
            values = {
                "proposition": proposition,
                "software_subject": str(row["software_subject"]),
            }
            basis = _basis(self.world, "governance_candidate", values)
            candidates.append({
                "software_subject": values["software_subject"],
                "label": _label(self.world, values["software_subject"]),
                "relation_support": basis["extra"].get("relation_support"),
                "endpoint_resolution": basis["extra"].get("endpoint_resolution"),
                "construction_method": basis["construction_method"],
                "establishment_rule": basis["extra"].get("establishment_rule"),
                "software_evidence": basis["extra"].get("software_evidence"),
                "origin": basis["origin"],
                "evidence": basis["evidence"],
            })
        questions = [
            {"state": str(row["state"]), "question": str(row["question"])}
            for row in self.world.relation_rows("governance_question")
            if row["proposition"] == proposition
        ]
        return {
            "proposition": proposition,
            "candidates": candidates,
            "questions": questions,
            "established_subjects": self.subjects_for_proposition(proposition),
        }

    def local_manifestation_for_subject(self, subject: str) -> dict[str, Any]:
        """Recover a manifestation from a producer receipt or a source byte range.

        A ``software_manifestation`` row supplies its own scheme, location,
        and capability. The content is the reconstructed grounding, and the
        digest is computed from that content. A single program source range
        still uses the source-token-range scheme. Anything else is
        ``NOT_PRODUCED``.
        """

        recorded = _recorded_manifestation(self.world, subject)
        if recorded is not None:
            return recorded
        producer = _producer(self.world, subject)
        observations = program_source_observations(self.world, subject)
        if len(observations) != 1:
            return _manifestation_not_produced(subject, producer)
        observation = observations[0]
        text, status = reconstruct_program_observation(self.world, observation)
        if status != "OK":
            return _manifestation_not_produced(subject, producer)
        handle = str(observation["native_handle"])
        file_digest = handle.rsplit("@sha256:", 1)[-1] if "@sha256:" in handle else ""
        return {
            "subject": subject,
            "status": "OK",
            "scheme": SOURCE_MANIFESTATION_SCHEME,
            "content": text,
            "content_digest": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "location": str(observation["native_location"]),
            "file_digest": file_digest,
            "producer": producer,
            "capability": SOURCE_MANIFESTATION_CAPABILITY,
        }

    def program_relations_for_subject(self, subject: str) -> dict[str, Any]:
        """Spine call relations when that producer emitted them.

        A world without those relations has no invocation graph. Emptiness
        here is not a missing governance binding.
        """

        invokes = []
        if _roles(self.world, "program_invokes") is not None:
            for row in self.world.query(
                "SELECT _assertion_id, call_site_id, target_id FROM program_invokes"
            ):
                call_site = str(row["call_site_id"])
                target = str(row["target_id"])
                if call_site != subject and target != subject:
                    continue
                invokes.append({
                    "call_site": call_site,
                    "target": target,
                    "target_label": _label(self.world, target),
                    "origin": self.world.origins_for_assertion(str(row["_assertion_id"])),
                })
        resolutions = []
        if _roles(self.world, "program_resolution") is not None:
            resolutions = [
                row for row in self.world.relation_rows("program_resolution")
                if row["subject"] == subject and row["capability"] == CALL_CAPABILITY
            ]
        candidates = []
        if _roles(self.world, "program_resolution_candidate") is not None:
            candidates = [
                str(row["candidate"])
                for row in self.world.relation_rows("program_resolution_candidate")
                if row["subject"] == subject and row["capability"] == CALL_CAPABILITY
            ]
        resolution = resolutions[0] if resolutions else {}
        return {
            "invokes": invokes,
            "resolution": {
                "capability": str(resolution.get("capability") or ""),
                "status": str(resolution.get("status") or ""),
                "candidates": candidates,
            },
        }

    def mechanical_facts_for_subject(self, subject: str) -> list[dict[str, Any]]:
        """Rows of producer relations that name this subject.

        Governance receipts and governance relations are not producer facts.
        The relation names come from the world, not from a fixed vocabulary.
        """

        facts = []
        for name in _relation_names(self.world):
            if name.startswith("governance_") or name in {"software_subject", "software_manifestation"}:
                continue
            schema = self.world.relation_schema(name)
            referent_roles = [
                str(role["name"]) for role in schema["roles"] if role["type"] == "REFERENT"
            ]
            if not referent_roles:
                continue
            for row in self.world.relation_rows(name):
                if subject not in {str(row[role]) for role in referent_roles}:
                    continue
                values = {str(key): row[key] for key in row}
                facts.append({
                    "relation": name,
                    "values": {key: str(value) for key, value in values.items()},
                    "origin": self.world.origins_for_assertion(
                        self.world._inner._store.assertion_id_for_tuple(name, values)
                    ),
                })
        return facts

    def semantic_subject_for(self, proposition: str) -> str | None:
        if _roles(self.world, "proposition_semantic_subject") is None:
            return None
        matches = [
            str(row["semantic_subject"])
            for row in self.world.relation_rows("proposition_semantic_subject")
            if row["proposition"] == proposition
        ]
        return matches[0] if matches else None

    def completeness(self) -> list[dict[str, Any]]:
        gaps: dict[str, list[str]] = {}
        gap_origins: dict[str, dict[str, str]] = {}
        if _roles(self.world, "governance_known_gap") is not None:
            for row in self.world.relation_rows("governance_known_gap"):
                capability = str(row["capability"])
                gap = str(row["gap"])
                gaps.setdefault(capability, []).append(gap)
                gap_origins.setdefault(capability, {})[gap] = _origin(
                    self.world,
                    "governance_known_gap",
                    {"capability": capability, "gap": gap},
                )
        if _roles(self.world, "governance_completeness") is None:
            return []
        return [
            {
                "capability": str(row["capability"]),
                "status": str(row["status"]),
                "universe": str(row["universe"]),
                "basis": str(row["basis"]),
                "known_gaps": sorted(gaps.get(str(row["capability"]), [])),
                "origin": _origin(
                    self.world,
                    "governance_completeness",
                    {
                        "capability": str(row["capability"]),
                        "status": str(row["status"]),
                        "universe": str(row["universe"]),
                        "basis": str(row["basis"]),
                    },
                ),
                "known_gap_origins": gap_origins.get(str(row["capability"]), {}),
            }
            for row in self.world.relation_rows("governance_completeness")
        ]

    def absence_is_negative(self, subject: str) -> bool:
        """A missing binding is negative only under a complete claim for its universe."""

        if self.propositions_for_subject(subject):
            return False
        for claim in self.completeness():
            if claim["capability"] != BINDINGS_CAPABILITY or claim["status"] != "COMPLETE":
                continue
            if claim["known_gaps"]:
                continue
            if _subject_in_universe(self.world, subject, str(claim["universe"])):
                return True
        return False


def open_governance_world(path: Path | str) -> GovernanceView:
    world_path = Path(path)
    database = world_path / "world.sqlite" if world_path.is_dir() else world_path
    return GovernanceView(ConstructionWorld.open(database, read_only=True))


def _basis(world: ConstructionWorld, relation: str, values: dict[str, Any]) -> dict[str, Any]:
    assertion_id = world._inner._store.assertion_id_for_tuple(relation, values)
    warrant = world.warrant_for_assertion(assertion_id)
    evidence: list[dict[str, str]] = []
    method = ""
    extra: dict[str, Any] = {}
    for base in warrant["bases"]:
        detail = base.get("detail")
        if not isinstance(detail, dict):
            continue
        method = str(detail.get("construction_method") or method)
        if isinstance(detail.get("extra"), dict):
            extra = detail["extra"]
        for observation in detail.get("observations") or []:
            if not isinstance(observation, dict):
                continue
            text, status = reconstruct_governance_observation(world, observation)
            evidence.append({
                "native_handle": str(observation.get("native_handle") or ""),
                "native_location": str(observation.get("native_location") or ""),
                "text": text,
                "status": status,
            })
    return {
        "evidence": evidence,
        "construction_method": method,
        "origin": warrant["recorded_construction_origin"],
        "extra": extra,
    }


def _labels(world: ConstructionWorld) -> dict[str, str]:
    return {
        str(row["id"]): str(row["label"])
        for row in world.query("SELECT id, label FROM _world_referents")
    }


def _label(world: ConstructionWorld, referent: str) -> str:
    return _labels(world).get(referent, "")


def _roles(world: ConstructionWorld, relation: str) -> dict[str, str] | None:
    try:
        schema = world.relation_schema(relation)
    except Exception:
        return None
    return {str(role["name"]): str(role["type"]) for role in schema["roles"]}


def _manifestation_not_produced(subject: str, producer: str) -> dict[str, Any]:
    return {
        "subject": subject,
        "status": "NOT_PRODUCED",
        "scheme": "",
        "content": "",
        "content_digest": "",
        "location": "",
        "file_digest": "",
        "producer": producer,
        "capability": "",
    }


def _recorded_manifestation(world: ConstructionWorld, subject: str) -> dict[str, Any] | None:
    if _roles(world, "software_manifestation") is None:
        return None
    rows = [
        row for row in world.relation_rows("software_manifestation")
        if str(row["subject"]) == subject
    ]
    if len(rows) != 1:
        return None
    row = rows[0]
    basis = _basis(world, "software_manifestation", dict(row))
    evidence = basis["evidence"]
    if len(evidence) != 1:
        text, status = "", "FAILED"
    else:
        text, status = evidence[0]["text"], evidence[0]["status"]
    producer = _producer(world, subject) or str(row["capability"])
    return {
        "subject": subject,
        "status": status,
        "scheme": str(row["scheme"]),
        "content": text,
        "content_digest": hashlib.sha256(text.encode("utf-8")).hexdigest() if status == "OK" else "",
        "location": str(row["location"]),
        "file_digest": "",
        "producer": producer,
        "capability": str(row["capability"]),
    }


def _producer(world: ConstructionWorld, subject: str) -> str:
    if _roles(world, "software_subject") is None:
        return ""
    rows = [
        row for row in world.relation_rows("software_subject")
        if str(row["subject"]) == subject and str(row["capability"]).strip()
    ]
    if not rows:
        return ""
    return f"{rows[0]['capability']}/{rows[0]['version']}"


def _subject_in_universe(world: ConstructionWorld, subject: str, universe: str) -> bool:
    if _roles(world, "software_subject") is None:
        return False
    return any(
        str(row["subject"]) == subject and str(row["snapshot"]) == universe
        for row in world.relation_rows("software_subject")
    )


def _relation_names(world: ConstructionWorld) -> list[str]:
    return [
        str(row["name"])
        for row in world.query("SELECT name FROM _world_relations ORDER BY name")
    ]


def _origin(world: ConstructionWorld, relation: str, values: dict[str, Any]) -> str:
    origins = world.origins_for_assertion(
        world._inner._store.assertion_id_for_tuple(relation, values)
    )
    return origins[0] if len(origins) == 1 else ",".join(origins)
