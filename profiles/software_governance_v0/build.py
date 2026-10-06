"""Acceptance profile for Software Governance construction.

The sentences and function names here are fixture vocabulary. They are not
the application ontology. This profile builds the TypeScript spine, then
asks generic Software Governance to record propositions on that World.

From the repository root:

```sh
uv run python profiles/software_governance_v0/build.py /path/to/fresh-world
```

The path must not already exist. The command seals a World there and prints
the publication address.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import uuid
from pathlib import Path

from ontology_author.evidence.markdown import MarkdownSource
from ontology_author.evidence.program_source import program_source_observations
from ontology_author.program_spine import TypeScriptBoundary, build_typescript_spine
from ontology_author.software_governance import (
    BindingSpec,
    CandidateSpec,
    CompletenessSpec,
    GovernanceConstructionResult,
    PropositionSpec,
    QuestionSpec,
    SoftwareSubjectSpec,
    construct_software_governance,
    open_governance_world,
)
from ontology_author.software_governance.reads import GovernanceView
from ontology_author.software_governance.validation import BINDINGS_CAPABILITY
from ontology_author.world.core.source import SourceObservation
from ontology_author.world.runtime.world import ConstructionError, ConstructionWorld
from profiles.software_governance_v0.subjects import select_resolved_call, subject_named
from profiles.software_governance_v0.validate import validate_mail_profile

PROFILE_ROOT = Path(__file__).resolve().parent
PROGRAM = PROFILE_ROOT / "program"
POLICY = PROFILE_ROOT / "policy.md"
RUNBOOK = PROFILE_ROOT / "runbook.md"
OUTBOUND = "Outbound email must pass through NotificationGateway."
MAILER = "Operational alerts must leave through an approved mailer."
PROFILE_ID = "software_governance_v0/mail"
SOFTWARE_EVIDENCE = "program-subject source observation"
COMPLETENESS_BASIS = "only the correspondences supplied to this construction are recorded"
COMPLETENESS_GAP = "supplied_correspondences_only"


def build_mail_profile(output: Path) -> GovernanceConstructionResult:
    publication = Path(output)
    if os.path.lexists(publication):
        return GovernanceConstructionResult(
            succeeded=False,
            errors=(f"publication address already exists: {publication}",),
        )
    staging = publication.with_name(
        f".{publication.name}.mail-spine-{uuid.uuid4().hex}"
    )
    if os.path.lexists(staging):
        return GovernanceConstructionResult(
            succeeded=False,
            errors=(f"mail staging address already exists: {staging}",),
        )
    try:
        spine = build_typescript_spine(
            PROGRAM,
            staging,
            boundary=TypeScriptBoundary(
                workspace_roots=("src",),
                projects=("tsconfig.json",),
                package_roots=("src",),
            ),
        )
        if not spine.succeeded or spine.world_dir is None:
            return GovernanceConstructionResult(succeeded=False, errors=tuple(spine.errors))
        world = ConstructionWorld.open(spine.world_dir / "world.sqlite", read_only=True)
        try:
            view = GovernanceView(world)
            bound = select_resolved_call(view, "sendReceipt", "notificationGatewaySend(body)")
            gateway = subject_named(view, "notificationGatewaySend", "callable")
            smtp = subject_named(view, "smtpClientSend", "callable")
            snapshot = str(world.relation_rows("program_snapshot")[0]["snapshot"])
            subjects = tuple(
                _spine_subject(world, subject_id)
                for subject_id in (bound, gateway, smtp)
            )
        finally:
            world.close()
        blobs: dict[str, bytes] = {}
        policy = _excerpt(POLICY, OUTBOUND, blobs)
        runbook = _excerpt(RUNBOOK, OUTBOUND, blobs)
        mailer = _excerpt(POLICY, MAILER, blobs)
        result = construct_software_governance(
            software_world=spine.world_dir,
            output=publication,
            profile_id=PROFILE_ID,
            evidence_blobs=blobs,
            propositions=(
                PropositionSpec(
                    proposition_id="proposition:outbound-mail",
                    statement=OUTBOUND,
                    domain_relation="outbound_mail_passes",
                    observations=(policy, runbook),
                ),
                PropositionSpec(
                    proposition_id="proposition:approved-mailer",
                    statement=MAILER,
                    domain_relation="approved_mailer",
                    observations=(mailer,),
                ),
            ),
            bindings=(
                BindingSpec(
                    proposition_id="proposition:outbound-mail",
                    software_subject=bound,
                    support="SOURCE_EXPLICIT",
                    endpoint_resolution="DETERMINISTIC",
                    construction_method="correspondence to one call-site occurrence",
                    observations=(policy,),
                    software_evidence=SOFTWARE_EVIDENCE,
                ),
            ),
            candidates=(
                CandidateSpec(
                    proposition_id="proposition:approved-mailer",
                    software_subject=gateway,
                    support="SOURCE_EXPLICIT",
                    endpoint_resolution="AMBIGUOUS",
                    construction_method="candidate software subject",
                    observations=(mailer,),
                    software_evidence=SOFTWARE_EVIDENCE,
                ),
                CandidateSpec(
                    proposition_id="proposition:approved-mailer",
                    software_subject=smtp,
                    support="SOURCE_EXPLICIT",
                    endpoint_resolution="AMBIGUOUS",
                    construction_method="candidate software subject",
                    observations=(mailer,),
                    software_evidence=SOFTWARE_EVIDENCE,
                ),
            ),
            questions=(
                QuestionSpec(
                    proposition_id="proposition:approved-mailer",
                    question="Which software subject is the approved mailer?",
                ),
            ),
            subjects=subjects,
            completeness=CompletenessSpec(
                capability=BINDINGS_CAPABILITY,
                status="INCOMPLETE",
                universe=snapshot,
                basis=COMPLETENESS_BASIS,
                known_gaps=(COMPLETENESS_GAP,),
            ),
        )
        if not result.succeeded or result.world_dir is None:
            return result
        sealed = open_governance_world(result.world_dir)
        try:
            profile_errors = tuple(validate_mail_profile(sealed.world))
        finally:
            sealed.world.close()
        if profile_errors:
            _discard(result.world_dir)
            return GovernanceConstructionResult(succeeded=False, errors=profile_errors)
        return result
    except Exception as exc:
        return GovernanceConstructionResult(
            succeeded=False,
            errors=(f"{type(exc).__name__}: {exc}",),
        )
    finally:
        _discard(staging)


def _spine_subject(world: ConstructionWorld, subject_id: str) -> SoftwareSubjectSpec:
    entity = next(
        row for row in world.relation_rows("program_entity")
        if str(row["entity"]) == subject_id
    )
    extractor = next(
        str(row["extractor"])
        for row in world.relation_rows("program_snapshot")
        if str(row["snapshot"]) == str(entity["snapshot"])
    )
    capability, separator, version = extractor.rpartition("@")
    if not separator:
        capability, version = extractor, "v0"
    observations = tuple(
        SourceObservation(
            provider=str(item["provider"]),
            native_handle=str(item["native_handle"]),
            source_revision=str(item["source_revision"]),
            native_location=str(item["native_location"]),
        )
        for item in program_source_observations(world, subject_id)
    )
    return SoftwareSubjectSpec(
        subject_id=subject_id,
        snapshot_id=str(entity["snapshot"]),
        kind=str(entity["kind"]),
        capability=capability,
        version=version,
        observations=observations,
    )


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
    result = build_mail_profile(Path(sys.argv[1]))
    if not result.succeeded or result.world_dir is None:
        raise SystemExit("\n".join(result.errors))
    print(result.world_dir)


if __name__ == "__main__":
    main()
