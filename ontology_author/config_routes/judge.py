"""Guarded production Judge for ``config.routes/v1`` sealed Worlds.

One call judges one question ``(world, proposition, subject)``: the facade
opens the exact publication, discovers the declared evaluator from durable
World content, assembles and verifies the canonical bounded case, invokes
only that evaluator, and binds the case plus artifact to the exact address.

Outcomes are explicit product results: ``JUDGED`` carries a verified
artifact; ``UNSUPPORTED_EVALUATOR``, ``UNKNOWN_PROPOSITION``,
``UNKNOWN_SUBJECT``, and ``INVALID_CASE`` refuse without a usable
artifact. An invalid, unsealed, or incompatible World address raises
``ValueError``.

Verification replays under the compatible installed implementation: the
World records statement, profile, rule, and evidence, but not historical
evaluator executable semantics. A verified bundle means the current
compatible product reproduces this verdict for the canonical Case — not
that package A's exact code ran. The method fingerprint is a recorded
consistency aid, not proof of historical identity.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from ontology_author.config_routes.evaluate import evaluate_route_case
from ontology_author.config_routes.inspect import (
    database_fingerprint,
    open_config_world_view,
)
from ontology_author.config_routes.rules import (
    EVALUATOR_COVERED_ROUTE_IDS,
    EVALUATOR_METHOD_ID,
    EVALUATOR_VERSION,
    PROFILE_ID,
    RULE_EVALUATOR,
    evaluator_for_statement,
)
from ontology_author.software_governance.judgment import (
    assemble_case,
    verify_case,
)
from ontology_author.software_governance.judgment.artifact import ARTIFACT_FIELDS
from ontology_author.software_governance.reads import GovernanceView

JUDGMENT_BUNDLE_FORMAT = "config-routes-judgment/v1"
JUDGE_QUESTION = "Does this route satisfy the stated route rule?"

_APPLICABILITY = frozenset({"APPLIES", "DOES_NOT_APPLY", "UNKNOWN"})
_CONFORMANCE = frozenset({"CONFORMS", "CONFLICTS", "UNKNOWN"})
_BUNDLE_KEYS = frozenset({"format", "world", "request", "case", "artifact"})
_WORLD_KEYS = frozenset({"address", "world_id", "revision", "database_fingerprint"})
_REQUEST_KEYS = frozenset({"proposition", "subject", "question", "case_id"})


def judge_config_world(
    *,
    world: Path | str,
    proposition: str,
    subject: str,
    persist_to: Path | str | None = None,
    case_id: str | None = None,
) -> dict[str, Any]:
    """Judge one supported question against one exact sealed World."""
    view, address = open_config_world_view(world)
    try:
        context = {
            "address": address,
            "world_id": view.world.world_id,
            "revision": _revision(view),
            "database_fingerprint": database_fingerprint(address),
        }
        proposition_row = _proposition_row(view, proposition)
        if proposition_row is None:
            return {
                "outcome": "UNKNOWN_PROPOSITION",
                "world": context,
                "proposition": proposition,
                "subject": subject,
                "reason": f"no such proposition {proposition!r} in {address}",
            }
        if not _subject_exists(view, subject):
            return {
                "outcome": "UNKNOWN_SUBJECT",
                "world": context,
                "proposition": proposition,
                "subject": subject,
                "reason": f"no such software subject {subject!r} in {address}",
            }
        inspected = view.inspect_governance_proposition(proposition)
        if inspected.get("profile_id") != PROFILE_ID:
            return {
                "outcome": "UNSUPPORTED_EVALUATOR",
                "world": context,
                "proposition": proposition,
                "subject": subject,
                "reason": (
                    f"proposition was constructed under "
                    f"{inspected.get('profile_id')!r}, not {PROFILE_ID}"
                ),
                "supported": _supported_scope(),
            }
        status, _route_id, reason = evaluator_for_statement(
            inspected["statement"], inspected.get("establishment_rule") or ""
        )
        if status != "covered":
            return {
                "outcome": "UNSUPPORTED_EVALUATOR",
                "world": context,
                "proposition": proposition,
                "subject": subject,
                "reason": reason,
                "supported": _supported_scope(),
            }
        request = {
            "proposition": proposition,
            "subject": subject,
            "question": JUDGE_QUESTION,
            "case_id": case_id or f"{proposition}::{subject}",
        }
        case = assemble_case(
            view,
            case_id=request["case_id"],
            question=request["question"],
            proposition_ids=(proposition,),
            subject_ids=(subject,),
        )
        case_errors = verify_case(view, case)
        case_errors.extend(
            _verify_exact_association(
                view, case, address, context["database_fingerprint"], context["revision"]
            )
        )
        broken = _broken_evidence(case)
        if broken:
            case_errors.append(
                "relied evidence failed to reconstruct: " + ", ".join(sorted(broken))
            )
        if case_errors:
            return {
                "outcome": "INVALID_CASE",
                "world": context,
                "proposition": proposition,
                "subject": subject,
                "errors": case_errors,
            }
        artifact = evaluate_route_case(case)
        artifact_errors = _verify_judgment_artifact(case, artifact)
        if artifact_errors:
            return {
                "outcome": "INVALID_CASE",
                "world": context,
                "proposition": proposition,
                "subject": subject,
                "errors": artifact_errors,
            }
        persisted_to: str | None = None
        if persist_to is not None:
            persisted_to = write_judgment_bundle(
                persist_to,
                world=context,
                request=request,
                case=case,
                artifact=artifact,
            )
        return {
            "outcome": "JUDGED",
            "world": context,
            "proposition": proposition,
            "subject": subject,
            "evaluator": {
                "method_id": artifact["method"]["id"],
                "version": artifact["method"]["version"],
                "fingerprint": artifact["method"]["fingerprint"],
                "rule": artifact["method"]["rule"],
            },
            "case": case,
            "artifact": artifact,
            "verification": {
                "exact_address": True,
                "revision": True,
                "database_fingerprint": True,
                "citations": True,
                "evidence_ok": True,
                "artifact_shape": True,
                "method_matches": True,
            },
            "unknowns": _explain_unknowns(view, case, artifact),
            "persisted_to": persisted_to,
        }
    finally:
        view.world.close()


def write_judgment_bundle(
    path: Path | str,
    *,
    world: dict[str, Any],
    request: dict[str, Any],
    case: dict[str, Any],
    artifact: dict[str, Any],
) -> str:
    """Persist one request plus case plus artifact.

    Exclusive no-clobber creation: an existing path entry (including a
    symlink) is never followed or replaced. No atomic-publish claim is
    made; a truncated file fails verification as a structured negative.
    Judgment artifacts always live outside the sealed World: any target
    resolving to or underneath the World directory is refused before
    any parent directory is created or file opened.
    """
    _reject_inside_world(path, world["address"])
    target = Path(path)
    if os.path.lexists(target):
        raise ValueError(f"judgment bundle address already exists: {target}")
    bundle = {
        "format": JUDGMENT_BUNDLE_FORMAT,
        "world": {
            "address": world["address"],
            "world_id": world["world_id"],
            "revision": world["revision"],
            "database_fingerprint": world["database_fingerprint"],
        },
        "request": {
            "proposition": request["proposition"],
            "subject": request["subject"],
            "question": request["question"],
            "case_id": request["case_id"],
        },
        "case": case,
        "artifact": artifact,
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(bundle, indent=2, sort_keys=True) + "\n"
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW
    try:
        fd = os.open(target, flags, 0o644)
    except FileExistsError:
        raise ValueError(f"judgment bundle address already exists: {target}") from None
    except OSError as exc:
        raise ValueError(f"judgment bundle address is not a fresh file: {target} ({exc})") from None
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(payload)
    return str(target.resolve())


def read_judgment_bundle(path: Path | str) -> dict[str, Any]:
    """Read one persisted judgment bundle."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _reject_inside_world(path: Path | str, world_address: str) -> None:
    """Refuse any artifact target at or under the sealed World directory."""
    root = Path(world_address).resolve()
    target = Path(path).resolve()
    if target == root or root in target.parents:
        raise ValueError(f"judgment bundle address is inside the sealed World: {path}")


