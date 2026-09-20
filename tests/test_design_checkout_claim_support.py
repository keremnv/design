"""Claim-level material evidence support for design_checkout availability.

Authority standing and material-region currency are evaluated separately.
Maintenance is deterministic: recorded line range + content digest versus the
current source. No model calls.
"""

from __future__ import annotations

import inspect
import json
import shutil
from pathlib import Path

from ontology_author.world.core.model import ObligationState, ResolutionStatus
from ontology_author.world.explorer import WorldExplorerAdapter
from ontology_author.world.runtime.entry import rebuild
from ontology_author.world.runtime.material_support import (
    SUPPORT_CHANGED,
    SUPPORT_MISSING,
    SUPPORT_PRESERVED,
    reproduce_material_support,
)
from ontology_author.world.runtime.source_helpers import Source

from profiles.design_checkout import (
    DESIGN_CONTRACT,
    load_design_law,
    load_evidence_authority,
)
from profiles.design_checkout.evidence import (
    AVAILABILITY_REQUIREMENT_HANDLE,
    AVAILABILITY_REQUIREMENT_LINES,
)


FIXTURE = Path(__file__).parents[1] / "profiles" / "design_checkout" / "fixture"
REQUIREMENTS = AVAILABILITY_REQUIREMENT_HANDLE


def _copy(tmp_path: Path, name: str = "claim-support") -> Path:
    root = tmp_path / name
    shutil.copytree(FIXTURE, root)
    return root


def _rebuild(root: Path, *, evidence_authority=None):
    result = rebuild(
        root,
        contract=DESIGN_CONTRACT,
        governance=load_design_law(root),
        evidence_authority=evidence_authority or load_evidence_authority(root),
    )
    assert result.succeeded, result.errors
    return result


def _availability_id(explorer: WorldExplorerAdapter) -> str:
    return next(
        item["obligation_id"]
        for item in explorer.obligations()["obligations"]
        if item.get("dimension") == "availability"
    )


def _write_requirements(root: Path, text: str) -> None:
    (root / REQUIREMENTS).write_text(text, encoding="utf-8")


def test_authoritative_file_with_current_region_is_sufficient(tmp_path: Path):
    root = _copy(tmp_path)
    _rebuild(root)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        obligation_id = _availability_id(explorer)
        recorded = explorer.resolution(obligation_id)
        assert recorded["status"] == ResolutionStatus.RESOLVED.value
        selected = recorded["selected_commitment_id"]
        support = explorer.claim_support(selected, source_root=root)
        assert support["current"]["status"] == SUPPORT_PRESERVED
        assert support["recorded"]["native_location"] == "lines:{}-{}".format(
            *AVAILABILITY_REQUIREMENT_LINES
        )
        assert support["recorded"]["native_handle"] == REQUIREMENTS
        assessment = recorded["candidate_assessments"][0]
        assert assessment["status"] == "SUFFICIENT"
        assert "APPROVED_REQUIREMENT" in assessment["warrant_authorities"]
        assert assessment["material_support"]["status"] == SUPPORT_PRESERVED
        current = explorer.current_resolution(obligation_id, source_root=root)
        assert current["status"] == ResolutionStatus.RESOLVED.value


def test_rebuild_after_removal_is_new_construction_not_old_basis_reuse(tmp_path: Path):
    root = _copy(tmp_path, "rebuild-removal")
    _rebuild(root)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        obligation_id = _availability_id(explorer)
        selected = explorer.resolution(obligation_id)["selected_commitment_id"]
        old_digest = explorer.claim_support(selected, source_root=root)["recorded"][
            "content_digest"
        ]
    text = (root / REQUIREMENTS).read_text(encoding="utf-8")
    _write_requirements(
        root,
        text.replace(
            "The mobile checkout must preserve purchase confidence. At the commitment\n"
            "point, the shopper must be able to see the order total and the promo-code\n"
            "entry. While entering payment details, the critical order summary (including\n"
            "the total) must remain available without losing the payment task.\n\n",
            "",
        ),
    )
    _rebuild(root)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        obligation_id = _availability_id(explorer)
        recorded = explorer.resolution(obligation_id)
        selected = (
            recorded["selected_commitment_id"]
            or explorer.obligation(obligation_id)["candidates"][0]["commitment_id"]
        )
        support = explorer.claim_support(selected, source_root=root)
        assert support["recorded"] is None or support["recorded"]["content_digest"] != old_digest
        assert recorded["status"] == ResolutionStatus.INSUFFICIENT_WARRANT.value


