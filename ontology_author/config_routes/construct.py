"""Production construction facade for ``config.routes/v1``.

Caller inputs (all explicit, no fixture knowledge)::

    software_source: path to the config-routes software JSON
    governance_source: path to the governance Markdown
    output: fresh publication address (must not exist)
    profile: must be ``config.routes/v1``
    expected_software_revision: optional ``sha256:`` hex the producer must consume
    expected_governance_revision: optional ``sha256:`` hex the governance read must consume

The profile derives proposition IDs, subject IDs, bindings, candidates,
questions, coverage, and gaps, and reports them in a machine-readable
:class:`ConfigRoutesReport`. Durable facts remain in the sealed World and
its retained evidence; the report is an ephemeral product result.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ontology_author.config_routes import producer as producer_module
from ontology_author.config_routes.producer import (
    CAPABILITY,
    KIND,
    SCHEME,
    VERSION,
    ExpectedRevisionMismatch,
    ProducedRoutes,
    normalize_revision,
)
from ontology_author.config_routes.rules import (
    BINDING_METHOD,
    BINDING_RESOLUTION,
    BINDING_SUPPORT,
    CANDIDATE_METHOD,
    CANDIDATE_RESOLUTION,
    CANDIDATE_SUPPORT,
    COMPLETENESS_BASIS,
    EVALUATOR_RULE,
    EVALUATOR_VERSION,
    GAP_GENERIC_UNRESOLVED,
    GAP_SUPPLIED_ONLY,
    GAP_UNSUPPORTED_GOVERNANCE,
    PROFILE_ID,
    RULE_BINDING,
    RULE_CANDIDATE,
    RULE_COVERAGE,
    PROFILE_VERSION,
    RULES,
    evaluator_status,
    extract_propositions,
    missing_route_gap,
    question_for_generic,
    question_for_missing_route,
)
from ontology_author.evidence import EvidenceError
from ontology_author.evidence.markdown import MarkdownSource
from ontology_author.software_governance import (
    BindingSpec,
    CandidateSpec,
    CompletenessSpec,
    ManifestationSpec,
    PropositionSpec,
    QuestionSpec,
    SoftwareSubjectSpec,
    construct_software_governance,
)
from ontology_author.software_governance.validation import BINDINGS_CAPABILITY
from ontology_author.world.core.source import SourceObservation
from ontology_author.world.runtime.world import ConstructionError


@dataclass(frozen=True)
class ConfigRoutesReport:
    succeeded: bool
    profile_id: str = PROFILE_ID
    profile_version: str = PROFILE_VERSION
    rules: tuple[str, ...] = RULES
    output: str = ""
    software_source: dict[str, str] = field(default_factory=dict)
    governance_source: dict[str, str] = field(default_factory=dict)
    consumed_software_revision: str = ""
    consumed_governance_revision: str = ""
    expected_software_revision: str = ""
    expected_governance_revision: str = ""
    propositions: tuple[dict[str, str], ...] = ()
    subjects: tuple[dict[str, str], ...] = ()
    bindings: tuple[dict[str, str], ...] = ()
    candidates: tuple[dict[str, str], ...] = ()
    questions: tuple[dict[str, str], ...] = ()
    coverage_status: str = ""
    coverage_basis: str = ""
    known_gaps: tuple[str, ...] = ()
    unsupported: tuple[dict[str, str], ...] = ()
    skipped: tuple[dict[str, str], ...] = ()
    evaluator: tuple[dict[str, Any], ...] = ()
    validation_errors: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["rules"] = list(self.rules)
        data["propositions"] = list(self.propositions)
        data["subjects"] = list(self.subjects)
        data["bindings"] = list(self.bindings)
        data["candidates"] = list(self.candidates)
        data["questions"] = list(self.questions)
        data["known_gaps"] = list(self.known_gaps)
        data["unsupported"] = list(self.unsupported)
        data["skipped"] = list(self.skipped)
        data["evaluator"] = list(self.evaluator)
        data["validation_errors"] = list(self.validation_errors)
        data["errors"] = list(self.errors)
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"


def construct_config_world(
    *,
    software_source: Path | str,
    governance_source: Path | str,
    output: Path | str,
    profile: str = PROFILE_ID,
    expected_software_revision: str | None = None,
    expected_governance_revision: str | None = None,
) -> ConfigRoutesReport:
    """Construct and publish a sealed config-routes World at ``output``."""
    publication = Path(output)
    software_path = Path(software_source)
    governance_path = Path(governance_source)
    expected_soft = _optional_revision(
        expected_software_revision, field="expected_software_revision"
    )
    expected_gov = _optional_revision(
        expected_governance_revision, field="expected_governance_revision"
    )
    if profile != PROFILE_ID:
        return ConfigRoutesReport(
            succeeded=False,
            output=str(publication),
            errors=(f"unsupported profile {profile!r}; this facade serves {PROFILE_ID}",),
            expected_software_revision=expected_soft,
            expected_governance_revision=expected_gov,
        )
    if os.path.lexists(publication):
        return ConfigRoutesReport(
            succeeded=False,
            output=str(publication),
            errors=(f"publication address already exists: {publication}",),
            expected_software_revision=expected_soft,
            expected_governance_revision=expected_gov,
        )
    staging = publication.with_name(
        publication.name + f".config-routes-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    )
    if os.path.lexists(staging):
        return ConfigRoutesReport(
            succeeded=False,
            output=str(publication),
            errors=(f"config-routes staging address already exists: {staging}",),
            expected_software_revision=expected_soft,
            expected_governance_revision=expected_gov,
        )
    try:
        try:
            produced = producer_module.produce_routes(
                staging,
                software_path,
                expected_revision=expected_soft or None,
            )
        except ExpectedRevisionMismatch as exc:
            _discard(staging)
            return ConfigRoutesReport(
                succeeded=False,
                output=str(publication),
                software_source=_source_identity(software_path),
                expected_software_revision=expected_soft,
                expected_governance_revision=expected_gov,
                consumed_software_revision=exc.consumed,
                errors=(
                    "expected software revision "
                    f"{exc.expected} but consumed {exc.consumed}; "
                    "no publication was made",
                ),
            )
        except (ConstructionError, OSError) as exc:
            _discard(staging)
            return ConfigRoutesReport(
                succeeded=False,
                output=str(publication),
                software_source=_source_identity(software_path),
                expected_software_revision=expected_soft,
                expected_governance_revision=expected_gov,
                errors=(f"{type(exc).__name__}: {exc}",),
            )
        try:
            gov_bytes, gov_digest, gov_source = _acquire_governance(
                governance_path, expected=expected_gov or None
            )
        except ExpectedRevisionMismatch as exc:
            _discard(staging)
            return ConfigRoutesReport(
                succeeded=False,
                output=str(publication),
                software_source=_source_identity(software_path),
                governance_source=_source_identity(governance_path),
                expected_software_revision=expected_soft,
                expected_governance_revision=expected_gov,
                consumed_software_revision=produced.consumed_revision,
                consumed_governance_revision=exc.consumed,
                errors=(
                    "expected governance revision "
                    f"{exc.expected} but consumed {exc.consumed}; "
                    "no publication was made",
                ),
            )
        except (ConstructionError, OSError, EvidenceError) as exc:
            _discard(staging)
            return ConfigRoutesReport(
                succeeded=False,
                output=str(publication),
                software_source=_source_identity(software_path),
                governance_source=_source_identity(governance_path),
                expected_software_revision=expected_soft,
                expected_governance_revision=expected_gov,
                consumed_software_revision=produced.consumed_revision,
                errors=(f"{type(exc).__name__}: {exc}",),
            )
        paragraphs: list[tuple[str, int]] = []
        gov_observations: dict[str, SourceObservation] = {}
        for index, region in enumerate(gov_source.paragraphs()):
            text = gov_source.reconstruct(region)
            stripped = text.strip()
            if not stripped:
                continue
            paragraphs.append((stripped, index))
            if stripped not in gov_observations:
                gov_observations[stripped] = SourceObservation(
                    provider="markdown",
                    native_handle=f"{governance_path.name}@sha256:{gov_digest}",
                    source_revision=f"sha256:{gov_digest}",
                    native_location=region.native_location,
                )
        extracted, unsupported = extract_propositions(paragraphs)
        skipped = _skipped_duplicates(paragraphs, extracted)
        if not extracted:
            _discard(staging)
            detail = "; ".join(
                item["reason"] for item in unsupported[:3]
            ) or "no supported governance paragraphs"
            return ConfigRoutesReport(
                succeeded=False,
                output=str(publication),
                software_source=_source_identity(software_path),
                governance_source=_source_identity(governance_path),
                expected_software_revision=expected_soft,
                expected_governance_revision=expected_gov,
                consumed_software_revision=produced.consumed_revision,
                consumed_governance_revision=gov_digest,
                unsupported=tuple(unsupported),
                skipped=tuple(skipped),
                coverage_status="",
                errors=(
                    "unsupported governance source for config.routes/v1: "
                    f"{detail}; no publication was made",
                ),
            )
        by_route = {item.route_id: item for item in produced.routes}
        blobs: dict[str, bytes] = dict(produced.blobs)
        blobs[gov_digest] = gov_bytes
        proposition_specs: list[PropositionSpec] = []
        binding_specs: list[BindingSpec] = []
        candidate_specs: list[CandidateSpec] = []
        question_specs: list[QuestionSpec] = []
        bindings_report: list[dict[str, str]] = []
        candidates_report: list[dict[str, str]] = []
        questions_report: list[dict[str, str]] = []
        gaps: list[str] = [GAP_SUPPLIED_ONLY]
        evaluator_report: list[dict[str, Any]] = []
        if unsupported:
            gaps.append(GAP_UNSUPPORTED_GOVERNANCE)
        for item in extracted:
            gov_obs = gov_observations[item.statement]
            proposition_specs.append(
                PropositionSpec(
                    proposition_id=item.proposition_id,
                    statement=item.statement,
                    domain_relation=item.domain_relation,
                    observations=(gov_obs,),
                    establishment_rule=item.establishment_rule,
                )
            )
            status, rule, gap = evaluator_status(item.proposition_id, item.route_id)
            evaluator_entry: dict[str, Any] = {
                "proposition": item.proposition_id,
                "status": status,
            }
            if rule is not None:
                evaluator_entry.update(rule)
                evaluator_entry["rule"] = dict(EVALUATOR_RULE)
            if gap is not None:
                evaluator_entry["gap"] = gap
            evaluator_report.append(evaluator_entry)
            if item.kind == "specific" and item.route_id is not None:
                target = by_route.get(item.route_id)
                if target is None:
                    question = question_for_missing_route(item.route_id, item.statement)
                    question_specs.append(
                        QuestionSpec(
                            proposition_id=item.proposition_id, question=question
                        )
                    )
                    questions_report.append({
                        "proposition": item.proposition_id,
                        "state": "UNRESOLVED",
                        "question": question,
                    })
                    gap_name = missing_route_gap(item.route_id)
                    if gap_name not in gaps:
                        gaps.append(gap_name)
                    continue
                binding_specs.append(
                    BindingSpec(
                        proposition_id=item.proposition_id,
                        software_subject=target.subject_id,
                        support=BINDING_SUPPORT,
                        endpoint_resolution=BINDING_RESOLUTION,
                        construction_method=BINDING_METHOD,
                        observations=(gov_obs, target.document_observation),
                        software_evidence=_software_evidence(target),
                        establishment_rule=RULE_BINDING,
                    )
                )
                bindings_report.append({
                    "proposition": item.proposition_id,
                    "software_subject": target.subject_id,
                    "route_id": target.route_id,
                    "establishment_rule": RULE_BINDING,
                })
            else:
                if GAP_GENERIC_UNRESOLVED not in gaps:
                    gaps.append(GAP_GENERIC_UNRESOLVED)
                for target in produced.routes:
                    candidate_specs.append(
                        CandidateSpec(
                            proposition_id=item.proposition_id,
                            software_subject=target.subject_id,
                            support=CANDIDATE_SUPPORT,
                            endpoint_resolution=CANDIDATE_RESOLUTION,
                            construction_method=CANDIDATE_METHOD,
                            observations=(gov_obs, target.document_observation),
                            software_evidence=_software_evidence(target),
                            establishment_rule=RULE_CANDIDATE,
                        )
                    )
                    candidates_report.append({
                        "proposition": item.proposition_id,
                        "software_subject": target.subject_id,
                        "route_id": target.route_id,
                        "establishment_rule": RULE_CANDIDATE,
                    })
                question = question_for_generic(item.subject_phrase)
                question_specs.append(
                    QuestionSpec(
                        proposition_id=item.proposition_id, question=question
                    )
                )
                questions_report.append({
                    "proposition": item.proposition_id,
                    "state": "UNRESOLVED",
                    "question": question,
                })
        if any(entry["status"] == "unsupported" for entry in evaluator_report):
            gaps.append("evaluator_rule_not_declared")
        gaps = list(dict.fromkeys(gaps))
        subjects = tuple(
            SoftwareSubjectSpec(
                subject_id=item.subject_id,
                snapshot_id=produced.snapshot_id,
                kind=KIND,
                capability=CAPABILITY,
                version=VERSION,
                observations=(item.document_observation,),
            )
            for item in produced.routes
        )
        manifestations = tuple(
            ManifestationSpec(
                subject_id=item.subject_id,
                scheme=SCHEME,
                location=item.location,
                capability=f"{CAPABILITY}/{VERSION}",
                observations=(item.manifestation_observation,),
            )
            for item in produced.routes
        )
        result = construct_software_governance(
            software_world=staging,
            output=publication,
            profile_id=PROFILE_ID,
            evidence_blobs=blobs,
            propositions=tuple(proposition_specs),
            bindings=tuple(binding_specs),
            candidates=tuple(candidate_specs),
            questions=tuple(question_specs),
            subjects=subjects,
            manifestations=manifestations,
            completeness=CompletenessSpec(
                capability=BINDINGS_CAPABILITY,
                status="INCOMPLETE",
                universe=produced.snapshot_id,
                basis=COMPLETENESS_BASIS,
                known_gaps=tuple(gaps),
            ),
        )
        _discard(staging)
        if not result.succeeded or result.world_dir is None:
            return ConfigRoutesReport(
                succeeded=False,
                output=str(publication),
                software_source=_source_identity(software_path),
                governance_source=_source_identity(governance_path),
                expected_software_revision=expected_soft,
                expected_governance_revision=expected_gov,
                consumed_software_revision=produced.consumed_revision,
                consumed_governance_revision=gov_digest,
                propositions=tuple(
                    {
                        "proposition": item.proposition_id,
                        "statement": item.statement,
                        "domain_relation": item.domain_relation,
                        "establishment_rule": item.establishment_rule,
                    }
                    for item in extracted
                ),
                subjects=tuple(
                    {
                        "subject": item.subject_id,
                        "route_id": item.route_id,
                        "location": item.location,
                    }
                    for item in produced.routes
                ),
                bindings=tuple(bindings_report),
                candidates=tuple(candidates_report),
                questions=tuple(questions_report),
                coverage_status="INCOMPLETE",
                coverage_basis=COMPLETENESS_BASIS,
                known_gaps=tuple(gaps),
                unsupported=tuple(unsupported),
                skipped=tuple(skipped),
                evaluator=tuple(evaluator_report),
                validation_errors=tuple(result.errors),
                errors=tuple(result.errors),
            )
        _verify_published_inventory(publication, produced)
        return ConfigRoutesReport(
            succeeded=True,
            output=str(publication.resolve()),
            software_source=_source_identity(software_path),
            governance_source=_source_identity(governance_path),
            expected_software_revision=expected_soft,
            expected_governance_revision=expected_gov,
            consumed_software_revision=produced.consumed_revision,
            consumed_governance_revision=gov_digest,
            propositions=tuple(
                {
                    "proposition": item.proposition_id,
                    "statement": item.statement,
                    "domain_relation": item.domain_relation,
                    "establishment_rule": item.establishment_rule,
                }
                for item in extracted
            ),
            subjects=tuple(
                {
                    "subject": item.subject_id,
                    "route_id": item.route_id,
                    "location": item.location,
                }
                for item in produced.routes
            ),
            bindings=tuple(bindings_report),
            candidates=tuple(candidates_report),
            questions=tuple(questions_report),
            coverage_status="INCOMPLETE",
            coverage_basis=COMPLETENESS_BASIS,
            known_gaps=tuple(gaps),
            unsupported=tuple(unsupported),
            skipped=tuple(skipped),
            evaluator=tuple(evaluator_report),
            validation_errors=(),
            errors=(),
        )
    finally:
        _discard(staging)


def _optional_revision(value: str | None, *, field: str) -> str:
    if value is None or str(value).strip() == "":
        return ""
    try:
        return normalize_revision(str(value))
    except ConstructionError as exc:
        raise ConstructionError(f"{field}: {exc}") from exc


def _source_identity(path: Path) -> dict[str, str]:
    return {"path": str(path), "name": path.name}


def _skipped_duplicates(
    paragraphs: list[tuple[str, int]], extracted
) -> list[dict[str, str]]:
    counts: dict[str, int] = {}
    for text, _ in paragraphs:
        counts[text] = counts.get(text, 0) + 1
    supported = {item.statement for item in extracted}
    skipped: list[dict[str, str]] = []
    for text, total in sorted(counts.items()):
        if text in supported and total > 1:
            skipped.append({
                "text": text[:200],
                "occurrences": str(total),
                "reason": "identical supported paragraph deduplicated to one proposition",
            })
    return skipped


def _acquire_governance(
    path: Path, *, expected: str | None
) -> tuple[bytes, str, MarkdownSource]:
    target = Path(path)
    if not target.is_file():
        raise ConstructionError(
            f"unsupported governance source form: not a regular file: {target}"
        )
    if target.suffix.lower() != ".md":
        raise ConstructionError(
            f"unsupported governance source form: {target.name} is not Markdown (.md)"
        )
    payload = target.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if expected is not None and digest != expected:
        raise ExpectedRevisionMismatch(expected=expected, consumed=digest)
    try:
        source = MarkdownSource(target, handle=target.name, data=payload)
    except EvidenceError as exc:
        raise ConstructionError(
            f"unsupported governance source form: {target.name}: {exc}"
        ) from exc
    if not source.paragraphs():
        raise ConstructionError(
            f"unsupported governance source form: {target.name} has no paragraphs"
        )
    return payload, digest, source


def _software_evidence(route) -> str:
    return (
        f"config_route record_id={route.route_id} location={route.location} "
        f"subject={route.subject_id}"
    )


def _verify_published_inventory(publication: Path, produced: ProducedRoutes) -> None:
    from ontology_author.software_governance import open_governance_world

    view = open_governance_world(publication)
    try:
        routes = list(view.world.relation_rows("config_route"))
        receipts = list(view.world.relation_rows("software_subject"))
        members = list(view.world.relation_rows("config_member"))
    finally:
        view.world.close()
    if (
        len(routes) != len(produced.routes)
        or len(receipts) != len(produced.routes)
        or len(members) != len(produced.routes)
    ):
        raise ConstructionError(
            "published inventory mismatch: parsed "
            f"{len(produced.routes)} routes but published {len(routes)} "
            f"route rows, {len(receipts)} subject receipts, {len(members)} members"
        )
    by_record = {str(row["record_id"]): row for row in routes}
    for item in produced.routes:
        row = by_record.get(item.route_id)
        if row is None:
            raise ConstructionError(
                f"published inventory mismatch: missing route {item.route_id}"
            )
        if str(row["path"]) != item.path or str(row["handler"]) != item.handler:
            raise ConstructionError(
                f"published inventory mismatch: route {item.route_id} differs"
            )


def _discard(path: Path) -> None:
    target = Path(path)
    if not os.path.lexists(target):
        return
    if not target.is_dir() or target.is_symlink():
        try:
            target.chmod(target.stat().st_mode | 0o600)
        except OSError:
            pass
        try:
            target.unlink()
        except OSError:
            pass
        return
    for child in target.rglob("*"):
        try:
            child.chmod(child.stat().st_mode | (0o700 if child.is_dir() else 0o600))
        except OSError:
            pass
    try:
        target.chmod(target.stat().st_mode | 0o700)
    except OSError:
        pass
    shutil.rmtree(target, ignore_errors=True)


__all__ = ["ConfigRoutesReport", "construct_config_world", "RULE_COVERAGE"]
