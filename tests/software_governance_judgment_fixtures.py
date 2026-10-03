"""Sealed worlds for Judgment v0 acceptance.

Support cases use the accepted profile builders. Conflict and unresolved
cases are additional sealed worlds, not comparisons between revisions.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from ontology_author.program_spine import TypeScriptBoundary, build_typescript_spine
from ontology_author.software_governance import (
    BindingSpec,
    CompletenessSpec,
    PropositionSpec,
    SoftwareSubjectSpec,
    construct_software_governance,
    open_governance_world,
)
from ontology_author.software_governance.reads import GovernanceView
from ontology_author.software_governance.validation import BINDINGS_CAPABILITY
from ontology_author.world.runtime.world import ConstructionWorld
from profiles.software_governance_config_v0.build import (
    EXPORT_ID,
    PROFILE_ID as CONFIG_PROFILE,
    SOFTWARE_EVIDENCE as CONFIG_EVIDENCE,
    build_config_profile,
)
from profiles.software_governance_config_v0.build import _excerpt as config_excerpt
from profiles.software_governance_config_v0.produce import (
    CAPABILITY,
    KIND,
    VERSION,
    produce_routes,
)
from profiles.software_governance_v0.build import (
    COMPLETENESS_BASIS,
    COMPLETENESS_GAP,
    OUTBOUND,
    POLICY,
    PROFILE_ID,
    PROGRAM,
    RUNBOOK,
    SOFTWARE_EVIDENCE,
    _excerpt,
    _spine_subject,
    build_mail_profile,
)
from profiles.software_governance_v0.subjects import call_sites_of, select_resolved_call, subject_named

CONFLICT_ROUTE = """{
  "routes": [
    {"id": "customer-export", "path": "/internal/export", "handler": "CustomerExport"},
    {"id": "health", "path": "/health", "handler": "Health"}
  ]
}
"""


def build_worlds(root: Path) -> dict[str, Path]:
    mail = root / "mail"
    build = build_mail_profile(mail)
    if not build.succeeded or build.world_dir is None:
        raise RuntimeError(build.errors)
    conflict_program = root / "mail-conflict-program"
    shutil.copytree(PROGRAM, conflict_program)
    source = conflict_program / "src" / "mail.ts"
    source.write_text(
        source.read_text(encoding="utf-8").replace(
            "  notificationGatewaySend(body);\n",
            "  smtpClientSend(body);\n",
            1,
        ),
        encoding="utf-8",
    )
    conflict = _mail_world(root / "mail-conflict", conflict_program, "sendReceipt", "smtpClientSend(body)")
    ambiguous = _mail_world_ambiguous(root / "mail-ambiguous", PROGRAM)
    config = root / "config"
    built = build_config_profile(config)
    if not built.succeeded or built.world_dir is None:
        raise RuntimeError(built.errors)
    document = root / "conflict-software.json"
    document.write_text(CONFLICT_ROUTE, encoding="utf-8")
    config_conflict = _config_world(root / "config-conflict", document)
    return {
        "mail": build.world_dir,
        "mail_conflict": conflict,
        "mail_ambiguous": ambiguous,
        "config": built.world_dir,
        "config_conflict": config_conflict,
    }


def _mail_world(root: Path, program: Path, owner: str, text: str) -> Path:
    spine = root / "spine"
    built = build_typescript_spine(
        program,
        spine,
        boundary=TypeScriptBoundary(
            workspace_roots=("src",),
            projects=("tsconfig.json",),
            package_roots=("src",),
        ),
    )
    if not built.succeeded or built.world_dir is None:
        raise RuntimeError(built.errors)
    view = open_governance_world(built.world_dir)
    try:
        subject = select_resolved_call(view, owner, text)
    finally:
        view.world.close()
    return _govern(root / "world", built.world_dir, subject)


def _mail_world_ambiguous(root: Path, program: Path) -> Path:
    spine = root / "spine"
    built = build_typescript_spine(
        program,
        spine,
        boundary=TypeScriptBoundary(
            workspace_roots=("src",),
            projects=("tsconfig.json",),
            package_roots=("src",),
        ),
    )
    if not built.succeeded or built.world_dir is None:
        raise RuntimeError(built.errors)
    view = open_governance_world(built.world_dir)
    try:
        sites = [
            site for site in call_sites_of(view, "sendAmbiguous")
            if site["resolution"] == "MULTIPLE_CANDIDATES"
        ]
        if len(sites) != 1:
            raise RuntimeError(sites)
        subject = str(sites[0]["subject"])
    finally:
        view.world.close()
    return _govern(root / "world", built.world_dir, subject)


def _govern(output: Path, spine: Path, subject: str) -> Path:
    world = ConstructionWorld.open(spine / "world.sqlite", read_only=True)
    try:
        view = GovernanceView(world)
        snapshot = str(world.relation_rows("program_snapshot")[0]["snapshot"])
        receipt = _spine_subject(world, subject)
        gateway = _spine_subject(world, subject_named(view, "notificationGatewaySend", "callable"))
    finally:
        world.close()
    blobs: dict[str, bytes] = {}
    policy = _excerpt(POLICY, OUTBOUND, blobs)
    runbook = _excerpt(RUNBOOK, OUTBOUND, blobs)
    result = construct_software_governance(
        software_world=spine,
        output=output,
        profile_id=PROFILE_ID,
        evidence_blobs=blobs,
        propositions=(
            PropositionSpec(
                proposition_id="proposition:outbound-mail",
                statement=OUTBOUND,
                domain_relation="outbound_mail_passes",
                observations=(policy, runbook),
            ),
        ),
        bindings=(
            BindingSpec(
                proposition_id="proposition:outbound-mail",
                software_subject=subject,
                support="SOURCE_EXPLICIT",
                endpoint_resolution="DETERMINISTIC",
                construction_method="correspondence to one call-site occurrence",
                observations=(policy,),
                software_evidence=SOFTWARE_EVIDENCE,
            ),
        ),
        subjects=(receipt, gateway),
        completeness=CompletenessSpec(
            capability=BINDINGS_CAPABILITY,
            status="INCOMPLETE",
            universe=snapshot,
            basis=COMPLETENESS_BASIS,
            known_gaps=(COMPLETENESS_GAP,),
        ),
    )
    if not result.succeeded or result.world_dir is None:
        raise RuntimeError(result.errors)
    return result.world_dir


def _config_world(root: Path, document: Path) -> Path:
    staging = root / "produced"
    produced = produce_routes(staging, document)
    export = next(route for route in produced.routes if route.route_id == "customer-export")
    blobs = dict(produced.blobs)
    text = config_excerpt(
        Path(__file__).resolve().parents[1] / "profiles" / "software_governance_config_v0" / "governance.md",
        "Customer export must use the approved customer-export route.",
        blobs,
    )
    result = construct_software_governance(
        software_world=staging,
        output=root / "world",
        profile_id=CONFIG_PROFILE,
        evidence_blobs=blobs,
        propositions=(
            PropositionSpec(
                proposition_id=EXPORT_ID,
                statement="Customer export must use the approved customer-export route.",
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
                software_evidence=CONFIG_EVIDENCE,
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