def verify_judgment_bundle(
    bundle: dict[str, Any] | Path | str,
    world: Path | str | None = None,
) -> dict[str, Any]:
    """Re-verify a persisted judgment against its exact sealed World.

    Reconstructs the canonical Case for the recorded request from the
    opened publication, requires the supplied Case to match it exactly,
    rediscovers evaluator eligibility, and replays the declared evaluator.
    Never trusts the supplied fact selection, support text, or verdict.
    Returns a structured negative report (never raises) for malformed,
    tampered, stale, or mismatched bundles.
    """
    checks: dict[str, bool] = {}
    errors: list[str] = []
    if isinstance(bundle, (Path, str)):
        try:
            loaded = read_judgment_bundle(bundle)
        except (OSError, ValueError) as exc:
            return {
                "verified": False,
                "checks": {"readable": False},
                "errors": [f"cannot parse judgment bundle: {exc}"],
            }
    else:
        loaded = bundle
    checks["readable"] = True
    if not isinstance(loaded, dict) or set(loaded) != _BUNDLE_KEYS:
        return _negative(
            checks, errors, "shape",
            f"invalid bundle shape: required keys {sorted(_BUNDLE_KEYS)}",
        )
    if loaded.get("format") != JUDGMENT_BUNDLE_FORMAT:
        return _negative(
            checks, errors, "shape",
            f"unknown judgment bundle format {loaded.get('format')!r}",
        )
    recorded_world = loaded["world"]
    request = loaded["request"]
    if (
        not isinstance(recorded_world, dict)
        or set(recorded_world) != _WORLD_KEYS
        or not isinstance(request, dict)
        or set(request) != _REQUEST_KEYS
    ):
        return _negative(
            checks, errors, "shape",
            "invalid bundle shape: world/request blocks lack required keys",
        )
    world_value_error = _world_block_error(recorded_world)
    if world_value_error is not None:
        return _negative(checks, errors, "shape", world_value_error)
    checks["shape"] = True
    if request["question"] != JUDGE_QUESTION:
        return _negative(
            checks, errors, "canonical_request",
            f"bundle question is not the product question {JUDGE_QUESTION!r}",
        )
    checks["canonical_request"] = True
    address = str(world) if world is not None else recorded_world["address"]
    try:
        view, opened = open_config_world_view(address)
    except (ValueError, TypeError, OSError) as exc:
        return _negative(checks, errors, "world_readable", str(exc))
    try:
        checks["world_readable"] = True
        checks["exact_address"] = opened == _resolved(recorded_world["address"])
        if not checks["exact_address"]:
            errors.append(
                f"bundle records {recorded_world['address']} but opened {opened}"
            )
        checks["world_id"] = view.world.world_id == recorded_world["world_id"]
        if not checks["world_id"]:
            errors.append("opened publication id differs from the bundle record")
        live_revision = _revision(view)
        checks["revision"] = live_revision == recorded_world["revision"]
        if not checks["revision"]:
            errors.append("opened publication revision differs from the bundle record")
        checks["database_fingerprint"] = (
            database_fingerprint(opened) == recorded_world["database_fingerprint"]
        )
        if not checks["database_fingerprint"]:
            errors.append("opened database bytes differ from the bundle fingerprint")
        proposition, subject = request["proposition"], request["subject"]
        if _proposition_row(view, proposition) is None:
            return _negative(
                checks, errors, "request_valid",
                f"no such proposition {proposition!r} in {opened}",
            )
        if not _subject_exists(view, subject):
            return _negative(
                checks, errors, "request_valid",
                f"no such software subject {subject!r} in {opened}",
            )
        checks["request_valid"] = True
        inspected = view.inspect_governance_proposition(proposition)
        eligible = inspected.get("profile_id") == PROFILE_ID and evaluator_for_statement(
            inspected["statement"], inspected.get("establishment_rule") or ""
        )[0] == "covered"
        checks["evaluator_supported"] = eligible
        if not eligible:
            return _negative(
                checks, errors, "evaluator_supported",
                f"no supported evaluator for {proposition!r} under the installed profile",
            )
        canonical = assemble_case(
            view,
            case_id=request["case_id"],
            question=request["question"],
            proposition_ids=(proposition,),
            subject_ids=(subject,),
        )
        supplied = loaded["case"]
        mismatch = _canonical_mismatch(canonical, supplied, opened)
        checks["canonical_match"] = mismatch == []
        errors.extend(mismatch)
        broken = _broken_evidence(canonical)
        checks["evidence_ok"] = broken == []
        if broken:
            errors.append(
                "relied evidence failed to reconstruct: " + ", ".join(sorted(broken))
            )
        if mismatch or broken:
            return {"verified": False, "checks": checks, "errors": errors}
        citation_errors = verify_case(view, canonical)
        checks["citations"] = citation_errors == []
        errors.extend(citation_errors)
        artifact = loaded["artifact"]
        try:
            shape_errors = _verify_judgment_artifact(canonical, artifact)
        except Exception as exc:
            shape_errors = [f"artifact could not be inspected as a judgment artifact: {exc}"]
        checks["artifact_shape"] = shape_errors == []
        errors.extend(shape_errors)
        try:
            replayed = evaluate_route_case(canonical)
        except Exception as exc:
            checks["verdict_reproduced"] = False
            errors.append(f"re-evaluation failed: {exc}")
        else:
            try:
                reproduced = (
                    replayed["applicability"] == artifact["applicability"]
                    and replayed["program_findings"] == artifact["program_findings"]
                    and replayed["conformance"] == artifact["conformance"]
                    and replayed["context_requests"] == artifact["context_requests"]
                    and replayed["method"] == artifact["method"]
                )
            except (KeyError, TypeError, AttributeError):
                checks["verdict_reproduced"] = False
                errors.append("recorded artifact lacks the reproduced verdict fields")
            else:
                checks["verdict_reproduced"] = reproduced
                if not reproduced:
                    errors.append("recorded verdict differs from re-evaluation")
        return {"verified": not errors, "checks": checks, "errors": errors}
    finally:
        view.world.close()


