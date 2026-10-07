"""Scoped mechanical reads over an exact opened program occurrence.

A ProgramBackend exposes only mechanically observed program information
under declared qualification/capability/evidence semantics. It establishes
no business meaning, requirement satisfaction, authority, or currentness.

Conventions forced by the migrated authority consumer and the Phase 5A
conformance contract:

- The backend-specific factory qualifies the exact retained occurrence.
  Entity tokens are opaque local hashable values; a (handle, token) pair
  is the qualified identity. Tokens need not encode any state or location.
- Read methods are total: unknown entities yield ``None``/empty results,
  never silently cross occurrences. Consumers check membership explicitly.
- Fact rows are plain dicts whose keys name the relation roles
  (``parent``/``child``, ``call_site``/``target``,
  ``subject``/``status``/``capability``). No row classes are introduced.
- Observations are opaque backend-owned objects round-tripped unchanged
  through :meth:`reconstruct`; consumers do not interpret their structure.
- Capability qualification is requested per family. Optional call reads
  may be empty with NOT_PRODUCED, which never licenses absence inference.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Hashable
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
    """COMPLETE is scoped; INCOMPLETE includes partial/uncertain coverage."""

    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    NOT_PRODUCED = "NOT_PRODUCED"


@dataclass(frozen=True)
class Capability:
    """Declared honesty metadata for one capability family.

    ``NOT_PRODUCED`` licenses no absence inference; only a supported +
    complete declaration with scope and basis qualifies negative
    conclusions. Native receipt shapes are never required here.
    """

    status: CapabilityStatus
    scope: str
    basis: str
    gaps: tuple[str, ...] = ()


class ProgramBackend(ABC):
    """Selected-entity reads, without entity or relation-universe enumeration."""

    def __enter__(self) -> ProgramBackend:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        """Release resources held by this handle."""

    @abstractmethod
    def snapshot(self) -> str:
        """Stable opaque observed-state token, not exact occurrence identity."""

    @abstractmethod
    def is_member(self, entity: Hashable) -> bool:
        """Whether the token is a member of this observed state."""

    @abstractmethod
    def kind(self, entity: Hashable) -> str | None:
        """Mechanical kind of a member, else ``None``."""

    @abstractmethod
    def containment(self, entity: Hashable) -> tuple[dict[str, Hashable], ...]:
        """Ancestor edges for this entity, with parent/child roles preserved.

        Return enough qualified edges to recover the demonstrated ancestor
        chain, not unrelated repository containment. A nonmember yields ().
        """

    def invocations(self, call_site: Hashable) -> tuple[dict[str, Hashable], ...]:
        """Optional outgoing edges for a site, with call_site/target roles.

        Production is optional; NOT_PRODUCED plus () is honest. A declared
        produced capability without an implementation must fail explicitly.
        """
        if not self.is_member(call_site):
            return ()
        if self.capability("invocation").status != CapabilityStatus.NOT_PRODUCED:
            raise OptionalUnsupported("produced invocation reads are not implemented")
        return ()

    def resolutions(self, subject: Hashable) -> tuple[dict[str, Hashable], ...]:
        """Optional subject/status/capability outcomes for one subject."""
        if not self.is_member(subject):
            return ()
        if self.capability("resolution").status != CapabilityStatus.NOT_PRODUCED:
            raise OptionalUnsupported("produced resolution reads are not implemented")
        return ()

    @abstractmethod
    def capability(self, family: str) -> Capability:
        """Qualification for the requested family; no inventory is required.

        Missing/unsupported families cannot confer completeness. Return an
        honest NOT_PRODUCED declaration or explicitly fail qualification.
        """

    @abstractmethod
    def observations(self, entity: Hashable) -> tuple[object, ...]:
        """Opaque revision-qualified evidence handles; () for a nonmember."""

    @abstractmethod
    def reconstruct(self, observation: object) -> tuple[str, bool]:
        """Reconstruct retained material as ``(material, verified)``.

        The verification flag distinguishes failure from verified empty
        material. Never represent mutable/unqualified material as verified.
        """

    @abstractmethod
    def verify(self) -> tuple[str, ...]:
        """Convenient composition of declared retained-guarantee checks.

        R7 forces verification behavior; the migrated constructor does not
        force this particular operation. Return violations, empty on success.
        """

    def discover(
        self,
        *,
        label: str | None = None,
        kind: str | None = None,
        descriptor_contains: str | None = None,
    ) -> tuple[Hashable, ...]:
        """Optional native-compatible discovery extension, outside core reads.

        Labels and descriptors are not identity. Backends without this
        service raise :class:`OptionalUnsupported` instead of guessing.
        descriptor_contains is native compatibility vocabulary, not a core
        backend requirement. Even unfiltered enumeration is optional.
        """
        raise OptionalUnsupported("label/identity discovery is not supported")
