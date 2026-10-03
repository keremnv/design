"""Fixture navigation over the TypeScript program spine.

Call-site and callable kinds belong to that producer. The generic
governance reads do not name them.
"""

from __future__ import annotations

from typing import Any

from ontology_author.software_governance.reads import GovernanceView


def call_sites_of(view: GovernanceView, owner_label: str) -> list[dict[str, Any]]:
    labels = _labels(view)
    parents: dict[str, list[str]] = {}
    for row in view.world.relation_rows("structural_context"):
        parents.setdefault(str(row["child"]), []).append(str(row["parent"]))
    kinds = {
        str(row["entity"]): str(row["kind"])
        for row in view.world.relation_rows("program_entity_kind")
    }
    found = []
    for entity, kind in kinds.items():
        if kind != "call_site":
            continue
        owner_ids = parents.get(entity, [])
        if owner_label not in {labels.get(owner, "") for owner in owner_ids}:
            continue
        manifestation = view.local_manifestation_for_subject(entity)
        relations = view.program_relations_for_subject(entity)
        found.append({
            "subject": entity,
            "text": manifestation["content"],
            "location": manifestation["location"],
            "resolution": relations["resolution"]["status"],
            "invokes": relations["invokes"],
        })
    return sorted(found, key=lambda item: _location_start(str(item["location"])))


def subject_named(view: GovernanceView, label: str, kind: str) -> str:
    labels = _labels(view)
    matches = [
        str(row["entity"])
        for row in view.world.relation_rows("program_entity_kind")
        if row["kind"] == kind and labels.get(str(row["entity"])) == label
    ]
    if len(matches) != 1:
        raise KeyError((label, kind, matches))
    return matches[0]


def select_resolved_call(view: GovernanceView, owner: str, text: str) -> str:
    matches = [
        site for site in call_sites_of(view, owner)
        if site["text"].strip() == text and site["resolution"] == "RESOLVED"
    ]
    if len(matches) != 1:
        raise KeyError((owner, text, [(site["text"], site["resolution"]) for site in call_sites_of(view, owner)]))
    return str(matches[0]["subject"])


def _labels(view: GovernanceView) -> dict[str, str]:
    return {
        str(row["id"]): str(row["label"])
        for row in view.world.query("SELECT id, label FROM _world_referents")
    }


def _location_start(location: str) -> int:
    parts = location.split(":")
    if len(parts) != 3:
        return 0
    return int(parts[1])