def _negative(
    checks: dict[str, bool], errors: list[str], name: str, message: str
) -> dict[str, Any]:
    checks[name] = False
    errors.append(message)
    return {"verified": False, "checks": checks, "errors": errors}


def _resolved(address: str) -> str:
    return str(Path(address).resolve())


def _supported_scope() -> dict[str, Any]:
    return {
        "profile_id": PROFILE_ID,
        "rule": RULE_EVALUATOR,
        "method_id": EVALUATOR_METHOD_ID,
        "version": EVALUATOR_VERSION,
        "covered_routes": sorted(EVALUATOR_COVERED_ROUTE_IDS),
    }


def _revision(view: GovernanceView) -> int:
    return int(
        view.world.query("SELECT revision FROM _world_meta WHERE singleton = 1")[0]["revision"]
    )


def _proposition_row(view: GovernanceView, proposition: str) -> dict[str, Any] | None:
    for row in view.world.relation_rows("governance_proposition"):
        if str(row["proposition"]) == proposition:
            return dict(row)
    return None


def _subject_exists(view: GovernanceView, subject: str) -> bool:
    return any(
        str(row["subject"]) == subject
        for row in view.world.relation_rows("software_subject")
    )


def _broken_evidence(case: dict[str, Any]) -> list[str]:
    """Case facts whose relied support did not reconstruct ``OK``.

    Any status other than ``OK`` (``FAILED`` today; anything unexpected
    fails closed) is fatal for a guarded Judgment.
    """
    broken: list[str] = []
    for fact in case.get("facts") or []:
        support = fact.get("support") or {}
        for item in support.get("reconstructed") or []:
            if item.get("status") != "OK":
                broken.append(f"{fact['relation']}/{fact['assertion_id'][:16]}")
                break
    return broken


