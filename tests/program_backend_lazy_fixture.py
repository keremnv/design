"""Honest query-backed core reader: integer IDs and structured evidence.

Only keyed lookups are available. Iterating the entity/edge index is an error,
so passing core tests cannot rely on a hidden full-repository enumeration.
The exact reference/factory here is test composition, not a production type.
"""

import hashlib

from ontology_author.program_backend import Capability, CapabilityStatus, ProgramBackend


class LookupOnly(dict):
    def __iter__(self):
        raise AssertionError("whole-index enumeration is unavailable")

    keys = values = items = __iter__


class LazyBackend(ProgramBackend):
    def __init__(self, occurrence):
        if occurrence not in (("retained-index", 11), ("retained-index", 12)):
            raise ValueError("exact occurrence is unavailable")
        self.occurrence = occurrence
        self._revision = occurrence[1]
        self._entity = 30 if self._revision == 11 else 31
        self._kinds = LookupOnly({10: "module", 20: "source_unit", self._entity: "callable", 40: "call_site", 99: "signature"})
        self._context = LookupOnly({
            10: (),
            20: ({"parent": 10, "child": 20},),
            self._entity: ({"parent": 10, "child": 20}, {"parent": 20, "child": self._entity}),
            40: ({"parent": 10, "child": 20}, {"parent": 20, "child": 40}),
            99: (),
        })
        self._material = f"retained source at integer revision {self._revision}"
        self._digest = hashlib.sha256(self._material.encode()).digest()

    def snapshot(self):
        return f"indexed-state-{self._revision}"

    def is_member(self, entity):
        return entity in self._kinds

    def kind(self, entity):
        return self._kinds.get(entity)

    def containment(self, entity):
        return self._context.get(entity, ())

    def capability(self, family):
        if family == "containment":
            return Capability(CapabilityStatus.COMPLETE, "declared indexed source", "retained ancestor index")
        return Capability(CapabilityStatus.NOT_PRODUCED, "", "family is not produced")

    def observations(self, entity):
        if not self.is_member(entity):
            return ()
        return ({
            "source": {"provider": "index", "id": (7, b"\x00opaque")},
            "revision": self._revision,
            "extent": {"start": 0, "end": len(self._material)},
            "content": self._digest,
        },)

    def reconstruct(self, observation):
        # All indexed entities in this tiny declared scope reference the same
        # retained input. Qualification and closure do not enumerate the index.
        if observation != self.observations(self._entity)[0] or self.verify():
            return "", False
        return self._material, True

    def verify(self):
        if hashlib.sha256(self._material.encode()).digest() != self._digest:
            return ("retained source changed",)
        return ()


class LazyCallsBackend(LazyBackend):
    def capability(self, family):
        if family in {"invocation", "resolution"}:
            return Capability(CapabilityStatus.COMPLETE, "indexed static sites", "resolution outcome per site")
        return super().capability(family)

    def invocations(self, call_site):
        if call_site == 40:
            return ({"call_site": 40, "target": self._entity},)
        return ()

    def resolutions(self, subject):
        if subject == 40:
            return ({"subject": 40, "status": "RESOLVED", "capability": "indexed static sites"},)
        return ()
