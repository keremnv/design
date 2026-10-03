"""Sealed worlds for Investigation v0 acceptance.

The accepted config profile supplies same-world facts. A second publication
reuses the producer world id with different bytes. A third publication's
source contains a field the producer does not assert.
"""

from __future__ import annotations

import json
from pathlib import Path

from ontology_author.software_governance import (
    BindingSpec,
    CompletenessSpec,
    ManifestationSpec,
    PropositionSpec,
    SoftwareSubjectSpec,
    construct_software_governance,
)
from ontology_author.software_governance.validation import BINDINGS_CAPABILITY
from profiles.software_governance_config_v0.build import (
    EXPORT_ID,
    GOVERNANCE,
    PROFILE_ID,
    SOFTWARE_EVIDENCE,
    _excerpt,
    build_config_profile,
)
from profiles.software_governance_config_v0.produce import (
    CAPABILITY,
    KIND,
    SCHEME,
    VERSION,
    produce_routes,
)

EXPORT_STATEMENT = "Customer export must use the approved customer-export route."
CONFLICT_DOCUMENT = {
    "routes": [
        {"id": "customer-export", "path": "/internal/export", "handler": "CustomerExport"},
        {"id": "health", "path": "/health", "handler": "Health"},
    ]
}
UNPUBLISHED_DOCUMENT = {
    "routes": [
        {
            "id": "customer-export",
            "path": "/customers/export",
            "handler": "CustomerExport",
            "approval": "manager-signoff",
        }
    ]
}


def build_worlds(root: Path) -> dict[str, Path]:
    accepted = build_config_profile(root / "accepted")
    if not accepted.succeeded or accepted.world_dir is None:
        raise RuntimeError(accepted.errors)
    return {
        "accepted": accepted.world_dir,
        "conflict": _bound_export(root / "conflict", CONFLICT_DOCUMENT),
        "unpublished": _bound_export(root / "unpublished", UNPUBLISHED_DOCUMENT),
    }


def _bound_export(root: Path, document: dict) -> Path:
    staging = root / "produced"
    source = root / "software.json"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    produced = produce_routes(staging, source)
    export = next(route for route in produced.routes if route.route_id == "customer-export")
    blobs = dict(produced.blobs)
    text = _excerpt(GOVERNANCE, EXPORT_STATEMENT, blobs)
    result = construct_software_governance(
        software_world=staging,
        output=root / "world",
        profile_id=PROFILE_ID,
        evidence_blobs=blobs,
        propositions=(
            PropositionSpec(
                proposition_id=EXPORT_ID,
                statement=EXPORT_STATEMENT,
                domain_relation="customer_export_route",
                observations=(text,),
            ),
        ),
        bindings=(
            BindingSpec(
                proposition_id=EXPORT_ID,
                software_subject=export.subject_id,
                support="SOURCE_EXPLICIT",
                endpoint_resolution="DETERMINISTIC",
                construction_method="correspondence to one route record",
                observations=(text,),
                software_evidence=SOFTWARE_EVIDENCE,
            ),
        ),
        subjects=(
            SoftwareSubjectSpec(
                subject_id=export.subject_id,
                snapshot_id=produced.snapshot_id,
                kind=KIND,
                capability=CAPABILITY,
                version=VERSION,
                observations=(export.document_observation,),
            ),
        ),
        manifestations=(
            ManifestationSpec(
                subject_id=export.subject_id,
                scheme=SCHEME,
                location=export.location,
                capability=f"{CAPABILITY}/{VERSION}",
                observations=(export.manifestation_observation,),
            ),
        ),
        completeness=CompletenessSpec(
            capability=BINDINGS_CAPABILITY,
            status="INCOMPLETE",
            universe=produced.snapshot_id,
            basis="only the correspondences supplied to this construction are recorded",
            known_gaps=("supplied_correspondences_only",),
        ),
    )
    if not result.succeeded or result.world_dir is None:
        raise RuntimeError(result.errors)
    return result.world_dir
