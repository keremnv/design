"""Config-route profile for Software Governance construction.

The route names and English sentences are fixture vocabulary. The producer
is a deterministic JSON reader. Generic Software Governance records the
propositions on the world that producer built.

From the repository root:

```sh
uv run python profiles/software_governance_config_v0/build.py /path/to/fresh-world
```

The path must not already exist.
"""

from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

from ontology_author.evidence.markdown import MarkdownSource
from ontology_author.software_governance import (
    BindingSpec,
    CandidateSpec,
    CompletenessSpec,
    GovernanceConstructionResult,
    ManifestationSpec,
    PropositionSpec,
    QuestionSpec,
    SoftwareSubjectSpec,
    construct_software_governance,
)
from ontology_author.software_governance.validation import BINDINGS_CAPABILITY
from ontology_author.world.core.source import SourceObservation
from ontology_author.world.runtime.world import ConstructionError
from profiles.software_governance_config_v0.produce import (
    CAPABILITY,
    KIND,
    SCHEME,
    VERSION,
    produce_routes,
)

PROFILE_ROOT = Path(__file__).resolve().parent
DOCUMENT = PROFILE_ROOT / "software.json"
GOVERNANCE = PROFILE_ROOT / "governance.md"
EXPORT = "Customer export must use the approved customer-export route."
STATUS = "Status checks must use an approved route."
PROFILE_ID = "software_governance_config_v0/routes"
SOFTWARE_EVIDENCE = "json route record"
COMPLETENESS_BASIS = "only the correspondences supplied to this construction are recorded"
COMPLETENESS_GAP = "supplied_correspondences_only"
EXPORT_ID = "proposition:customer-export-route"
STATUS_ID = "proposition:approved-status-route"


def build_config_profile(output: Path) -> GovernanceConstructionResult:
    publication = Path(output)
    if publication.exists():
        return GovernanceConstructionResult(
            succeeded=False,
            errors=(f"publication address already exists: {publication}",),
        )
    staging = publication.with_name(publication.name + ".config-routes")
    _discard(staging)
    try:
        produced = produce_routes(staging, DOCUMENT)
        by_id = {route.route_id: route for route in produced.routes}
        export = by_id["customer-export"]
        health = by_id["health"]
        blobs = dict(produced.blobs)
        export_text = _excerpt(GOVERNANCE, EXPORT, blobs)
        status_text = _excerpt(GOVERNANCE, STATUS, blobs)
        subjects = tuple(
            SoftwareSubjectSpec(
                subject_id=route.subject_id,
                snapshot_id=produced.snapshot_id,
                kind=KIND,
                capability=CAPABILITY,
                version=VERSION,
                observations=(route.document_observation,),
            )
            for route in produced.routes
        )
        manifestations = tuple(
            ManifestationSpec(
                subject_id=route.subject_id,
                scheme=SCHEME,
                location=route.location,
                capability=f"{CAPABILITY}/{VERSION}",
                observations=(route.manifestation_observation,),
            )
            for route in produced.routes
        )
        return construct_software_governance(
            software_world=staging,
            output=publication,
            profile_id=PROFILE_ID,
            evidence_blobs=blobs,
            propositions=(
                PropositionSpec(
                    proposition_id=EXPORT_ID,
                    statement=EXPORT,
                    domain_relation="customer_export_route",
                    observations=(export_text,),
                ),
                PropositionSpec(
                    proposition_id=STATUS_ID,
                    statement=STATUS,
                    domain_relation="approved_status_route",
                    observations=(status_text,),
                ),
            ),
            bindings=(
                BindingSpec(
                    proposition_id=EXPORT_ID,
                    software_subject=export.subject_id,
                    support="SOURCE_EXPLICIT",
                    endpoint_resolution="DETERMINISTIC",
                    construction_method="correspondence to one route record",
                    observations=(export_text,),
                    software_evidence=SOFTWARE_EVIDENCE,
                ),
            ),
            candidates=(
                CandidateSpec(
                    proposition_id=STATUS_ID,
                    software_subject=export.subject_id,
                    support="SOURCE_EXPLICIT",
                    endpoint_resolution="AMBIGUOUS",
                    construction_method="candidate route record",
                    observations=(status_text,),
                    software_evidence=SOFTWARE_EVIDENCE,
                ),
                CandidateSpec(
                    proposition_id=STATUS_ID,
                    software_subject=health.subject_id,
                    support="SOURCE_EXPLICIT",
                    endpoint_resolution="AMBIGUOUS",
                    construction_method="candidate route record",
                    observations=(status_text,),
                    software_evidence=SOFTWARE_EVIDENCE,
                ),
            ),
            questions=(
                QuestionSpec(
                    proposition_id=STATUS_ID,
                    question="Which route is the approved status route?",
                ),
            ),
            subjects=subjects,
            manifestations=manifestations,
            completeness=CompletenessSpec(
                capability=BINDINGS_CAPABILITY,
                status="INCOMPLETE",
                universe=produced.snapshot_id,
                basis=COMPLETENESS_BASIS,
                known_gaps=(COMPLETENESS_GAP,),
            ),
        )
    except Exception as exc:
        return GovernanceConstructionResult(
            succeeded=False,
            errors=(f"{type(exc).__name__}: {exc}",),
        )
    finally:
        _discard(staging)


def _excerpt(path: Path, text: str, blobs: dict[str, bytes]) -> SourceObservation:
    source = MarkdownSource(path, handle=path.name)
    matches = [
        region
        for region in source.paragraphs()
        if source.reconstruct(region).strip() == text.strip()
    ]
    if len(matches) != 1:
        raise ConstructionError(f"{path.name} does not contain one paragraph {text!r}")
    digest = hashlib.sha256(source.data).hexdigest()
    blobs[digest] = source.data
    region = matches[0]
    return SourceObservation(
        provider="markdown",
        native_handle=f"{path.name}@sha256:{digest}",
        source_revision=source.revision,
        native_location=region.native_location,
    )


def _discard(path: Path) -> None:
    if not path.exists():
        return
    for child in path.rglob("*"):
        child.chmod(child.stat().st_mode | (0o700 if child.is_dir() else 0o600))
    path.chmod(path.stat().st_mode | 0o700)
    shutil.rmtree(path)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: build.py <fresh-output-directory>")
    result = build_config_profile(Path(sys.argv[1]))
    if not result.succeeded or result.world_dir is None:
        raise SystemExit("\n".join(result.errors))
    print(result.world_dir)


if __name__ == "__main__":
    main()