def _canonical_mismatch(
    canonical: dict[str, Any], supplied: dict[str, Any], opened: str
) -> list[str]:
    """Named reasons the supplied Case is not the canonical product Case."""
    errors: list[str] = []
    if not isinstance(supplied, dict):
        return ["supplied case is not a judgment case object"]
    for field in ("world_id", "revision", "case_id", "question"):
        if supplied.get(field) != canonical.get(field):
            errors.append(f"supplied case {field} differs from the canonical case")
    if supplied.get("proposition_ids") != canonical.get("proposition_ids"):
        errors.append("supplied case proposition selection differs from the request")
    if supplied.get("subject_ids") != canonical.get("subject_ids"):
        errors.append("supplied case subject selection differs from the request")
    if _resolved(str(supplied.get("world_address", ""))) != opened:
        errors.append("supplied case address differs from the opened publication")
    want = Counter(_normalize_fact(fact) for fact in canonical.get("facts") or [])
    got: Counter[str] = Counter()
    facts = supplied.get("facts")
    if not isinstance(facts, list):
        errors.append("supplied case facts are not a fact list")
        facts = []
    for fact in facts:
        try:
            got[_normalize_fact(fact)] += 1
        except (KeyError, TypeError, AttributeError):
            errors.append("supplied case contains a malformed fact")
    missing = sum((want - got).values())
    extra = sum((got - want).values())
    if missing:
        errors.append(f"supplied case omits {missing} canonical fact occurrence(s)")
    if extra:
        errors.append(f"supplied case adds {extra} non-canonical fact occurrence(s)")
    return errors


