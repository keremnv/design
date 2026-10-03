"""Historical experiment: what a governance binding targets for one invocation.

Excluded from the default gate. Run with `pytest -m historical`.

Uses sealed TypeScript spine facts as they are. Call-site correspondence is
not modified. Insert-before and reorder mis-joins are reported, not fixed.
The governance record is a direct evidence-to-software binding: no semantic
identity is introduced for this single sentence.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from ontology_author.evidence.program_source import reconstruct_program_observation
from ontology_author.program_spine import TypeScriptBoundary, build_typescript_spine, compare_program_spines
from ontology_author.world.core.model import Role, RoleType
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding, SourceObservation
from ontology_author.world.runtime.world import ConstructionWorld

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
pytestmark = [
    pytest.mark.historical,
    pytest.mark.skipif(
        shutil.which("node") is None or not (REPOSITORY_ROOT / "frontend" / "node_modules" / "typescript").exists(),
        reason="the TypeScript compiler API dependency is not installed",
    ),
]

KNOWLEDGE = "Outbound email must pass through NotificationGateway."

# A property call such as gateway.send is not a positive program_invokes edge
# in the current extractor: the property target and the signature target are
# both recorded, so the status is MULTIPLE_CANDIDATES even when they name one
# method. The resolved caller→target facts below are therefore function calls.
# The union method call remains the genuine two-candidate case.
BASELINE = """\
export class NotificationGateway {
  send(body: string): string { return body; }
}
export class SMTPClient {
  send(body: string): string { return body; }
}
export function notificationGatewaySend(body: string): string { return body; }
export function smtpClientSend(body: string): string { return body; }
export function sendReceipt(body: string): string {
  const marked = body;
  notificationGatewaySend(body);
  return notificationGatewaySend(marked);
}
export function sendInvoice(body: string): string {
  return notificationGatewaySend(body);
}
export function probeMethod(): string {
  const gateway = new NotificationGateway();
  return gateway.send("x");
}
export function sendAmbiguous(body: string, channel: NotificationGateway | SMTPClient): string {
  return channel.send(body);
}
"""


def _variant(body: str) -> str:
    old = """\
export function sendReceipt(body: string): string {
  const marked = body;
  notificationGatewaySend(body);
  return notificationGatewaySend(marked);
}
"""
    assert old in BASELINE
    return BASELINE.replace(old, body, 1)


CONTROLS = {
    "A_retarget": _variant(
        """\
export function sendReceipt(body: string): string {
  const marked = body;
  notificationGatewaySend(body);
  return smtpClientSend(marked);
}
"""
    ),
    "B_body_edit": _variant(
        """\
export function sendReceipt(body: string): string {
  const prepared = body + "!";
  const marked = body;
  notificationGatewaySend(body);
  return notificationGatewaySend(marked);
}
"""
    ),
    "C_call_after": _variant(
        """\
export function sendReceipt(body: string): string {
  const marked = body;
  notificationGatewaySend(body);
  return notificationGatewaySend(marked);
  audit(body);
}
export function audit(body: string): string { return body; }
"""
    ),
    "C_call_before": _variant(
        """\
export function sendReceipt(body: string): string {
  audit(body);
  const marked = body;
  notificationGatewaySend(body);
  return notificationGatewaySend(marked);
}
export function audit(body: string): string { return body; }
"""
    ),
    "D_shift": _variant(
        """\
export function sendReceipt(body: string): string {
  const marked = body;
  notificationGatewaySend(body);
  const note = marked;
  return notificationGatewaySend(marked);
}
"""
    ),
    "D_reorder": _variant(
        """\
export function sendReceipt(body: string): string {
  const marked = body;
  return notificationGatewaySend(marked);
  notificationGatewaySend(body);
}
"""
    ),
    "E_rename_owner": BASELINE.replace("function sendReceipt", "function deliverReceipt", 1),
    "F_sibling_retarget": _variant(
        """\