def test_unrelated_edit_preserves_recorded_support(tmp_path: Path):
    root = _copy(tmp_path, "unrelated")
    _rebuild(root)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        obligation_id = _availability_id(explorer)
        selected = explorer.resolution(obligation_id)["selected_commitment_id"]
        before = explorer.claim_support(selected, source_root=root)
        before_file = Source(root).file_hash(REQUIREMENTS)

    text = (root / REQUIREMENTS).read_text(encoding="utf-8")
    _write_requirements(
        root,
        text.replace(
            "That is a design determination for the\nconstructor to make.",
            "That is a design determination for the\nconstructor to make. Extra note.",
        ),
    )
    assert Source(root).file_hash(REQUIREMENTS) != before_file
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        obligation_id = _availability_id(explorer)
        selected = explorer.resolution(obligation_id)["selected_commitment_id"]
        after = explorer.claim_support(selected, source_root=root)
        assert after["current"]["status"] == SUPPORT_PRESERVED
        assert after["recorded"]["content_digest"] == before["recorded"]["content_digest"]
        current = explorer.current_resolution(obligation_id, source_root=root)
        assert current["status"] == ResolutionStatus.RESOLVED.value
        bindings = [
            item["authority"]
            for item in explorer.evidence_authority()["bindings"]
        ]
        assert "APPROVED_REQUIREMENT" in bindings

    _rebuild(root)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        obligation_id = _availability_id(explorer)
        assert explorer.resolution(obligation_id)["status"] == (
            ResolutionStatus.RESOLVED.value
        )


def test_formatting_only_edit_invalidates_byte_identical_support(tmp_path: Path):
    root = _copy(tmp_path, "formatting")
    _rebuild(root)
    text = (root / REQUIREMENTS).read_text(encoding="utf-8")
    _write_requirements(
        root,
        text.replace("must remain available", "must  remain available"),
    )
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        obligation_id = _availability_id(explorer)
        selected = explorer.resolution(obligation_id)["selected_commitment_id"]
        support = explorer.claim_support(selected, source_root=root)
        assert support["current"]["status"] == SUPPORT_CHANGED
        current = explorer.current_resolution(obligation_id, source_root=root)
        assert current["status"] == ResolutionStatus.INSUFFICIENT_WARRANT.value


def test_material_wording_change_invalidates_automatic_support_reuse(tmp_path: Path):
    root = _copy(tmp_path, "wording")
    _rebuild(root)
    text = (root / REQUIREMENTS).read_text(encoding="utf-8")
    _write_requirements(
        root,
        text.replace(
            "must remain available without losing the payment task.",
            "should generally remain visible during payment.",
        ),
    )
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        obligation_id = _availability_id(explorer)
        selected = explorer.resolution(obligation_id)["selected_commitment_id"]
        support = explorer.claim_support(selected, source_root=root)
        assert support["current"]["status"] == SUPPORT_CHANGED
        current = explorer.current_resolution(obligation_id, source_root=root)
        assert current["status"] == ResolutionStatus.INSUFFICIENT_WARRANT.value
        assert current["selected_commitment_id"] in (None, "")
        assert explorer.resolution(obligation_id)["status"] == (
            ResolutionStatus.RESOLVED.value
        )
        assert explorer.assertion(selected)["values"]["subject"] == "order_summary"
        assert explorer.obligation(obligation_id)["state"] == (
            ObligationState.RESOLVED.value
        )
        current_detail = explorer.current_resolution(obligation_id, source_root=root)
        assert "APPROVED_REQUIREMENT" in current_detail["candidate_assessments"][0][
            "warrant_authorities"
        ]
        assert current_detail["candidate_assessments"][0]["material_support"][
            "status"
        ] == SUPPORT_CHANGED