def _world_block_error(recorded_world: dict[str, Any]) -> str | None:
    """Reject malformed recorded World metadata before any path use."""
    if not isinstance(recorded_world.get("address"), str) or not recorded_world["address"]:
        return "invalid bundle shape: recorded world address is not a non-empty string"
    if not isinstance(recorded_world.get("world_id"), str) or not recorded_world["world_id"]:
        return "invalid bundle shape: recorded world id is not a non-empty string"
    revision = recorded_world.get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool):
        return "invalid bundle shape: recorded revision is not an integer"
    fingerprint = recorded_world.get("database_fingerprint")
    if not isinstance(fingerprint, str) or not fingerprint:
        return "invalid bundle shape: recorded database fingerprint is not a non-empty string"
    return None


def _normalize_fact(fact: dict[str, Any]) -> str:
    support = fact.get("support") or {}
    return json.dumps(
        {
            "relation": fact["relation"],
            "assertion_id": fact["assertion_id"],
            "values": fact["values"],
            "support": {
                "origins": support.get("origins"),
                "bases": support.get("bases"),
                "reconstructed": sorted(
                    json.dumps(item, sort_keys=True)
                    for item in support.get("reconstructed") or []
                ),
            },
            "support_fingerprint": fact["support_fingerprint"],
        },
        sort_keys=True,
    )


def _verify_exact_association(
    view: GovernanceView,
    case: dict[str, Any],
    address: str,
    fingerprint: str,
    revision: int,
) -> list[str]:
    errors: list[str] = []
    if _resolved(case["world_address"]) != address:
        errors.append("case world address differs from the opened publication")
    if case.get("revision") != revision:
        errors.append("case revision differs from the opened publication")
    if database_fingerprint(address) != fingerprint:
        errors.append("opened database bytes differ from the judged fingerprint")
    return errors


def _verify_judgment_artifact(case: dict[str, Any], artifact: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(artifact, dict) or set(artifact) != set(ARTIFACT_FIELDS):
        errors.append("artifact shape is not the accepted judgment shape")
        return errors
    if artifact["case_id"] != case["case_id"]:
        errors.append("artifact case id differs from the case")
    if artifact["world_id"] != case["world_id"] or artifact["revision"] != case["revision"]:
        errors.append("artifact publication differs from the case")
    if not isinstance(artifact["applicability"], dict) or artifact["applicability"].get("result") not in _APPLICABILITY:
        errors.append("artifact applicability is not a supported result")
        return errors
    conformance = artifact["conformance"]
    if conformance is not None and (
        not isinstance(conformance, dict) or conformance.get("result") not in _CONFORMANCE
    ):
        errors.append("artifact conformance is not a supported result")
        return errors
    if artifact["applicability"]["result"] != "APPLIES" and conformance is not None and conformance["result"] != "UNKNOWN":
        errors.append("artifact claims conformance without APPLIES")
    known = {fact["assertion_id"] for fact in case["facts"]}
    cited: list[str] = []
    cited.extend(artifact["applicability"].get("assertion_ids") or [])
    for finding in artifact["program_findings"] or []:
        cited.extend(finding.get("assertion_ids") or [])
    if conformance is not None:
        cited.extend(conformance.get("assertion_ids") or [])
    for assertion_id in cited:
        if assertion_id not in known:
            errors.append(f"artifact cites {assertion_id} outside the case")
    try:
        expected_method = evaluate_route_case(case)["method"]
    except Exception as exc:
        errors.append(f"declared evaluator method could not be reproduced: {exc}")
        return errors
    if artifact["method"] != expected_method:
        errors.append("artifact method differs from the declared evaluator")
    return errors


def _explain_unknowns(
    view: GovernanceView, case: dict[str, Any], artifact: dict[str, Any]
) -> dict[str, Any]:
    applicability = artifact["applicability"]
    conformance = artifact["conformance"]
    questions = [
        fact["values"]
        for fact in case["facts"]
        if fact["relation"] == "governance_question"
    ]
    gaps = [
        fact["values"]["gap"]
        for fact in case["facts"]
        if fact["relation"] == "governance_known_gap"
    ]
    return {
        "applicability_unknown": applicability["result"] == "UNKNOWN",
        "applicability_because": applicability.get("because", ""),
        "conformance_unknown": conformance is not None and conformance.get("result") == "UNKNOWN",
        "conformance_because": conformance.get("because", "") if conformance is not None else "",
        "questions": questions,
        "known_gaps": sorted(gaps),
        "context_requests": artifact["context_requests"],
    }