export function sendReceipt(body: string): string {
  const marked = body;
  smtpClientSend(body);
  return notificationGatewaySend(marked);
}
"""
    ),
}


def _build(root: Path, name: str, source: str) -> ConstructionWorld:
    project = root / name
    source_path = project / "src" / "mail.ts"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(source, encoding="utf-8", newline="\n")
    (project / "tsconfig.json").write_text(
        json.dumps({
            "compilerOptions": {"target": "ES2020", "module": "commonjs", "moduleResolution": "node", "strict": True},
            "include": ["src/**/*.ts"],
        }),
        encoding="utf-8",
    )
    boundary = TypeScriptBoundary(workspace_roots=("src",), projects=("tsconfig.json",), package_roots=("src",))
    result = build_typescript_spine(project, project / "world", boundary=boundary)
    assert result.succeeded, result.errors
    return ConstructionWorld.open(project / "world" / "world.sqlite")


def _labels(world: ConstructionWorld) -> dict[str, str]:
    return {str(row["id"]): str(row["label"]) for row in world.query("SELECT id, label FROM _world_referents")}


def _parents(world: ConstructionWorld) -> dict[str, list[str]]:
    parents: dict[str, list[str]] = {}
    for row in world.relation_rows("structural_context"):
        parents.setdefault(str(row["child"]), []).append(str(row["parent"]))
    return parents


def _kind(world: ConstructionWorld) -> dict[str, str]:
    return {str(row["entity"]): str(row["kind"]) for row in world.relation_rows("program_entity_kind")}


def _invokes(world: ConstructionWorld) -> list[dict[str, str]]:
    return [
        {"assertion_id": str(row["_assertion_id"]), "call_site": str(row["call_site_id"]), "target": str(row["target_id"])}
        for row in world.query("SELECT _assertion_id, call_site_id, target_id FROM program_invokes")
    ]


def _resolution(world: ConstructionWorld, subject: str) -> dict[str, object]:
    rows = [
        row for row in world.relation_rows("program_resolution")
        if row["subject"] == subject and row["capability"] == "spine.calls/v1"
    ]
    assert len(rows) == 1, (subject, rows)
    candidates = [
        str(row["candidate"]) for row in world.relation_rows("program_resolution_candidate")
        if row["subject"] == subject and row["capability"] == "spine.calls/v1"
    ]
    return {"status": str(rows[0]["status"]), "candidates": candidates}


def _region(world: ConstructionWorld, entity: str) -> str:
    from ontology_author.evidence.program_source import program_source_observations

    observations = program_source_observations(world, entity)
    assert len(observations) == 1
    text, status = reconstruct_program_observation(world, observations[0])
    assert status == "OK"
    return text


def _call_sites_of(world: ConstructionWorld, owner_label: str) -> list[dict[str, object]]:
    labels = _labels(world)
    parents = _parents(world)
    kinds = _kind(world)
    invokes = {row["call_site"]: row for row in _invokes(world)}
    found = []
    for entity, kind in kinds.items():
        if kind != "call_site":
            continue
        owner_ids = parents.get(entity, [])
        if owner_label not in {labels.get(owner, "") for owner in owner_ids}:
            continue
        edge = invokes.get(entity)
        resolution = _resolution(world, entity)
        target = edge["target"] if edge else ""
        target_parents = parents.get(target, []) if target else []
        found.append({
            "call_site": entity,
            "text": _region(world, entity),
            "start": int(str(_source_location(world, entity)).split(":")[1]),
            "target": target,
            "target_label": labels.get(target, ""),
            "target_owner": labels.get(target_parents[0], "") if target_parents else "",
            "assertion_id": edge["assertion_id"] if edge else "",
            "resolution": resolution["status"],
            "candidates": resolution["candidates"],
        })
    return sorted(found, key=lambda item: int(item["start"]))


def _source_location(world: ConstructionWorld, entity: str) -> str:
    from ontology_author.evidence.program_source import program_source_observations

    observations = program_source_observations(world, entity)
    assert len(observations) == 1
    return observations[0]["native_location"]


def _entity_named(world: ConstructionWorld, label: str, kind: str) -> str:
    labels = _labels(world)
    kinds = _kind(world)
    matches = [entity for entity, entity_kind in kinds.items() if entity_kind == kind and labels.get(entity) == label]
    assert len(matches) == 1, (label, kind, matches)
    return matches[0]


def _continued(comparison, old_id: str) -> str:
    claims = [claim for claim in comparison.correspondences if claim.old_entity == old_id]
    assert len(claims) == 1
    claim = claims[0]
    if claim.continuity != "CONTINUED" or not claim.new_entity:
        return ""
    return str(claim.new_entity)


def _relation_status(comparison, old_call: str, old_target: str) -> str:
    relation = comparison.delta.relations["program_invokes"]
    for bucket in ("preserved", "retargeted", "removed", "unresolved"):
        for row in relation[bucket]:
            old = row.get("old") or {}
            if old.get("call_site") == old_call and old.get("target") == old_target:
                return bucket
    return "ABSENT"


def test_invocation_binding_targets_the_call_site_not_the_owner_or_tuple(tmp_path: Path) -> None:
    baseline = _build(tmp_path, "baseline", BASELINE)
    try:
        owner = _entity_named(baseline, "sendReceipt", "callable")
        invoice = _entity_named(baseline, "sendInvoice", "callable")
        ambiguous_owner = _entity_named(baseline, "sendAmbiguous", "callable")
        receipt_calls = _call_sites_of(baseline, "sendReceipt")
        gateway_sends = [
            call for call in receipt_calls
            if call["resolution"] == "RESOLVED" and call["target_label"] == "notificationGatewaySend"
        ]
        assert len(gateway_sends) == 2
        ungoverned, governed = gateway_sends
        assert governed["assertion_id"] and governed["assertion_id"] != ungoverned["assertion_id"]
        ambiguous_calls = _call_sites_of(baseline, "sendAmbiguous")
        assert len(ambiguous_calls) == 1
        ambiguous = ambiguous_calls[0]
        assert ambiguous["resolution"] == "MULTIPLE_CANDIDATES"
        assert ambiguous["assertion_id"] == ""
        assert len(ambiguous["candidates"]) >= 2
        ambiguous_owners = {
            parent
            for candidate in ambiguous["candidates"]
            for parent in (_labels(baseline).get(item, "") for item in _parents(baseline).get(str(candidate), []))
        }
        assert {"NotificationGateway", "SMTPClient"} <= ambiguous_owners
        invoice_sends = [
            call for call in _call_sites_of(baseline, "sendInvoice")
            if call["resolution"] == "RESOLVED" and call["target_label"] == "notificationGatewaySend"
        ]
        assert len(invoice_sends) == 1
        probe_calls = [call for call in _call_sites_of(baseline, "probeMethod") if "gateway.send" in str(call["text"])]
        assert len(probe_calls) == 1
        assert probe_calls[0]["resolution"] == "MULTIPLE_CANDIDATES"
        assert probe_calls[0]["assertion_id"] == ""
        assert probe_calls[0]["candidates"]

        # Direct bindings. Shape D is not stored: its tuple is the mechanical
        # program_invokes row already identified by the governed call site.
        knowledge = _knowledge_world(tmp_path / "governance.sqlite", KNOWLEDGE)
        try:
            _bind(knowledge, "owner", owner)
            _bind(knowledge, "occurrence", str(governed["call_site"]))
            _bind(knowledge, "relation", str(governed["assertion_id"]))
            _bind(knowledge, "ambiguous-occurrence", str(ambiguous["call_site"]))

            assert _bound_to(knowledge, "owner") == {owner}
            assert _bound_to(knowledge, "occurrence") == {str(governed["call_site"])}
            assert str(ungoverned["call_site"]) not in _bound_to(knowledge, "occurrence")
            assert str(invoice_sends[0]["call_site"]) not in _bound_to(knowledge, "occurrence")
            relation_assertion = _relation_assertion(baseline, str(governed["assertion_id"]))
            assert relation_assertion == {"call_site": governed["call_site"], "target": governed["target"]}
            assert _bound_to(knowledge, "relation") == {str(governed["assertion_id"])}
            # The other send has the same target and a different assertion.
            assert governed["target"] == ungoverned["target"]
            assert ungoverned["call_site"] != governed["call_site"]

            # Owner binding cannot say which of the two gateway sends it governs.
            owner_children = {str(call["call_site"]) for call in gateway_sends}
            assert len(owner_children & _bound_to(knowledge, "occurrence")) == 1
            # Ambiguous knowledge names the call site and no positive target.
            assert ambiguous["call_site"] in _bound_to(knowledge, "ambiguous-occurrence")
            assert ambiguous["target"] == ""
            candidate_labels = {_labels(baseline).get(candidate, "") for candidate in ambiguous["candidates"]}
            assert "send" in candidate_labels

            snapshots = {name: _build(tmp_path, name, source) for name, source in CONTROLS.items()}
            try:
                retarget = compare_program_spines(baseline, snapshots["A_retarget"])
                governed_now = _continued(retarget, str(governed["call_site"]))
                assert governed_now
                assert _region(snapshots["A_retarget"], governed_now) == "smtpClientSend(marked)"
                retarget_invokes = {row["call_site"]: row for row in _invokes(snapshots["A_retarget"])}
                assert retarget_invokes[governed_now]["target"] == _continued(retarget, _entity_named(baseline, "smtpClientSend", "callable"))
                # Shared-target retarget is not classified as retargeted: another
                # invocation of notificationGatewaySend is still present, so the
                # old tuple is removed and the new tuple is added.
                relation = retarget.delta.relations["program_invokes"]
                assert _relation_status(retarget, str(governed["call_site"]), str(governed["target"])) == "removed"
                assert any(row["new"]["call_site"] == governed_now for row in relation["added"])
                assert not relation["retargeted"]
                assert _continued(retarget, owner)
                new_ids = {row["assertion_id"] for row in _invokes(snapshots["A_retarget"])}
                assert str(governed["assertion_id"]) not in new_ids

                sibling = compare_program_spines(baseline, snapshots["F_sibling_retarget"])
                assert _relation_status(sibling, str(governed["call_site"]), str(governed["target"])) == "preserved"
                assert _relation_status(sibling, str(ungoverned["call_site"]), str(ungoverned["target"])) == "retargeted"
                assert _continued(sibling, str(governed["call_site"]))
                assert _continued(sibling, owner)

                shift = compare_program_spines(baseline, snapshots["D_shift"])
                shifted = _continued(shift, str(governed["call_site"]))
                assert shifted
                assert _relation_status(shift, str(governed["call_site"]), str(governed["target"])) == "preserved"
                assert _source_location(baseline, str(governed["call_site"])) != _source_location(snapshots["D_shift"], shifted)

                renamed = compare_program_spines(baseline, snapshots["E_rename_owner"])
                assert _continued(renamed, owner)
                assert _labels(snapshots["E_rename_owner"])[_continued(renamed, owner)] == "deliverReceipt"
                assert _relation_status(renamed, str(governed["call_site"]), str(governed["target"])) == "preserved"
                assert _continued(renamed, str(governed["call_site"]))

                added = compare_program_spines(baseline, snapshots["C_call_after"])
                assert _continued(added, str(governed["call_site"]))
                assert _relation_status(added, str(governed["call_site"]), str(governed["target"])) == "preserved"

                before = compare_program_spines(baseline, snapshots["C_call_before"])
                misjoined = _continued(before, str(governed["call_site"]))
                assert misjoined
                assert _region(snapshots["C_call_before"], misjoined) != _region(baseline, str(governed["call_site"]))

                reorder = compare_program_spines(baseline, snapshots["D_reorder"])
                reordered = _continued(reorder, str(governed["call_site"]))
                assert reordered
                assert _region(snapshots["D_reorder"], reordered) != _region(baseline, str(governed["call_site"]))

                body = compare_program_spines(baseline, snapshots["B_body_edit"])
                continued_call = _continued(body, str(governed["call_site"]))
                continued_owner = _continued(body, owner)
                assert continued_call and continued_owner
                assert _region(baseline, str(governed["call_site"])) == _region(snapshots["B_body_edit"], continued_call)
                assert _region(baseline, owner) != _region(snapshots["B_body_edit"], continued_owner)
                assert hashlib.sha256(_region(baseline, str(governed["call_site"])).encode()).hexdigest() == hashlib.sha256(
                    _region(snapshots["B_body_edit"], continued_call).encode()
                ).hexdigest()
            finally:
                for world in snapshots.values():
                    world.close()
        finally:
            knowledge.close()
    finally:
        baseline.close()


def _knowledge_world(path: Path, statement: str) -> ConstructionWorld:
    world = ConstructionWorld.create(path, world_id="governance-binding-experiment")
    text = RoleType.TEXT
    world.declare_relation(
        "governance_knowledge",
        [Role("knowledge", text), Role("statement", text)],
        description="The authoritative sentence. Not a semantic software identity.",
    )
    world.declare_relation(
        "governance_binding",
        [Role("knowledge", text), Role("shape", text), Role("target", text)],
        description="Direct binding from the sentence to one mechanical target id.",
    )
    observation = SourceObservation(
        provider="markdown",
        native_handle="policy.md",
        source_revision="sha256:" + hashlib.sha256(statement.encode()).hexdigest(),
        native_location="bytes:0:" + str(len(statement.encode())),
    )
    world.assert_tuple(
        "governance_knowledge",
        {"knowledge": "outbound-email", "statement": statement},
        origin=ConstructionOrigin.SEMANTIC,
        grounding=AssertionGrounding((observation,), construction_method="experimental authority sentence"),
    )
    return world


def _bind(world: ConstructionWorld, shape: str, target: str) -> None:
    observation = SourceObservation(
        provider="spine",
        native_handle=shape,
        source_revision="baseline",
        native_location="id",
    )
    world.assert_tuple(
        "governance_binding",
        {"knowledge": "outbound-email", "shape": shape, "target": target},
        origin=ConstructionOrigin.SEMANTIC,
        grounding=AssertionGrounding(
            (observation,),
            construction_method="direct evidence to mechanical spine id",
            extra={"relation_support": "SOURCE_EXPLICIT", "endpoint_resolution": {shape: "DETERMINISTIC" if shape != "ambiguous-occurrence" else "AMBIGUOUS"}},
        ),
    )


def _bound_to(world: ConstructionWorld, shape: str) -> set[str]:
    return {str(row["target"]) for row in world.relation_rows("governance_binding") if row["shape"] == shape}


def _relation_assertion(world: ConstructionWorld, assertion_id: str) -> dict[str, str]:
    rows = [
        {"call_site": str(row["call_site_id"]), "target": str(row["target_id"])}
        for row in world.query("SELECT _assertion_id, call_site_id, target_id FROM program_invokes")
        if str(row["_assertion_id"]) == assertion_id
    ]
    assert len(rows) == 1
    return rows[0]