def test_requirement_removal_invalidates_support_without_negative_claim(tmp_path: Path):
    root = _copy(tmp_path, "removed")
    _rebuild(root)
    text = (root / REQUIREMENTS).read_text(encoding="utf-8")
    _write_requirements(
        root,
        text.replace(
            "The mobile checkout must preserve purchase confidence. At the commitment\n"
            "point, the shopper must be able to see the order total and the promo-code\n"
            "entry. While entering payment details, the critical order summary (including\n"
            "the total) must remain available without losing the payment task.\n\n",
            "",
        ),
    )
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        obligation_id = _availability_id(explorer)
        generated_ids = {
            item["obligation_id"] for item in explorer.obligations()["obligations"]
        }
        assert obligation_id in generated_ids
        selected = explorer.resolution(obligation_id)["selected_commitment_id"]
        support = explorer.claim_support(selected, source_root=root)
        assert support["current"]["status"] in {SUPPORT_CHANGED, SUPPORT_MISSING}
        current = explorer.current_resolution(obligation_id, source_root=root)
        assert current["status"] == ResolutionStatus.INSUFFICIENT_WARRANT.value
        assert explorer.rows("does_not_remain_available_during")["total"] == 0
        bindings = explorer.evidence_authority()["bindings"]
        assert any(item["authority"] == "APPROVED_REQUIREMENT" for item in bindings)
        assert explorer.assertion(selected)["commitment_id"] == selected
        current_detail = explorer.current_resolution(obligation_id, source_root=root)
        assert current_detail["state"] == ObligationState.UNRESOLVED.value
        assert "APPROVED_REQUIREMENT" in current_detail["candidate_assessments"][0][
            "warrant_authorities"
        ]
        sealed = explorer.obligations()["obligations"]
        assert {item["dimension"] for item in sealed} == {
            "availability",
            "priority",
            "goal_support",
        }
        assert explorer.resolution(obligation_id)["status"] == (
            ResolutionStatus.RESOLVED.value
        )


def test_requirement_reversal_does_not_create_a_negative_claim(tmp_path: Path):
    root = _copy(tmp_path, "reversed")
    _rebuild(root)
    text = (root / REQUIREMENTS).read_text(encoding="utf-8")
    _write_requirements(
        root,
        text.replace("must remain available", "must not remain available"),
    )
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        obligation_id = _availability_id(explorer)
        selected = explorer.resolution(obligation_id)["selected_commitment_id"]
        support = explorer.claim_support(selected, source_root=root)
        assert support["current"]["status"] == SUPPORT_CHANGED
        current = explorer.current_resolution(obligation_id, source_root=root)
        assert current["status"] == ResolutionStatus.INSUFFICIENT_WARRANT.value
        assert explorer.rows("does_not_remain_available_during")["total"] == 0
        assert explorer.assertion(selected)["relation"] == "remains_available_during"


def test_authority_failure_is_distinct_from_material_support_failure(tmp_path: Path):
    root = _copy(tmp_path, "authority-vs-support")
    _rebuild(root)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        obligation_id = _availability_id(explorer)
        selected = explorer.resolution(obligation_id)["selected_commitment_id"]
        preserved = explorer.claim_support(selected, source_root=root)
        assert preserved["current"]["status"] == SUPPORT_PRESERVED

    manifest = json.loads((root / "evidence-authorities.json").read_text(encoding="utf-8"))
    manifest["bindings"] = [
        item
        for item in manifest["bindings"]
        if item["authority"] != "APPROVED_REQUIREMENT"
    ]
    (root / "evidence-authorities.json").write_text(json.dumps(manifest), encoding="utf-8")
    _rebuild(root)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        obligation_id = _availability_id(explorer)
        recorded = explorer.resolution(obligation_id)
        assert recorded["status"] == ResolutionStatus.INSUFFICIENT_WARRANT.value
        assessment = recorded["candidate_assessments"][0]
        assert "APPROVED_REQUIREMENT" not in assessment["warrant_authorities"]
        assert assessment["material_support"]["status"] == SUPPORT_PRESERVED
        selected = explorer.obligation(obligation_id)["candidates"][0]["commitment_id"]
        support = explorer.claim_support(selected, source_root=root)
        assert support["current"]["status"] == SUPPORT_PRESERVED


