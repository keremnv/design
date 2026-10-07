"""Minimal production read boundary over an exact retained program occurrence.

A ProgramBackend exposes only mechanically observed program information
under declared qualification/capability/evidence semantics. It establishes
no business meaning, requirement satisfaction, authority, or currentness.

Conventions forced by the migrated authority consumer and the Phase 5A
conformance contract:

- The handle is scoped to one exact opened occurrence. Entity tokens are
  opaque local strings; a (handle, token) pair is the qualified identity.
  Tokens never encode snapshot, occurrence, language, path, or position.
- Read methods are total: unknown entities yield ``None``/empty results,
  never silently cross occurrences. Consumers check membership explicitly.
- Fact rows are plain dicts whose keys name the relation roles
  (``parent``/``child``, ``call_site``/``target``,
  ``subject``/``status``/``capability``). No row classes are introduced.
- Observations are opaque backend-defined mappings round-tripped through
  :meth:`reconstruct`. Reconstruction is fail-closed: unverified material
  is never returned as usable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum


class BackendError(Exception):
    """Base failure for program-backend reads."""


class NotAProgramOccurrence(BackendError):
    """The opened occurrence carries no program plane at all."""


class OccurrenceQualificationError(BackendError):
    """The program plane is present but unqualified or malformed."""


class OptionalUnsupported(BackendError):
    """An optional backend service is not provided by this backend."""


class CapabilityStatus(StrEnum):
    """Production/reporting state of one declared capability family."""

    COMPLETE = "COMPLETE"
    STATIC_COMPLETE = "STATIC_COMPLETE"
    PARTIAL = "PARTIAL"
    INCOMPLETE = "INCOMPLETE"
    UNKNOWN = "UNKNOWN"
    NOT_PRODUCED = "NOT_PRODUCED"


@dataclass(frozen=True)
class Capability:
    """Declared honesty metadata for one capability family.

    ``NOT_PRODUCED`` with empty gaps/references licenses no absence
    inference; only a supported + complete declaration scopes negative
    conclusions. Native receipt shapes are never required here.
    """

    status: CapabilityStatus
    scope: str
    basis: str
    gaps: tuple[str, ...] = ()


class ProgramBackend(ABC):
    """Smallest production read surface forced by the binding consumer."""

    def __enter__(self) -> ProgramBackend:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        """Release resources held by this handle."""

    @abstractmethod
    def snapshot(self) -> str:
        """Opaque token of the governed observed state."""

    @abstractmethod
    def snapshot_id(self) -> str:
        """Opaque recorded identity of the observed state."""

    @abstractmethod
    def members(self) -> tuple[str, ...]:
        """Opaque entity tokens in this observed state."""

    def is_member(self, entity: str) -> bool:
        """Whether the token is a member of this observed state."""
        return entity in self.members()

    @abstractmethod
    def kind(self, entity: str) -> str | None:
        """Mechanical kind of a member, else ``None``."""

    @abstractmethod
    def containment(self) -> tuple[dict[str, str], ...]:
        """Containment edges as ``{"parent": ..., "child": ...}`` rows."""

    @abstractmethod
    def invocations(self) -> tuple[dict[str, str], ...]:
        """Invocation edges as ``{"call_site": ..., "target": ...}`` rows."""

    @abstractmethod
    def resolutions(self) -> tuple[dict[str, str], ...]:
        """Resolution outcomes as ``{"subject", "status", "capability"}`` rows."""

    @abstractmethod
    def capabilities(self) -> Mapping[str, Capability]:
        """Declared honesty metadata by capability family.

        The ``containment``/``invocation``/``resolution`` families are
        always declared; further keys are backend-declared vocabulary.
        """

    @abstractmethod
    def observations(self, entity: str) -> tuple[dict[str, str], ...]:
        """Opaque qualified source observations for an entity token."""

    @abstractmethod
    def reconstruct(self, observation: Mapping[str, str]) -> tuple[str, bool]:
        """Reconstruct retained material as ``(material, verified)``.

        Unverified observations yield ``("", False)``; no partial or
        unqualified material is returned as usable.
        """

    @abstractmethod
    def verify(self) -> tuple[str, ...]:
        """Violations of the declared retained-evidence guarantees."""

    def discover(
        self,
        *,
        label: str | None = None,
        kind: str | None = None,
        descriptor_contains: str | None = None,
    ) -> tuple[str, ...]:
        """Optional candidate lookup over display/identity metadata.

        Labels and descriptors are not identity. Backends without this
        service raise :class:`OptionalUnsupported` instead of guessing.
        """
        raise OptionalUnsupported("label/identity discovery is not supported")
