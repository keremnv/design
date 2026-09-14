"""Small governance-side checks over the generic Ontology Author substrate.

This module deliberately does not change World storage. It gives governance
construction code a vocabulary for identity planes and for the finer support
metadata that generic ``ConstructionOrigin`` cannot carry by itself.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from ontology_author.world.core.source import AssertionGrounding, SourceObservation


class IdentityPlane(StrEnum):
    SOURCE = "SOURCE"
    SEMANTIC = "SEMANTIC"
    PROGRAM = "PROGRAM"


class SupportMode(StrEnum):
    MECHANICALLY_SOURCE_NATIVE = "mechanically_source_native"
    SOURCE_EXPLICIT = "source_explicit"
    SOURCE_STRUCTURAL = "source_structural"
    CROSS_EVIDENCE_INFERRED = "cross_evidence_inferred"
    HYPOTHESIZED = "hypothesized"


class ReferentResolution(StrEnum):
    NATIVE_ID = "native_id"
    DETERMINISTIC = "deterministic"
    SOURCE_DEFINED = "source_defined"
    AGENT_RESOLVED = "agent_resolved"
    AMBIGUOUS = "ambiguous"


class GovernanceValidationError(ValueError):
    """A governance-specific identity or support invariant was violated."""


def namespaced_referent_id(plane: IdentityPlane | str, local_id: str) -> str:
    """Return a stable, visibly plane-qualified governance referent ID."""

    try:
        selected = IdentityPlane(plane)
    except ValueError as exc:
        raise GovernanceValidationError(f"unknown identity plane {plane!r}") from exc
    local = str(local_id or "").strip()
    if not local:
        raise GovernanceValidationError("a namespaced referent local ID must be non-empty")
    return f"{selected.value.lower()}:{local}"


def identity_plane(referent_id: str) -> IdentityPlane:
    """Read the plane prefix of a governance namespaced referent ID."""

    prefix, separator, _local = str(referent_id or "").partition(":")
    if not separator:
        raise GovernanceValidationError(
            f"governance referent {referent_id!r} has no identity-plane namespace"
        )
    try:
        return IdentityPlane(prefix.upper())
    except ValueError as exc:
        raise GovernanceValidationError(
            f"governance referent {referent_id!r} has unknown identity plane"
        ) from exc


def validate_relation_identity_planes(
    values: Mapping[str, Any], expected: Mapping[str, IdentityPlane | str]
) -> None:
    """Require every identity-bearing relation value to use its intended plane.

    This is an application-side check. Generic World relations intentionally
    remain unaware of governance identity planes.
    """

    if set(values) != set(expected):
        raise GovernanceValidationError(
            f"relation identity roles {sorted(expected)} do not match values {sorted(values)}"
        )
    for role, expected_plane in expected.items():
        actual = identity_plane(str(values[role]))
        try:
            wanted = IdentityPlane(expected_plane)
        except ValueError as exc:
            raise GovernanceValidationError(
                f"unknown expected identity plane {expected_plane!r} for {role!r}"
            ) from exc
        if actual is not wanted:
            raise GovernanceValidationError(
                f"{role!r} requires {wanted.value} identity, got {actual.value}"
            )


@dataclass(frozen=True)
class GovernanceSupport:
    """Fine support metadata carried through existing assertion grounding.

    The metadata is intentionally an application value object, not a new
    kernel primitive. Source observations are required so a durable support
    record has a reconstructible evidence path. A cross-evidence inference can
    therefore list all observations that established it.
    """

    support_mode: SupportMode | str
    observations: tuple[SourceObservation, ...]
    referent_resolution: Mapping[str, ReferentResolution | str] = field(
        default_factory=dict
    )
    construction_method: str = ""

    def __post_init__(self) -> None:
        try:
            mode = SupportMode(self.support_mode)
        except ValueError as exc:
            raise GovernanceValidationError(
                f"unknown governance support mode {self.support_mode!r}"
            ) from exc
        object.__setattr__(self, "support_mode", mode)
        observations = tuple(self.observations)
        if not observations:
            raise GovernanceValidationError(
                "durable governance support needs reconstructible source observations"
            )
        for observation in observations:
            if not isinstance(observation, SourceObservation):
                raise GovernanceValidationError(
                    "governance support observations must be SourceObservation values"
                )
            if not all(
                str(value or "").strip()
                for value in (
                    observation.provider,
                    observation.native_handle,
                    observation.source_revision,
                    observation.native_location,
                )
            ):
                raise GovernanceValidationError(
                    "each governance source observation needs provider, handle, "
                    "revision, and location"
                )
        resolutions: dict[str, ReferentResolution] = {}
        for role, resolution in dict(self.referent_resolution).items():
            try:
                resolutions[str(role)] = ReferentResolution(resolution)
            except ValueError as exc:
                raise GovernanceValidationError(
                    f"unknown referent resolution {resolution!r} for {role!r}"
                ) from exc
        object.__setattr__(self, "observations", observations)
        object.__setattr__(self, "referent_resolution", resolutions)

    def assertion_grounding(self) -> AssertionGrounding:
        """Encode support metadata using the existing grounding boundary."""

        return AssertionGrounding(
            observations=self.observations,
            construction_method=self.construction_method,
            extra={
                "governance_support_mode": self.support_mode.value,
                "governance_referent_resolution": {
                    role: resolution.value
                    for role, resolution in sorted(self.referent_resolution.items())
                },
            },
        )


__all__ = [
    "GovernanceSupport",
    "GovernanceValidationError",
    "IdentityPlane",
    "ReferentResolution",
    "SupportMode",
    "identity_plane",
    "namespaced_referent_id",
    "validate_relation_identity_planes",
]