def test_fresh_agent_can_inspect_support_observation_and_currency(tmp_path: Path):
    root = _copy(tmp_path, "inspect")
    _rebuild(root)
    text = (root / REQUIREMENTS).read_text(encoding="utf-8")
    _write_requirements(
        root,
        text.replace("must remain available", "must remain nearby"),
    )
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        obligation_id = _availability_id(explorer)
        recorded = explorer.resolution(obligation_id)
        selected = recorded["selected_commitment_id"]
        support = explorer.claim_support(selected, source_root=root)
        identities = {
            f"{item['provider']}://{item['native_handle']}"
            for item in support["authority"]["warrant_source_identities"]
            if item.get("native_handle")
        }
        assert "file://checkout-requirements.md" in identities
        locator = next(
            item
            for item in support["authority"]["warrant_source_identities"]
            if item.get("native_handle") == REQUIREMENTS
        )
        assert locator["native_location"] == "lines:3-6"
        assert locator["source_revision"]
        assert support["current"]["status"] == SUPPORT_CHANGED
        current = explorer.current_resolution(obligation_id, source_root=root)
        assert "material evidence basis" in current["reason"]
        assert "APPROVED_REQUIREMENT" in current["candidate_assessments"][0][
            "warrant_authorities"
        ]


def test_support_maintenance_is_deterministic_and_model_free():
    from ontology_author.world.runtime import material_support as module

    source = inspect.getsource(module)
    assert "cursor-agent" not in source
    assert "openai" not in source.lower()
    assert "embedding" not in source.lower()
    assert "llm" not in source.lower()
    assert inspect.getsource(reproduce_material_support)


def test_construction_receipt_is_not_the_claim_evidence_basis(tmp_path: Path):
    root = _copy(tmp_path, "receipt-vs-support")
    _rebuild(root)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        receipt = explorer.construction_receipt()
        obligation_id = _availability_id(explorer)
        selected = explorer.resolution(obligation_id)["selected_commitment_id"]
        support = explorer.claim_support(selected, source_root=root)
        assert receipt["entrypoint"] == "construction.py"
        assert support["recorded"]["native_handle"] == REQUIREMENTS
        assert receipt["source_digest"] != support["recorded"]["content_digest"]


def test_source_observation_pointer_omits_payload_and_records_locator(tmp_path: Path):
    root = _copy(tmp_path, "observation-shape")
    _rebuild(root)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        obligation_id = _availability_id(explorer)
        selected = explorer.resolution(obligation_id)["selected_commitment_id"]
        warrant = explorer.assertion(selected)["warrant"]
        source_bases = [
            base["detail"]
            for base in warrant["bases"]
            if base["kind"] == "SOURCE"
            and base["detail"].get("native_handle") == REQUIREMENTS
        ]
        assert source_bases
        pointer = source_bases[0]
        assert set(pointer) >= {
            "provider",
            "native_handle",
            "source_revision",
            "native_location",
        }
        assert "payload" not in pointer
        assert pointer["native_location"] == "lines:3-6"
        world_extra = next(
            base["detail"]["extra"]
            for base in warrant["bases"]
            if base["kind"] == "WORLD" and "extra" in base.get("detail", {})
        )
        assert world_extra["material_support"]["content_digest"].startswith("sha256:")


def test_material_support_is_not_a_kernel_schema(tmp_path: Path):
    kernel = (
        Path(__file__).resolve().parents[1]
        / "ontology_author"
        / "world"
        / "core"
        / "kernel.py"
    ).read_text(encoding="utf-8")
    store = (
        Path(__file__).resolve().parents[1]
        / "ontology_author"
        / "world"
        / "core"
        / "store.py"
    ).read_text(encoding="utf-8")
    assert "material_support" not in kernel
    assert "material_support" not in store
    root = _copy(tmp_path, "kernel-check")
    _rebuild(root)
    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        assert explorer.construction_receipt()["entrypoint"] == "construction.py"
