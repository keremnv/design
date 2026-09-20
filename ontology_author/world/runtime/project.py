"""Project root: construction.py (+ optional legacy Purpose) → World.

``construction.py`` is the current authoring shape, not ontology. Evidence is
the ordinary project tree.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path
from typing import Any

from ontology_author.world.core.contract import Contract, ContractAdmissionError
from ontology_author.world.core.model import (
    Completeness,
    CompletenessStatus,
    RelationMode,
    Role,
    RoleType,
    SemanticRefKind,
)

from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding, SourceObservation
from ontology_author.world.runtime.commit import (
    RunResult,
    discard_candidate,
    _replace_candidate,
    validate_contract_admission,
    write_sidecars,
)
from ontology_author.world.runtime.resolution import (
    ResolutionEvaluationError,
    resolve_world,
)
from ontology_author.world.runtime.purpose import Purpose
from ontology_author.world.runtime.source_helpers import Source
from ontology_author.world.runtime.world import (
    ConstructionError,
    ConstructionWorld,
    GroundingError,
)

WORLD_ID = "v0"


class Project:
    def __init__(
        self,
        root: Path | str,
        *,
        project_root: Path | str | None = None,
        contract: Contract | None = None,
        governance: Any | None = None,
        evidence_authority: Any | None = None,
        adjudication_authority: Any | None = None,
    ) -> None:
        self.root = Path(root)
        self.project_root = (
            Path(project_root)
            if project_root is not None
            else self._infer_project_root(self.root)
        )
        self.candidate_dir = self.root / "candidate"
        self.world_dir = self.root / "world"
        self.contract = contract or Contract.default()
        self.governance = governance
        # This is intentionally not exposed to construction.py.  It is an
        # external runtime binding used only after the candidate has recorded
        # its Warrant bases.
        self.evidence_authority = evidence_authority
        self.adjudication_authority = adjudication_authority

    @staticmethod
    def _infer_project_root(root: Path) -> Path:
        resolved = root.resolve()
        return resolved.parent.parent if resolved.parent.name == ".worlds" else resolved

    @property
    def world_path(self) -> Path:
        return self.world_dir / "world.sqlite"

    def run(
        self,
        construction: Path | str | None = None,
        *,
        purpose: str | Path | None = None,
    ) -> RunResult:
        """Construct and publish a candidate World.

        ``purpose=None`` is the governed path: no Purpose object or Purpose
        relation is created, and ``PURPOSE.md`` is never read implicitly.
        An explicit text-or-path request still builds the legacy Purpose
        context for old three-argument constructors; those constructors
        receive ``None`` when no purpose was requested.
        """
        construction_path = Path(construction) if construction else self.root / "construction.py"

        discard_candidate(self.candidate_dir)
        self.candidate_dir.mkdir(parents=True)
        db_path = self.candidate_dir / "world.sqlite"
        world = ConstructionWorld.create(
            db_path,
            world_id=WORLD_ID,
            contract=self.contract,
        )
        purpose_context: Purpose | None = None
        try:
            source = Source(self.project_root)
            namespace = _construction_namespace(
                source, world, self.contract, self.governance
            )
            if not construction_path.exists():
                raise ConstructionError("construction.py missing")
            code = construction_path.read_text(encoding="utf-8")
            import_roots = [str(self.root.resolve()), str(self.project_root.resolve())]
            inserted = [path for path in import_roots if path not in sys.path]
            for path in reversed(inserted):
                sys.path.insert(0, path)
            try:
                exec(compile(code, str(construction_path), "exec"), namespace, namespace)
                construct = namespace.get("construct")
                if not callable(construct):
                    raise ConstructionError(
                        "construction.py must define construct(source, world[, purpose])"
                    )
                purpose_text = _purpose_text_for_run(purpose)
                if purpose_text is not None:
                    purpose_context = Purpose(world, text=purpose_text)
                    namespace["purpose"] = purpose_context
                _invoke_constructor(construct, source, world, purpose_context)
            finally:
                for path in inserted:
                    try:
                        sys.path.remove(path)
                    except ValueError:
                        pass
            from ontology_author.world.runtime.construction_receipt import (
                build_construction_receipt,
            )

            write_sidecars(
                world,
                purpose_context.payload() if purpose_context is not None else None,
                _governance_payload(self.governance),
                _evidence_authority_payload(self.evidence_authority),
                _adjudication_authority_payload(self.adjudication_authority),
                build_construction_receipt(
                    entrypoint=construction_path,
                    workspace=self.root,
                    runtime_world_id=WORLD_ID,
                    contract_identity=self.contract.identity(),
                ),
            )
            report = validate_contract_admission(world)
            if not report.ok:
                world.close()
                world = None  # type: ignore[assignment]
                discard_candidate(self.candidate_dir)
                return RunResult(
                    succeeded=False,
                    reason=report.reason,
                    errors=tuple(
                        f"{item['relation']}:{item['assertion_id']}" for item in report.ungrounded
                    ),
                )
            if (
                self.contract.resolution_warrant_kinds
                or self.contract.adjudication_authority_kinds
            ):
                resolve_world(
                    world,
                    self.contract,
                    conflict_checker=_resolution_conflict_checker(self.governance),
                    evidence_authority=self.evidence_authority,
                    adjudication_authority=self.adjudication_authority,
                    source=source,
                )
            world.close()
            world = None  # type: ignore[assignment]
            _replace_candidate(self.candidate_dir, self.world_dir)
            return RunResult(succeeded=True, world_dir=self.world_dir)
        except GroundingError as exc:
            if world is not None:
                try:
                    world.close()
                except Exception:
                    pass
            discard_candidate(self.candidate_dir)
            return RunResult(succeeded=False, reason="ungrounded_world_base", errors=(str(exc),))
        except ContractAdmissionError as exc:
            if world is not None:
                try:
                    world.close()
                except Exception:
                    pass
            discard_candidate(self.candidate_dir)
            return RunResult(succeeded=False, reason=exc.reason, errors=(str(exc),))
        except ResolutionEvaluationError as exc:
            if world is not None:
                try:
                    world.close()
                except Exception:
                    pass
            discard_candidate(self.candidate_dir)
            return RunResult(
                succeeded=False,
                reason="resolution_error",
                errors=(str(exc),),
            )
        except ConstructionError as exc:
            if world is not None:
                try:
                    world.close()
                except Exception:
                    pass
            discard_candidate(self.candidate_dir)
            return RunResult(succeeded=False, reason="construction_error", errors=(str(exc),))
        except Exception as exc:
            if world is not None:
                try:
                    world.close()
                except Exception:
                    pass
            discard_candidate(self.candidate_dir)
            return RunResult(
                succeeded=False,
                reason="construction_error",
                errors=(f"{type(exc).__name__}: {exc}",),
            )

    def open_world(self) -> ConstructionWorld:
        if not self.world_path.exists():
            raise ConstructionError("no World has been built")
        return ConstructionWorld.open(self.world_path, world_id=WORLD_ID)


def _construction_namespace(
    source: Source,
    world: ConstructionWorld,
    contract: Contract,
    governance: Any | None,
) -> dict[str, Any]:
    return {
        "Source": Source,
        "source": source,
        "world": world,
        "Contract": Contract,
        "contract": contract,
        "governance": governance,
        "Role": Role,
        "RoleType": RoleType,
        "SemanticRefKind": SemanticRefKind,
        "RelationMode": RelationMode,
        "ConstructionOrigin": ConstructionOrigin,
        "AssertionGrounding": AssertionGrounding,
        "SourceObservation": SourceObservation,
        "Completeness": Completeness,
        "CompletenessStatus": CompletenessStatus,
        "GroundingError": GroundingError,
        "ConstructionError": ConstructionError,
    }


def _purpose_text_for_run(requested: str | Path | None) -> str | None:
    """Resolve an explicit Purpose request; ``None`` always disables it."""

    if requested is None:
        return None
    if isinstance(requested, Path):
        if not requested.is_file():
            raise ConstructionError(f"purpose file does not exist: {requested}")
        return requested.read_text(encoding="utf-8")
    if isinstance(requested, str):
        candidate = Path(requested)
        try:
            if "\n" not in requested and "\r" not in requested and candidate.is_file():
                return candidate.read_text(encoding="utf-8")
        except OSError:
            # A long or otherwise non-filesystem-shaped string is Purpose
            # text, not a path.  It is still a valid explicit request.
            pass
        return requested
    raise ConstructionError("purpose must be text, a file path, or None")


def _invoke_constructor(
    construct: Any,
    source: Source,
    world: ConstructionWorld,
    purpose: Purpose | None,
) -> None:
    """Call either the current two-argument or legacy three-argument shape."""

    try:
        signature = inspect.signature(construct)
    except (TypeError, ValueError):
        if purpose is None:
            construct(source, world)
        else:
            construct(source, world, purpose)
        return

    if purpose is not None:
        try:
            signature.bind(source, world, purpose)
        except TypeError:
            try:
                signature.bind(source, world, purpose=purpose)
            except TypeError:
                try:
                    signature.bind(source, world)
                except TypeError as exc:
                    raise ConstructionError(
                        "construction.py construct must accept (source, world) or "
                        "(source, world, purpose)"
                    ) from exc
                construct(source, world)
            else:
                construct(source, world, purpose=purpose)
        else:
            construct(source, world, purpose)
        return

    try:
        signature.bind(source, world)
    except TypeError:
        try:
            signature.bind(source, world, None)
        except TypeError:
            try:
                signature.bind(source, world, purpose=None)
            except TypeError as exc:
                raise ConstructionError(
                    "construction.py construct must accept (source, world) or "
                    "(source, world, purpose)"
                ) from exc
            construct(source, world, purpose=None)
        else:
            # Passing None here preserves a required legacy parameter without
            # inventing a no-op Purpose object.  Code that actually calls a
            # Purpose method will fail clearly at construction time and can
            # opt in to one.
            construct(source, world, None)
        return

    construct(source, world)


def _governance_payload(governance: Any | None) -> dict[str, Any] | None:
    if governance is None:
        return None
    inspector = getattr(governance, "inspection_payload", None)
    if not callable(inspector):
        raise ConstructionError(
            "governance must provide inspection_payload() for sealed-world inspection"
        )
    payload = inspector()
    if not isinstance(payload, dict):
        raise ConstructionError("governance inspection_payload() must return a mapping")
    return payload


def _resolution_conflict_checker(governance: Any | None) -> Any | None:
    if governance is None:
        return None
    checker = getattr(governance, "conflict_checker", None)
    return checker if callable(checker) else None


def _evidence_authority_payload(authority: Any | None) -> dict[str, Any] | None:
    if authority is None:
        return None
    inspector = getattr(authority, "inspection_payload", None)
    if not callable(inspector):
        raise ConstructionError(
            "evidence_authority must provide inspection_payload() for sealed-world inspection"
        )
    payload = inspector()
    if not isinstance(payload, dict):
        raise ConstructionError(
            "evidence_authority inspection_payload() must return a mapping"
        )
    return payload


def _adjudication_authority_payload(authority: Any | None) -> dict[str, Any] | None:
    if authority is None:
        return None
    inspector = getattr(authority, "inspection_payload", None)
    if not callable(inspector):
        raise ConstructionError(
            "adjudication_authority must provide inspection_payload() "
            "for sealed-world inspection"
        )
    payload = inspector()
    if not isinstance(payload, dict):
        raise ConstructionError(
            "adjudication_authority inspection_payload() must return a mapping"
        )
    return payload


__all__ = ["Project", "WORLD_ID"]
