"""Historical probe: how Core v1 can store a governance binding with no semantic identity.

Excluded from the default gate. Run with `pytest -m historical`.

Experimental representations only. The shapes share one sentence and one
call-site subject. No checkout, payment, or design vocabulary.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from ontology_author.world.core.contract import ContractAdmissionError
from ontology_author.world.core.model import (
    Grounding,
    GroundingKind,
    Role,
    RoleType,
    SemanticRefKind,
    WorldStoreError,
)
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding, SourceObservation
from ontology_author.world.runtime.world import ConstructionWorld

pytestmark = pytest.mark.historical

POLICY = "Outbound email must pass through NotificationGateway."
RUNBOOK = "Receipt mail uses the same gateway rule."
RECEIPT = "Receipt notices must pass through NotificationGateway."
CALL_SITE = "call-site:send-receipt"
OTHER_SITE = "call-site:send-invoice"
CANDIDATE_A = "call-site:candidate-a"
CANDIDATE_B = "call-site:candidate-b"
GATEWAY = "callable:notification-gateway-send"


def _observation(handle: str, text: str, location: str) -> SourceObservation:
    return SourceObservation(
        provider="markdown",
        native_handle=handle,
        source_revision="sha256:" + hashlib.sha256(text.encode()).hexdigest(),
        native_location=location,
    )


def _ground(*observations: SourceObservation, method: str, extra: dict | None = None) -> AssertionGrounding:
    return AssertionGrounding(observations, construction_method=method, extra=extra)


def _world(tmp_path: Path, name: str) -> ConstructionWorld:
    return ConstructionWorld.create(tmp_path / name, world_id=name)


def _roles_touching(world: ConstructionWorld, referent: str) -> list[str]:
    found = []
    for row in world.query("SELECT name FROM _world_relations ORDER BY name"):
        relation = str(row["name"])
        schema = world.relation_schema(relation)
        for role in schema["roles"]:
            if role["type"] != "REFERENT":
                continue
            if any(item[role["name"]] == referent for item in world.relation_rows(relation)):
                found.append(relation)
                break
    return found


def _source_handles(world: ConstructionWorld, assertion_id: str) -> set[str]:
    warrant = world.warrant_for_assertion(assertion_id)
    handles = set()
    for base in warrant["bases"]:
        detail = base.get("detail")
        if not isinstance(detail, dict):
            continue
        for observation in detail.get("observations") or []:
            if isinstance(observation, dict) and observation.get("native_handle"):
                handles.add(str(observation["native_handle"]))
        reference = str(base.get("reference") or "")
        if reference.startswith("markdown://"):
            handles.add(reference.split("://", 1)[1].split("@", 1)[0])
    return handles


def test_shape_a_domain_tuple_is_the_binding_and_is_not_generically_separable(tmp_path: Path) -> None:
    world = _world(tmp_path, "shape-a")
    try:
        for referent in (CALL_SITE, OTHER_SITE, GATEWAY):
            world.add_referent(referent, label=referent)
        text = RoleType.TEXT
        ref = RoleType.REFERENT
        world.declare_relation(
            "program_invokes",
            [Role("call_site", ref), Role("target", ref)],
            description="Mechanical caller to target. Not governance knowledge.",
        )
        world.declare_relation(
            "outbound_mail_passes",
            [Role("software_subject", ref)],
            description="Domain governance assertion. The tuple is the correspondence.",
        )
        world.declare_relation(
            "receipt_notice_passes",
            [Role("software_subject", ref)],
            description="A second domain governance assertion.",
        )
        policy = _observation("policy.md", POLICY, "bytes:0:48")
        runbook = _observation("runbook.md", RUNBOOK, "bytes:0:40")
        receipt = _observation("policy.md", RECEIPT, "bytes:49:100")
        world.assert_tuple(
            "program_invokes",
            {"call_site": CALL_SITE, "target": GATEWAY},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=_ground(policy, method="spine"),
        )
        first = world.assert_tuple(
            "outbound_mail_passes",
            {"software_subject": CALL_SITE},
            origin=ConstructionOrigin.SEMANTIC,
            grounding=_ground(
                policy,
                method="direct evidence to software subject",
                extra={"relation_support": "SOURCE_EXPLICIT", "endpoint_resolution": "DETERMINISTIC"},
            ),
        )
        second = world.assert_tuple(
            "outbound_mail_passes",
            {"software_subject": CALL_SITE},
            origin=ConstructionOrigin.SEMANTIC,
            grounding=_ground(runbook, method="direct evidence to software subject"),
        )
        world.assert_tuple(
            "outbound_mail_passes",
            {"software_subject": OTHER_SITE},
            origin=ConstructionOrigin.SEMANTIC,
            grounding=_ground(policy, runbook, method="direct evidence to software subject"),
        )
        world.assert_tuple(
            "receipt_notice_passes",
            {"software_subject": CALL_SITE},
            origin=ConstructionOrigin.SEMANTIC,
            grounding=_ground(receipt, method="direct evidence to software subject"),
        )

        assert first.assertion_id == second.assertion_id
        assert first.inserted is True and second.inserted is False
        assert _source_handles(world, first.assertion_id) == {"policy.md", "runbook.md"}
        subjects = {row["software_subject"] for row in world.relation_rows("outbound_mail_passes")}
        assert subjects == {CALL_SITE, OTHER_SITE}
        propositions = _roles_touching(world, CALL_SITE)
        assert propositions == ["outbound_mail_passes", "program_invokes", "receipt_notice_passes"]
        schema = world.relation_schema("outbound_mail_passes")
        assert "governance" not in schema
        assert all(role.get("reference_kind") in (None, "") for role in schema["roles"])
    finally:
        world.close()


def test_shape_b_assertion_grounding_records_support_not_concern(tmp_path: Path) -> None:
    world = _world(tmp_path, "shape-b")
    try:
        world.add_referent(CALL_SITE, label=CALL_SITE)
        ref = RoleType.REFERENT
        text = RoleType.TEXT
        world.declare_relation("governance_proposition", [Role("statement", text)])
        world.declare_relation("governance_binding", [Role("software_subject", ref)])
        policy = _observation("policy.md", POLICY, "bytes:0:48")
        proposition = world.assert_tuple(
            "governance_proposition",
            {"statement": POLICY},
            origin=ConstructionOrigin.SEMANTIC,
            grounding=_ground(policy, method="record the sentence"),
        )
        binding = world.assert_tuple(
            "governance_binding",
            {"software_subject": CALL_SITE},
            origin=ConstructionOrigin.SEMANTIC,
            grounding=_ground(policy, method="binding whose tuple does not name the proposition"),
        )
        store = world._inner._store
        store.assert_tuple(
            "governance_binding",
            {"software_subject": CALL_SITE},
            grounding=[Grounding(GroundingKind.ASSERTION, proposition.assertion_id)],
        )
        kinds = {row["kind"] for row in store.groundings("ASSERTION", binding.assertion_id)}
        assert "ASSERTION" in kinds
        supports = world._inner.construction_supports_for_assertion(binding.assertion_id)
        assert all(item["kind"] == "WORLD" for item in supports)
        assert world.retract_tuple("governance_proposition", {"statement": POLICY})
        dangling = [
            row["reference"]
            for row in store.groundings("ASSERTION", binding.assertion_id)
            if row["kind"] == "ASSERTION"
        ]
        assert dangling == [proposition.assertion_id]
        assert world.relation_rows("governance_binding") == [{"software_subject": CALL_SITE}]
    finally:
        world.close()


def test_shape_c_proposition_referent_answers_binding_reads_without_semantic_identity(tmp_path: Path) -> None:
    world = _world(tmp_path, "shape-c")
    try:
        subjects = (CALL_SITE, OTHER_SITE, CANDIDATE_A, CANDIDATE_B, GATEWAY)
        for referent in subjects:
            world.add_referent(referent, label=referent)
        outbound = "proposition:outbound-mail"
        receipt = "proposition:receipt-notice"
        replaced = "proposition:replaced-rule"
        semantic = "semantic:outbound-mail-rule"
        for referent in (outbound, receipt, replaced, semantic):
            world.add_referent(referent, label=referent)
        ref = RoleType.REFERENT
        text = RoleType.TEXT
        world.declare_relation(
            "program_invokes",
            [Role("call_site", ref), Role("target", ref)],
        )
        world.declare_relation(
            "governance_proposition",
            [Role("proposition", ref), Role("statement", text), Role("domain_relation", text)],
        )
        world.declare_relation(
            "governance_binding",
            [Role("proposition", ref), Role("software_subject", ref)],
        )
        world.declare_relation(
            "governance_candidate",
            [Role("proposition", ref), Role("software_subject", ref)],
        )
        world.declare_relation(
            "proposition_semantic_subject",
            [Role("proposition", ref), Role("semantic_subject", ref)],
        )
        policy = _observation("policy.md", POLICY, "bytes:0:48")
        runbook = _observation("runbook.md", RUNBOOK, "bytes:0:40")
        receipt_obs = _observation("policy.md", RECEIPT, "bytes:49:100")
        replacement = _observation("replacement.md", "Notices leave only through the notice hub.", "bytes:0:44")
        world.assert_tuple(
            "program_invokes",
            {"call_site": CALL_SITE, "target": GATEWAY},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=_ground(policy, method="spine"),
        )
        outbound_row = world.assert_tuple(
            "governance_proposition",
            {
                "proposition": outbound,
                "statement": POLICY,
                "domain_relation": "outbound_mail_passes",
            },
            origin=ConstructionOrigin.SEMANTIC,
            grounding=_ground(policy, method="proposition from policy"),
        )
        world.assert_tuple(
            "governance_proposition",
            {
                "proposition": outbound,
                "statement": POLICY,
                "domain_relation": "outbound_mail_passes",
            },
            origin=ConstructionOrigin.SEMANTIC,
            grounding=_ground(runbook, method="same proposition, second region"),
        )
        world.assert_tuple(
            "governance_proposition",
            {
                "proposition": receipt,
                "statement": RECEIPT,
                "domain_relation": "receipt_notice_passes",
            },
            origin=ConstructionOrigin.SEMANTIC,
            grounding=_ground(receipt_obs, method="second proposition"),
        )
        world.assert_tuple(
            "governance_proposition",
            {
                "proposition": replaced,
                "statement": "Notices leave only through the notice hub.",
                "domain_relation": "outbound_mail_passes",
            },
            origin=ConstructionOrigin.SEMANTIC,
            grounding=_ground(
                replacement,
                method="cross-replacement proposition",
                extra={"equivalence": "experimental-rule-equivalence"},
            ),
        )
        for subject in (CALL_SITE, OTHER_SITE):
            world.assert_tuple(
                "governance_binding",
                {"proposition": outbound, "software_subject": subject},
                origin=ConstructionOrigin.SEMANTIC,
                grounding=_ground(
                    policy,
                    method="correspondence to a call site",
                    extra={"relation_support": "SOURCE_EXPLICIT", "endpoint_resolution": "DETERMINISTIC"},
                ),
            )
        world.assert_tuple(
            "governance_binding",
            {"proposition": receipt, "software_subject": CALL_SITE},
            origin=ConstructionOrigin.SEMANTIC,
            grounding=_ground(
                receipt_obs,
                method="second proposition, same subject",
                extra={"relation_support": "SOURCE_EXPLICIT", "endpoint_resolution": "DETERMINISTIC"},
            ),
        )
        world.assert_tuple(
            "governance_binding",
            {"proposition": replaced, "software_subject": GATEWAY},
            origin=ConstructionOrigin.SEMANTIC,
            grounding=_ground(replacement, method="endpoint after replacement"),
        )
        world.assert_tuple(
            "proposition_semantic_subject",
            {"proposition": replaced, "semantic_subject": semantic},
            origin=ConstructionOrigin.SEMANTIC,
            grounding=_ground(
                replacement,
                method="semantic identity earned by cross-replacement",
                extra={"equivalence": "experimental-rule-equivalence"},
            ),
        )
        for candidate in (CANDIDATE_A, CANDIDATE_B):
            world.assert_tuple(
                "governance_candidate",
                {"proposition": outbound, "software_subject": candidate},
                origin=ConstructionOrigin.SEMANTIC,
                grounding=_ground(
                    policy,
                    method="unresolved candidate",
                    extra={"endpoint_resolution": "AMBIGUOUS"},
                ),
            )

        concerning_receipt = {
            row["proposition"]
            for row in world.relation_rows("governance_binding")
            if row["software_subject"] == CALL_SITE
        }
        assert concerning_receipt == {outbound, receipt}
        outbound_subjects = {
            row["software_subject"]
            for row in world.relation_rows("governance_binding")
            if row["proposition"] == outbound
        }
        assert outbound_subjects == {CALL_SITE, OTHER_SITE}
        assert _source_handles(world, outbound_row.assertion_id) == {"policy.md", "runbook.md"}
        binding_id = world._inner._store.assertion_id_for_tuple(
            "governance_binding",
            {"proposition": outbound, "software_subject": CALL_SITE},
        )
        warrant = world.warrant_for_assertion(binding_id)
        extras = [
            base["detail"]["extra"]
            for base in warrant["bases"]
            if isinstance(base.get("detail"), dict) and "extra" in base["detail"]
        ]
        assert {"relation_support": "SOURCE_EXPLICIT", "endpoint_resolution": "DETERMINISTIC"} in extras
        established = {
            row["software_subject"]
            for row in world.relation_rows("governance_binding")
            if row["proposition"] == outbound
        }
        candidates = {
            row["software_subject"]
            for row in world.relation_rows("governance_candidate")
            if row["proposition"] == outbound
        }
        assert candidates == {CANDIDATE_A, CANDIDATE_B}
        assert established.isdisjoint(candidates)
        semantic_links = world.relation_rows("proposition_semantic_subject")
        assert semantic_links == [{"proposition": replaced, "semantic_subject": semantic}]
        assert outbound not in {row["proposition"] for row in semantic_links}
        meanings = {
            row["proposition"]: row["domain_relation"]
            for row in world.relation_rows("governance_proposition")
        }
        assert meanings[outbound] == "outbound_mail_passes"
        assert "program_invokes" not in {
            row["domain_relation"] for row in world.relation_rows("governance_proposition")
        }
        with pytest.raises(WorldStoreError, match="unknown referent"):
            world.assert_tuple(
                "governance_binding",
                {"proposition": outbound, "software_subject": "call-site:missing"},
                origin=ConstructionOrigin.SEMANTIC,
                grounding=_ground(policy, method="missing subject"),
            )
    finally:
        world.close()


def test_shape_d_text_assertion_id_survives_retraction_of_its_target(tmp_path: Path) -> None:
    world = _world(tmp_path, "shape-d")
    try:
        world.add_referent(CALL_SITE, label=CALL_SITE)
        world.declare_relation("governance_proposition", [Role("statement", RoleType.TEXT)])
        world.declare_relation(
            "governance_binding",
            [Role("proposition_assertion_id", RoleType.TEXT), Role("software_subject", RoleType.REFERENT)],
        )
        policy = _observation("policy.md", POLICY, "bytes:0:48")
        proposition = world.assert_tuple(
            "governance_proposition",
            {"statement": POLICY},
            origin=ConstructionOrigin.SEMANTIC,
            grounding=_ground(policy, method="record the sentence"),
        )
        world.assert_tuple(
            "governance_binding",
            {"proposition_assertion_id": proposition.assertion_id, "software_subject": CALL_SITE},
            origin=ConstructionOrigin.SEMANTIC,
            grounding=_ground(policy, method="unchecked assertion id"),
        )
        schema = world.relation_schema("governance_binding")
        id_role = next(role for role in schema["roles"] if role["name"] == "proposition_assertion_id")
        assert id_role["type"] == "TEXT"
        assert not id_role.get("reference_kind")
        assert world.retract_tuple("governance_proposition", {"statement": POLICY})
        remaining = world.relation_rows("governance_binding")
        assert remaining == [
            {"proposition_assertion_id": proposition.assertion_id, "software_subject": CALL_SITE}
        ]
        assert world.warrant_for_assertion(
            world._inner._store.assertion_id_for_tuple("governance_binding", remaining[0])
        )["relation"] == "governance_binding"
    finally:
        world.close()


def test_default_contract_rejects_a_commitment_role_for_the_proposition(tmp_path: Path) -> None:
    world = _world(tmp_path, "commitment-role")
    try:
        world.add_referent(CALL_SITE, label=CALL_SITE)
        world.declare_relation("governance_proposition", [Role("statement", RoleType.TEXT)])
        world.declare_relation(
            "governance_binding",
            [
                Role("proposition", RoleType.TEXT, SemanticRefKind.COMMITMENT),
                Role("software_subject", RoleType.REFERENT),
            ],
        )
        policy = _observation("policy.md", POLICY, "bytes:0:48")
        proposition = world.assert_tuple(
            "governance_proposition",
            {"statement": POLICY},
            origin=ConstructionOrigin.SEMANTIC,
            grounding=_ground(policy, method="record the sentence"),
        )
        with pytest.raises(ContractAdmissionError, match="semantic-reference"):
            world.assert_tuple(
                "governance_binding",
                {"proposition": proposition.assertion_id, "software_subject": CALL_SITE},
                origin=ConstructionOrigin.SEMANTIC,
                grounding=_ground(policy, method="commitment reference"),
            )
    finally:
        world.close()
