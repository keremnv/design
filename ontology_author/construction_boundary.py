"""Small construction boundary records, composed above the frozen kernel.

These are material boundary objects, not an investigation protocol. Providers
still own evidence reconstruction; applications still own meaning and admission.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from ontology_author.world.core.source import SourceObservation
from ontology_author.world.runtime.publication import PublicationRef


@dataclass(frozen=True)
class ConstructionBasis:
    """Declared consumed material; membership grants no semantic support.

    Program qualifications reuse an exact publication and its native snapshot
    referent/id. Configuration is canonical JSON to keep the record immutable.
    A copied baseline is separately identified; it is not an inheritance rule.
    """

    observations: tuple[SourceObservation, ...]
    publications: tuple[PublicationRef, ...] = ()
    program_snapshots: tuple[tuple[PublicationRef, str, str], ...] = ()
    configuration_json: str = "{}"
    candidate_baseline: PublicationRef | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "observations": [item.as_pointer() for item in self.observations],
            "publications": [item.as_dict() for item in self.publications],
            "program_snapshots": [
                {"publication": publication.as_dict(), "snapshot": snapshot,
                 "snapshot_id": snapshot_id}
                for publication, snapshot, snapshot_id in self.program_snapshots
            ],
            "configuration": json.loads(self.configuration_json),
            "candidate_baseline": (
                self.candidate_baseline.as_dict() if self.candidate_baseline else None
            ),
        }


@dataclass(frozen=True)
class SupportPath:
    """All members are jointly required; separate paths are independent.

    This records the constructor's warrant, not a proof of intelligent inference.
    """

    members: tuple[SourceObservation, ...]

    def __post_init__(self) -> None:
        if not self.members:
            raise ValueError("support path must have at least one member")

    def as_dict(self) -> dict[str, Any]:
        return {"members": [item.as_pointer() for item in self.members]}


def support_paths_for_assertion(world: Any, assertion_id: str) -> tuple[SupportPath, ...]:
    """Read only explicitly recorded grouping; legacy flat support stays flat."""

    paths: dict[str, SupportPath] = {}
    for base in world.warrant_for_assertion(assertion_id).get("bases", []):
        detail = base.get("detail")
        if isinstance(detail, dict):
            extra = detail.get("extra") or {}
            if "support_paths" in extra:
                for path in extra["support_paths"]:
                    value = SupportPath(tuple(SourceObservation(**member) for member in path["members"]))
                    paths[json.dumps(value.as_dict(), sort_keys=True)] = value
    return tuple(paths.values())
