"""`WorldExplorerAdapter` — the read surface the canvas talks to.

The front end needs the answers listed in §14 of the World IR front-end spec:
relation schemas, tuples, SQL, tuple inspection, construction origin, grounding,
staleness, completeness, derivation dependencies and unresolved obligations.
`SemanticWorld` already answers nearly all of it — `describe()`
alone carries roles, types, columns, mode, counts, staleness and completeness —
so this module formats; it does not store.

That distinction is the one rule worth stating outright, because it is the one
that would quietly be broken first: **the adapter holds no state.** Every method
reads through to the open world. Nothing is cached, denormalised, or kept
between calls. An adapter that starts remembering is a second copy of the world
with its own staleness, which is exactly what rule 10 of the spec forbids and
what the tests here pin.

Two things it does have to reconcile, because the store and the product disagree
about words:

**Origin.** `_world_assertions.origin` is `ASSERTED` or `DERIVED` — how the tuple
got into the table. The product means something else by origin: MECHANICAL,
SEMANTIC or DERIVED — who decided it, which is what the canvas paints. That
lives on the grounding/support paths, via `origins_for_assertion`. A world
compiled without that metadata has no answer at all, and this reports
`UNKNOWN` rather than raising, because a missing origin is a fact about the
world worth seeing on screen, not a broken request. `origin` remains a scalar
compatibility summary; `origins` carries every support-path origin.

**Roles versus columns.** A relation's role is `new_part`; its column is
`new_part_id` for a referent role and the bare name for a scalar. `describe()`
returns both, so nothing here guesses — and the referent/scalar split is what
decides whether a value becomes a node on the canvas or a field on a card.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from ontology_author.world.core.kernel import SemanticWorld
from ontology_author.world.core.origins import OriginMetadataError

#: Reported when a world carries no construction-origin grounding for a tuple.
UNKNOWN_ORIGIN = "UNKNOWN"
MULTIPLE_ORIGINS = "MULTIPLE"

#: Ceiling on rows any single call will return. The canvas is bounded by design
#: and the table pages; nothing downstream wants the whole extension in one
#: response, and a missing `limit` should not be able to ask for one.
MAX_ROWS = 500

#: How many scalar properties of one referent are worth flattening into card
#: fields. Past this the relation is reported as a relation instead, so the
#: reader sends it to the windowed table rather than listing it — the same
#: judgement §5.4 already makes about putting a relation on the field.
MAX_FIELDS = 200


PURPOSE_FAILURE_RELATION = "purpose_requirement_failure"

def _purpose_path(db_path: Path) -> Path:
    """`world.sqlite` -> `world.purpose.json`, the v1 boundary's sidecar."""
    return db_path.with_suffix(".purpose.json")


def _admission_path(db_path: Path) -> Path:
    """`world.sqlite` -> `world.admission.json`, where scope is recorded."""
    return db_path.with_suffix(".admission.json")


def _governance_path(db_path: Path) -> Path:
    """`world.sqlite` -> `world.governance.json`, the application law artifact."""
    return db_path.with_suffix(".governance.json")


def _structure_path(db_path: Path) -> Path:
    """`world.sqlite` -> `world.structure.json`, the bounded model artifact."""
    return db_path.with_suffix(".structure.json")


def _obligations_path(db_path: Path) -> Path:
    """`world.sqlite` -> generated-law obligation provenance artifact."""
    return db_path.with_suffix(".obligations.json")


def _evidence_authority_path(db_path: Path) -> Path:
    """`world.sqlite` -> the selected evidence-authority configuration."""
    return db_path.with_suffix(".evidence-authority.json")


def _adjudication_authority_path(db_path: Path) -> Path:
    """`world.sqlite` -> the selected adjudication-authority configuration."""
    return db_path.with_suffix(".adjudication-authority.json")


def _read_json_sidecar(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def world_id_of(db_path: Path | str) -> str:
    """The WorldStore id a world file already carries.

    Asked of the file rather than of the caller. `WorldStore` refuses to open a
    database whose `world_id` differs from the one passed in, and that id is set
    by whichever compiler wrote the file — so requiring the explorer to know it
    in advance turns opening a world into a guess, and the failure reads as a
    corrupt file rather than as a mismatched string.
    """
    connection = sqlite3.connect(f"file:{Path(db_path)}?mode=ro", uri=True)
    try:
        row = connection.execute(
            "SELECT world_id FROM _world_meta WHERE singleton = 1"
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        raise ValueError(f"{db_path} is not a WorldStore world")
    return str(row[0])


@dataclass(frozen=True)
class Role:
    name: str
    type: str
    column: str
    reference_kind: str | None = None

    @property
    def referent(self) -> bool:
        return self.type == "REFERENT"


class WorldExplorerAdapter:
    """One open World, formatted for the explorer."""

    def __init__(self, path: Path | str, *, world_id: str | None = None) -> None:
        self.path = Path(path)
        self._world = SemanticWorld(
            self.path, world_id=world_id or world_id_of(self.path), read_only=True
        )
        self._store = self._world._store
        self._purpose_document: dict[str, Any] | None = None
        purpose = _purpose_path(self.path)
        if purpose.exists():
            document = json.loads(purpose.read_text(encoding="utf-8"))
            # Project.run keeps passing an empty Purpose object to the legacy
            # constructor and therefore may persist an empty compatibility
            # sidecar. It is not a loaded Purpose demand unless it has user
            # text or declared requirements.
            if document.get("text", "").strip() or document.get("requirements"):
                self._purpose_document = document
        self._governance_document = _read_json_sidecar(_governance_path(self.path))
        self._structure_document = _read_json_sidecar(_structure_path(self.path))
        self._obligations_document = _read_json_sidecar(_obligations_path(self.path))
        self._evidence_authority_document = _read_json_sidecar(
            _evidence_authority_path(self.path)
        )
        self._adjudication_authority_document = _read_json_sidecar(
            _adjudication_authority_path(self.path)
        )

    def close(self) -> None:
        """Release the read-only World without writing to it."""
        self._world.close()

    def __enter__(self) -> "WorldExplorerAdapter":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    # -- reading through ----------------------------------------------------

    def _described(self) -> list[dict[str, Any]]:
        return self._store.describe()["relations"]

    def _scopes(self) -> dict[str, str]:
        """relation -> WORLD | PURPOSE, from the admission sidecar.

        Read on every call, like everything else here. Scope is not a WorldStore
        column — it is admitted at publication and recorded beside the file —
        so a compiled world that carries no admission document has no scopes,
        and every relation reports `null` rather than a guessed WORLD. Guessing
        would be the worse failure: WORLD is the stronger claim, and a purpose
        artefact promoted to a world fact by a missing file is exactly the
        laundering the two-scope distinction exists to prevent.
        """
        path = _admission_path(self.path)
        if not path.exists():
            return {}
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            return {}
        relations = document.get("relations")
        return (
            {str(k): str(v) for k, v in relations.items()}
            if isinstance(relations, dict)
            else {}
        )

    def _relation(self, name: str) -> dict[str, Any]:
        for record in self._described():
            if record["name"] == name:
                return record
        raise KeyError(f"no relation {name!r} in this world")

    @staticmethod
    def _roles(record: Mapping[str, Any]) -> list[Role]:
        return [
            Role(r["name"], r["type"], r["column"], r.get("reference_kind"))
            for r in record["roles"]
        ]

    def _origins(self, assertion_id: str) -> list[str]:
        try:
            return self._world.origins_for_assertion(assertion_id)
        except OriginMetadataError:
            return [UNKNOWN_ORIGIN]

    def _origin(self, assertion_id: str) -> str:
        origins = self._origins(assertion_id)
        if len(origins) == 1:
            return origins[0]
        return MULTIPLE_ORIGINS

    def _grounding(self, subject_type: str, subject_id: str) -> list[dict[str, Any]]:
        """Grounding with its detail opened up.

        WorldStore stores `detail` as a JSON string, which is right for a store
        and wrong for the thing that has to draw `engineering_notes.md lines
        6-14` in a panel. Parsed here, once, rather than in every consumer —
        and the source handle and location are lifted to the top level because
        they are the whole of what §8.5 shows.

        Left as the raw string if it will not parse. A grounding this layer
        cannot read is still a grounding, and dropping it would be the one kind
        of loss this product cannot afford.
        """
        out: list[dict[str, Any]] = []
        for row in self._store.groundings(subject_type, subject_id):
            item: dict[str, Any] = {"kind": row["kind"], "reference": row["reference"]}
            try:
                detail = json.loads(row["detail"]) if row["detail"] else {}
            except (TypeError, ValueError):
                item["detail_text"] = row["detail"]
                out.append(item)
                continue
            item["detail"] = detail
            if isinstance(detail, Mapping):
                for key in ("native_handle", "native_location", "provider",
                            "source_revision", "construction_method",
                            "construction_origin"):
                    if key in detail:
                        item[key] = detail[key]
            out.append(item)
        return out

    def _row_out(self, roles: Sequence[Role], row: Mapping[str, Any]) -> dict[str, Any]:
        assertion_id = row["_assertion_id"]
        return {
            "assertion_id": assertion_id,
            "origin": self._origin(assertion_id),
            "origins": self._origins(assertion_id),
            "values": {role.name: row[role.column] for role in roles},
        }

    @staticmethod
    def _completeness_out(receipt: Mapping[str, Any] | None) -> dict[str, Any] | None:
        """The completeness claim, named for the canvas rather than the store.

        WorldStore's receipt carries versions, fingerprints and environment —
        facts the derivation drawer already has from the run record. What the
        overlay needs is the declared status, the universe it was claimed over,
        and whether that claim is still current. A missing receipt is `None`,
        not UNKNOWN: UNKNOWN is a status someone recorded.
        """
        if not receipt:
            return None
        gaps = receipt.get("known_gaps") or []
        return {
            "status": receipt["status"],
            "universe": receipt.get("universe_relation"),
            "current": bool(receipt.get("current")),
            "known_gaps": list(gaps) if isinstance(gaps, list) else [],
        }

    def _origins_seen(self) -> dict[str, list[str]]:
        """Every construction origin present in each relation.

        This was a sample — one assertion per relation, on the ground that a
        world's relations are homogeneous. Adjudication ends that: a person's
        verdict lands on single tuples inside relations the machine otherwise
        built, so the origin worth seeing is the rare one, and any sample large
        enough to miss it is a sample that reports a human decision as the
        machine's. It is a whole scan for that reason, not for tidiness.

        One pass for the whole schema rather than a query per relation, and
        nothing kept between calls — the adapter reads through.
        """
        seen: dict[str, list[str]] = {}
        for row in self._store.query(
            "SELECT relation_name, assertion_id FROM _world_assertions"
        ):
            origins = seen.setdefault(row["relation_name"], [])
            for origin in self._origins(row["assertion_id"]):
                if origin not in origins:
                    origins.append(origin)
        return {name: sorted(origins) for name, origins in seen.items()}

    # -- §7.1 world and schema ---------------------------------------------

    def identity(self) -> dict[str, Any]:
        """Which world this is, and at which revision.

        Split out of `overview()` because a judgment has to be bound to a
        world and a revision, and `overview()` scans every assertion to count
        construction origins. Nothing that only needs the name should pay for
        that.
        """
        payload: dict[str, Any] = {
            "world_id": self._world.world_id,
            "revision": self._store.revision,
            "contract": self._world.contract_identity(),
            "governance": (
                self._governance_document or {}
            ).get("identity"),
        }
        if self._evidence_authority_document is not None:
            payload["evidence_authority"] = (
                self._evidence_authority_document.get("identity")
            )
        if self._adjudication_authority_document is not None:
            payload["adjudication_authority"] = (
                self._adjudication_authority_document.get("identity")
            )
        return payload

    def governance(self) -> dict[str, Any] | None:
        """The application Governance Law artifact, when one was published."""
        return self._governance_document

    def evidence_authority(self) -> dict[str, Any] | None:
        """The externally selected evidence-authority artifact, when published."""
        return self._evidence_authority_document

    def adjudication_authority(self) -> dict[str, Any] | None:
        """The selected adjudication-authority artifact, when published."""
        return self._adjudication_authority_document

    def adjudication(self, adjudication_id: str) -> dict[str, Any] | None:
        """One durable adjudicative input, addressed by its identity."""
        return self._world.adjudication(adjudication_id)

    def adjudications(self) -> list[dict[str, Any]]:
        """All durable adjudicative inputs in deterministic order."""
        return self._world.adjudications()

    def structure(self) -> dict[str, Any] | None:
        """The bounded descriptive frontend structure, when one was published."""
        return self._structure_document

    def obligations(self) -> dict[str, Any]:
        """The read contract for durable, law-generated Obligations.

        This is deliberately separate from :meth:`demand`.  The latter reads
        only the legacy Purpose frontier; this payload reads the durable
        Obligation records and their already-recorded resolution/candidate
        projections.  Law provenance is attached to each item by
        ``_governed_obligation_rows`` rather than returned as a second,
        unrelated obligation document.
        """
        return {
            "contract": self._world.contract_identity(),
            "governance": (
                self._governance_document or {}
            ).get("identity"),
            "obligations": self._governed_obligation_rows(),
        }

    def resolution(self, obligation_id: str) -> dict[str, Any] | None:
        """The current persisted evaluation for one Obligation."""
        return self._world.resolution(obligation_id)

    def obligation(self, obligation_id: str) -> dict[str, Any] | None:
        """One durable Obligation as a human-facing inspection aggregate.

        ``/world/demand`` remains the compact frontier payload used by the
        legacy Purpose surface.  This selected-obligation read joins the
        already-recorded Commitment, Warrant, assessment, and adjudication
        state so the reader does not have to reproduce kernel joins or make a
        request per candidate.
        """

        target = str(obligation_id)
        for item in self._governed_obligation_rows():
            if item.get("obligation_id") != target:
                continue
            resolution = item.get("resolution")
            item["candidates"] = self._contract_candidates(
                target,
                detailed=True,
                resolution=resolution if isinstance(resolution, Mapping) else None,
            )
            assessments = {
                str(assessment.get("adjudication_id")): assessment
                for assessment in (
                    resolution.get("adjudication_assessments", [])
                    if isinstance(resolution, Mapping)
                    else []
                )
                if isinstance(assessment, Mapping)
                and assessment.get("adjudication_id")
            }
            item["adjudications"] = [
                {
                    "record": record,
                    "assessment": assessments.get(str(record["adjudication_id"])),
                }
                for record in self._world.adjudications_for_obligation(target)
            ]
            identities = self.identity()
            item["context"] = {
                "contract": identities.get("contract"),
                "governance": identities.get("governance"),
                "evidence_authority": identities.get("evidence_authority"),
                "adjudication_authority": identities.get("adjudication_authority"),
            }
            return item
        return None

    def overview(self) -> dict[str, Any]:
        described = self._described()
        counts = self._store.query(
            "SELECT (SELECT COUNT(*) FROM _world_referents) AS referents, "
            "(SELECT COUNT(*) FROM _world_assertions) AS assertions"
        )[0]
        origins: dict[str, int] = {}
        for row in self._store.query("SELECT assertion_id FROM _world_assertions"):
            for origin in self._origins(row["assertion_id"]):
                origins[origin] = origins.get(origin, 0) + 1
        incomplete = [
            record["name"]
            for record in described
            if record["completeness"]
            and record["completeness"]["status"] != "COMPLETE"
        ]
        payload: dict[str, Any] = {
            "world_id": self._world.world_id,
            "revision": self._store.revision,
            "contract": self._world.contract_identity(),
            "governance": (
                self._governance_document or {}
            ).get("identity"),
            "relations": len(described),
            "referents": counts["referents"],
            "assertions": counts["assertions"],
            "origins": origins,
            "stale": self._world.stale_relations(),
            "incomplete": incomplete,
            "demand": self._demand_overview(),
            "governed_obligations": self._governed_obligations_overview(),
        }
        if self._evidence_authority_document is not None:
            payload["evidence_authority"] = (
                self._evidence_authority_document.get("identity")
            )
        if self._adjudication_authority_document is not None:
            payload["adjudication_authority"] = (
                self._adjudication_authority_document.get("identity")
            )
        return payload

    def _demand_overview(self) -> dict[str, Any] | None:
        frontier = self._purpose_frontier()
        if frontier is None:
            return None
        return {
            "purpose": frontier["purpose"],
            "obligations": len(frontier["obligations"]),
            "demanded": frontier["demanded"],
        }

    def _governed_obligations_overview(self) -> dict[str, int] | None:
        """Compact navigation counts for durable governed Obligations."""
        obligations = self._world.obligations()
        if not obligations:
            return None
        resolved = sum(
            1 for item in obligations if item.get("resolution_status") == "RESOLVED"
        )
        return {
            "count": len(obligations),
            "resolved": resolved,
            "unresolved": len(obligations) - resolved,
        }

    def schema(self) -> list[dict[str, Any]]:
        """Every relation, with the facts the schema canvas draws from.

        `arity` and the referent/scalar split are here rather than in the front
        end because they decide the projection — arity 2 collapses onto a
        filament, arity 3+ stands as a plate, and a scalar role never becomes a
        node at all. That is a rule about the world, not about the renderer.

        `scope` says whether a relation is a claim about the world or an
        artefact of one purpose. The constitution keeps that distinction and
        the read plane was dropping it: the admission sidecar records it, the
        delta reports when it moves, and a reader looking at the catalogue had
        no way to tell a world fact from a purpose's own bookkeeping.
        """
        out: list[dict[str, Any]] = []
        origins_seen = self._origins_seen()
        scopes = self._scopes()
        # Filled in below, and only if the namespace convention came up empty.
        derived: dict[tuple[str, str], str] | None = None
        for record in self._described():
            roles = self._roles(record)
            item: dict[str, Any] = {
                "name": record["name"],
                "description": record["description"],
                "mode": record["mode"],
                "arity": len(roles),
                "roles": [
                    {
                        "name": role.name,
                        "type": role.type,
                        "column": role.column,
                        "referent": role.referent,
                        "kinds": [],
                        **(
                            {"reference_kind": role.reference_kind}
                            if role.reference_kind
                            else {}
                        ),
                    }
                    for role in roles
                ],
                "referent_arity": sum(1 for role in roles if role.referent),
                "scope": scopes.get(record["name"]),
                "count": record["row_count"],
                "stale": record["stale"],
                "origins": origins_seen.get(record["name"], []),
                "completeness": self._completeness_out(record["completeness"]),
            }
            if record.get("derivation"):
                item["derivation"] = {
                    **record["derivation"],
                    "inputs": self.derivation_inputs(record["name"]),
                }
            out.append(item)

        # Kinds last, in two passes, because the fallback is whole-world and
        # the namespace read is per-role. A role keeps whatever the ids say;
        # only a role the convention left empty asks `derived_kinds`, and only
        # if some role did is that scan paid for at all.
        for item, record in zip(out, self._described()):
            for role, described in zip(item["roles"], self._roles(record)):
                if not described.referent:
                    continue
                role["kinds"] = self.role_kinds(item["name"], described.column)
                if not role["kinds"]:
                    if derived is None:
                        derived = self.derived_kinds()
                    kind = derived.get((item["name"], described.name))
                    role["kinds"] = [kind] if kind else []
        return out

    #: How many distinct namespaces a role is reported as accepting before the
    #: answer stops being a type and starts being a list.
    MAX_ROLE_KINDS = 6

    def role_kinds(self, relation: str, column: str) -> list[str]:
        """The referent namespaces actually seen in one role, e.g. `["part"]`.

        World IR types a role as REFERENT and stops there — a role knows it
        takes a referent, not that it takes a *part*. But §7.1's schema view is
        drawn in exactly those terms (`SupplierListing ─ listing_of ─ Part`), so
        the kinds have to come from somewhere.

        They come from the data. Referent ids in this world are namespaced —
        `part:X160`, `context:outdoor_enclosure` — so the distinct prefixes a
        role has actually been filled with are an observation, not a schema
        claim, and this returns them as such. A role that has never been filled
        reports nothing, which is honest: an empty relation has no kinds to
        show, and inventing one would put a type on the canvas the world has
        never asserted.
        """
        rows = self._store.query(
            f'SELECT DISTINCT substr("{column}", 1, instr("{column}", \':\') - 1) '
            f'AS kind FROM "{relation}" '
            f'WHERE "{column}" IS NOT NULL AND instr("{column}", \':\') > 0 '
            f"ORDER BY kind LIMIT ?",
            (self.MAX_ROLE_KINDS,),
        )
        return [row["kind"] for row in rows if row["kind"]]

    def derived_kinds(self) -> dict[tuple[str, str], str]:
        """`(relation, role)` -> kind, for a world whose ids carry no namespace.

        `role_kinds` reads the kind off the id — `part:X160` -> `part`. That is
        a naming convention the constructor either followed or did not, and a
        world rebuilt through the v1 boundary generally did not: every
        Philips referent is `BIPAP_A30`, `FDA_RECALL_Z-2035-2025`, and the
        schema canvas drew nothing at all because it had no kinds to place.

        Kinds are recoverable without the convention, from the world itself and
        with no guessing. Two roles are the same kind when they have been
        filled with the same referents — `later_action` and `earlier_action`
        hold the actions `action` holds, so all three are one kind — and that
        is set arithmetic over asserted tuples, not an inference about meaning.
        The component is named for the role that carries the most of them.

        What this deliberately does not do is invent a distinction. Roles whose
        populations never meet stay separate because the world never says they
        are the same, which is the same restraint `delta.py` shows in refusing
        to notice a rename.

        Whole-world, so `schema()` calls it once and only when some role came
        back without a namespace. A world that has the convention pays nothing.
        """
        columns = [
            (str(record["name"]), role)
            for record in self._described()
            for role in self._roles(record)
            if role.referent
        ]
        population: dict[tuple[str, str], set[str]] = {}
        for relation, role in columns:
            key = (relation, role.name)
            population[key] = {
                str(row["value"])
                for row in self._store.query(
                    f'SELECT DISTINCT "{role.column}" AS value FROM "{relation}" '
                    f'WHERE "{role.column}" IS NOT NULL'
                )
                if row["value"]
            }

        # Union-find over roles, joined wherever two of them have held the same
        # referent. Sorted so the result does not depend on dict order.
        keys = sorted(population)
        parent = {key: key for key in keys}

        def find(key: tuple[str, str]) -> tuple[str, str]:
            while parent[key] != key:
                parent[key] = parent[parent[key]]
                key = parent[key]
            return key

        for index, left in enumerate(keys):
            for right in keys[index + 1 :]:
                if population[left] & population[right]:
                    a, b = find(left), find(right)
                    if a != b:
                        parent[a] = b

        components: dict[tuple[str, str], list[tuple[str, str]]] = {}
        for key in keys:
            components.setdefault(find(key), []).append(key)

        out: dict[tuple[str, str], str] = {}
        for members in components.values():
            # Most-filled role names the kind; alphabetical breaks a tie, so
            # two roles of equal standing do not swap names between reads.
            name = min(
                {key[1] for key in members},
                key=lambda role_name: (
                    -max(
                        len(population[key])
                        for key in members
                        if key[1] == role_name
                    ),
                    role_name,
                ),
            )
            for key in members:
                if population[key]:
                    out[key] = name
        return out

    def derivation_inputs(self, relation: str) -> list[str]:
        return [
            row["input_relation"]
            for row in self._store.query(
                "SELECT input_relation FROM _world_derivation_inputs "
                "WHERE relation_name = ? ORDER BY input_relation",
                (relation,),
            )
        ]

    # -- §8.1 search --------------------------------------------------------

    def search(self, query: str, *, limit: int = 30) -> list[dict[str, Any]]:
        """Referents and relation names matching a substring.

        Deliberately dumb. At S100 the whole referent table is 3,118 rows and
        reads in 3ms, so the front end is expected to hold it and filter as you
        type; this exists for callers that are not the canvas.
        """
        needle = f"%{query}%"
        out: list[dict[str, Any]] = [
            {"kind": "referent", "id": row["id"], "label": row["label"]}
            for row in self._store.query(
                "SELECT id, label FROM _world_referents "
                "WHERE id LIKE ? OR label LIKE ? ORDER BY id LIMIT ?",
                (needle, needle, min(limit, MAX_ROWS)),
            )
        ]
        lowered = query.lower()
        out.extend(
            {"kind": "relation", "id": record["name"], "label": record["description"]}
            for record in self._described()
            if lowered in record["name"].lower()
        )
        return out

    def referents(self) -> list[dict[str, Any]]:
        """Every referent, for a front end that wants to search locally."""
        return [
            {"id": row["id"], "label": row["label"]}
            for row in self._store.query("SELECT id, label FROM _world_referents ORDER BY id")
        ]

    def labels(self, referent_ids: Iterable[str]) -> dict[str, str | None]:
        """Return labels for a bounded set of referent ids."""
        ids = list(dict.fromkeys(str(item) for item in referent_ids if str(item)))
        if not ids:
            return {}
        marks = ",".join("?" for _ in ids)
        return {
            row["id"]: row["label"]
            for row in self._store.query(
                f"SELECT id, label FROM _world_referents WHERE id IN ({marks})",
                ids,
            )
        }

    # -- §7.2 referent neighborhood ----------------------------------------

    def referent(self, referent_id: str) -> dict[str, Any]:
        """One referent, its scalar fields, and its relations *with counts*.

        Counts before matter: the canvas asks what expanding would cost before
        it expands, which is how a relation with four hundred tuples goes to the
        table instead of onto the field.

        The counts are counted, not measured off fetched rows. That distinction
        is the whole cost of this call — a referent can be in a relation tens of
        thousands of times, and reading those rows to find out how many there
        are is how a cheap question becomes a multi-megabyte answer.
        """
        rows = self._store.query(
            "SELECT id, label FROM _world_referents WHERE id = ?", (referent_id,)
        )
        if not rows:
            raise KeyError(f"no referent {referent_id!r} in this world")

        fields: list[dict[str, Any]] = []
        relations: list[dict[str, Any]] = []
        for record in self._described():
            roles = self._roles(record)
            referent_roles = [role for role in roles if role.referent]
            if not referent_roles:
                continue
            where = " OR ".join(f'"{role.column}" = ?' for role in referent_roles)
            arguments = [referent_id] * len(referent_roles)
            # Count first, fetch second. This used to `SELECT *` unbounded and
            # decide afterwards, which is fine until a referent is in a large
            # relation: one Philips serial set is in `serial_scope_member`
            # 22,413 times, and the answer was a 3.27 MB document of 22,413
            # card fields — each one having cost its own origin lookup — that
            # the reader then tried to render as 22,413 rows.
            count = self._store.query(
                f'SELECT COUNT(*) AS n FROM "{record["name"]}" WHERE {where}',
                arguments,
            )[0]["n"]
            if not count:
                continue
            scalar_roles = [role for role in roles if not role.referent]
            # A scalar-valued relation over exactly this referent is a property
            # of it as far as a reader is concerned — `rated_voltage 24` — so it
            # is offered as a card field. It stays an assertion: the field
            # carries its assertion id, so the inspector can still be opened on
            # it and its grounding read. §5.4 is a presentation rule, not a
            # claim that the value is stored on the referent.
            # §5.4 already says a relation too big for the field goes to the
            # table instead. A scalar property is the same judgement made about
            # the same relation, so it takes the same threshold rather than a
            # second one: past it, this is reported as a relation with its
            # count and the reader offers the extension, which is windowed.
            if (
                len(referent_roles) == 1
                and len(scalar_roles) == 1
                and count <= MAX_FIELDS
            ):
                found = self._store.query(
                    f'SELECT * FROM "{record["name"]}" WHERE {where}', arguments
                )
                for row in found:
                    fields.append(
                        {
                            "relation": record["name"],
                            "role": scalar_roles[0].name,
                            "value": row[scalar_roles[0].column],
                            "assertion_id": row["_assertion_id"],
                            "origin": self._origin(row["_assertion_id"]),
                            "origins": self._origins(row["_assertion_id"]),
                        }
                    )
                continue
            relations.append(
                {
                    "name": record["name"],
                    "arity": len(roles),
                    "mode": record["mode"],
                    "stale": record["stale"],
                    "count": count,
                }
            )
        return {
            "id": rows[0]["id"],
            "label": rows[0]["label"],
            "grounding": self._grounding("REFERENT", referent_id),
            "fields": fields,
            "relations": sorted(relations, key=lambda item: item["name"]),
        }

    def expand(
        self, referent_id: str, relation: str, *, limit: int = MAX_ROWS
    ) -> dict[str, Any]:
        """The tuples of one relation that this referent takes part in."""
        record = self._relation(relation)
        roles = self._roles(record)
        referent_roles = [role for role in roles if role.referent]
        if not referent_roles:
            return {"relation": relation, "roles": [r.name for r in roles], "tuples": []}
        where = " OR ".join(f'"{role.column}" = ?' for role in referent_roles)
        rows = self._store.query(
            f'SELECT * FROM "{relation}" WHERE {where} LIMIT ?',
            [referent_id] * len(referent_roles) + [min(limit, MAX_ROWS)],
        )
        return {
            "relation": relation,
            "arity": len(roles),
            "roles": [
                {
                    "name": role.name,
                    "type": role.type,
                    "referent": role.referent,
                    **(
                        {"reference_kind": role.reference_kind}
                        if role.reference_kind
                        else {}
                    ),
                }
                for role in roles
            ],
            "tuples": [self._row_out(roles, row) for row in rows],
        }

    # -- §8.3 relation extension -------------------------------------------

    def rows(
        self,
        relation: str,
        *,
        limit: int = 200,
        offset: int = 0,
        order: str | None = None,
        descending: bool = False,
        subject: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        """One page of a relation's extension, ordered in SQL.

        Sorting is the database's job, not the table component's. SQLite orders
        the largest relation in this world in well under a millisecond, and a
        client-side sort would only ever see the page it already has.

        `subject` narrows the extension to the tuples one referent takes part
        in — the same predicate `expand` uses, because it is the same question
        asked of a surface that pages instead of drawing. A referent's panel
        offers its own count, so a table opened from there that answered with
        the whole relation would be answering a question nobody asked. The
        total is the filtered total for the same reason.
        """
        record = self._relation(relation)
        roles = self._roles(record)
        columns = {role.name: role.column for role in roles}
        clause = ""
        if order:
            if order not in columns:
                raise KeyError(f"{relation!r} has no role {order!r}")
            clause = f' ORDER BY "{columns[order]}" {"DESC" if descending else "ASC"}'

        where = ""
        subject_values: list[Any] = []
        total = record["row_count"]
        if subject is not None:
            referent_roles = [role for role in roles if role.referent]
            if not referent_roles:
                return {
                    "relation": relation,
                    "mode": record["mode"],
                    "stale": record["stale"],
                    "total": 0,
                    "offset": offset,
                    "roles": [
                        {"name": role.name, "type": role.type, "referent": role.referent}
                        for role in roles
                    ],
                    "rows": [],
                }
            predicate = " OR ".join(f'"{role.column}" = ?' for role in referent_roles)
            where = f" WHERE ({predicate})"
            subject_values = [subject] * len(referent_roles)
            total = self._store.query(
                f'SELECT COUNT(*) AS n FROM "{relation}"{where}', subject_values
            )[0]["n"]

        if search and search.strip():
            # Literal substring search across every role, before paging/counting.
            predicate = " OR ".join(
                f'instr(lower(CAST("{role.column}" AS TEXT)), lower(?)) > 0'
                for role in roles
            ) or "0"
            where += (" AND " if where else " WHERE ") + f"({predicate})"
            subject_values.extend([search.strip()] * len(roles))
            total = self._store.query(
                f'SELECT COUNT(*) AS n FROM "{relation}"{where}', subject_values
            )[0]["n"]

        rows = self._store.query(
            f'SELECT * FROM "{relation}"{where}{clause} LIMIT ? OFFSET ?',
            [*subject_values, min(limit, MAX_ROWS), max(0, offset)],
        )
        return {
            "relation": relation,
            "mode": record["mode"],
            "stale": record["stale"],
            "total": total,
            "offset": offset,
            "roles": [
                {"name": role.name, "type": role.type, "referent": role.referent}
                for role in roles
            ],
            "rows": [self._row_out(roles, row) for row in rows],
        }

    def query(self, sql: str, parameters: Sequence[Any] = ()) -> list[dict[str, Any]]:
        """The SQL surface, unhidden. Read-only by construction upstream."""
        return self._world.query(sql, parameters)

    def query_semantic(self, sql: str, parameters: Sequence[Any] = ()) -> list[dict[str, Any]]:
        """Read only declared semantic relation tables."""
        return self._world.query_semantic(sql, parameters)

    # -- §8.4 / §8.5 / §8.6 assertion, grounding, derivation ---------------

    def assertion(self, assertion_id: str) -> dict[str, Any]:
        """Everything §8.4 asks for about one tuple, addressed by its id.

        By id rather than by role values because that is what a row and a chip
        both carry, and reconstructing a values map to look a tuple back up is
        an opportunity to get it subtly wrong.
        """
        found = self._store.query(
            "SELECT relation_name, origin, created_revision FROM _world_assertions "
            "WHERE assertion_id = ?",
            (assertion_id,),
        )
        if not found:
            raise KeyError(f"no assertion {assertion_id!r} in this world")
        relation = found[0]["relation_name"]
        record = self._relation(relation)
        roles = self._roles(record)
        rows = self._store.query(
            f'SELECT * FROM "{relation}" WHERE _assertion_id = ?', (assertion_id,)
        )
        values = {role.name: rows[0][role.column] for role in roles} if rows else {}
        out: dict[str, Any] = {
            "assertion_id": assertion_id,
            "relation": relation,
            "mode": record["mode"],
            "arity": len(roles),
            "roles": [
                {"name": role.name, "type": role.type, "referent": role.referent}
                for role in roles
            ],
            "values": values,
            "commitment_id": assertion_id,
            # The product's origin (who decided this), not the store's
            # (how it got into the table). Both are reported, because a reader
            # asking "why is this here" is served by neither alone.
            "origin": self._origin(assertion_id),
            "origins": self._origins(assertion_id),
            "assertion_state": found[0]["origin"],
            "created_revision": int(found[0]["created_revision"]),
            "relation_stale": record["stale"],
            "completeness": self._completeness_out(record["completeness"]),
            "grounding": self._grounding("ASSERTION", assertion_id),
            "warrant": self._world.warrant_for_assertion(assertion_id),
            "candidate_for": self._world.obligations_for(assertion_id),
        }
        assessments: list[dict[str, Any]] = []
        governing: list[str] = []
        for obligation_id in out["candidate_for"]:
            resolution = self._world.resolution(obligation_id)
            if resolution is None:
                continue
            if resolution.get("selected_commitment_id") == assertion_id:
                governing.append(obligation_id)
            for assessment in resolution.get("candidate_assessments", []):
                if (
                    isinstance(assessment, Mapping)
                    and assessment.get("commitment_id") == assertion_id
                ):
                    assessments.append(
                        {"obligation_id": obligation_id, **dict(assessment)}
                    )
        out["governing_obligations"] = governing
        out["candidate_assessments"] = assessments
        if record["mode"] == "DERIVED":
            out["derivation"] = {
                **(record.get("derivation") or {}),
                "inputs": self.derivation_inputs(relation),
            }
        return out

    # -- §8.6 the derivation explorer ---------------------------------------

    def derivation(self, relation: str) -> dict[str, Any]:
        """What a relation rests on, and what rests on it.

        §8.6 draws the upward tree — `eligible_part ↑ voltage_compatible …` —
        and §21 asks the other question too: *what computation depends on this?*
        A base relation has no derivation of its own and is still worth asking
        about, because the answer for `rated_voltage` is that two derived
        relations read it and one of those feeds a third. Both directions are
        one edge table read from opposite ends, so both are answered here
        rather than by two half-endpoints.

        Returned as adjacency plus a node for every relation reached, not as a
        nested tree. A relation can sit at more than one place in the closure —
        `part_type` feeds both compatibility relations — and a nested tree would
        either duplicate it or silently drop the second path. The front end
        draws a tree; the closure is what is true.

        The run record is where staleness stops being a flag and becomes an
        account. WorldStore remembers the version and cardinality of every input
        as it stood when the derivation last ran, so each can be compared
        against the same relation now: an input that has moved since is the
        reason the output is suspect, named. Inputs the engine snapshotted but
        the dependency table does not declare are reported as what they are
        rather than quietly merged, because the difference between "the SQL
        reads this" and "the run held this" is a fact about the world.
        """
        record = self._relation(relation)
        described = {item["name"]: item for item in self._described()}

        upward: dict[str, list[str]] = {}
        downward: dict[str, list[str]] = {}
        for row in self._store.query(
            "SELECT relation_name, input_relation FROM _world_derivation_inputs "
            "ORDER BY relation_name, input_relation"
        ):
            upward.setdefault(row["relation_name"], []).append(row["input_relation"])
            downward.setdefault(row["input_relation"], []).append(row["relation_name"])

        nodes: dict[str, dict[str, Any]] = {}

        def note(name: str) -> None:
            if name in nodes:
                return
            found = described.get(name)
            derivation = (found or {}).get("derivation") or {}
            nodes[name] = {
                "name": name,
                "mode": found["mode"] if found else "BASE",
                "arity": len(found["roles"]) if found else 0,
                "count": found["row_count"] if found else 0,
                "stale": bool(found["stale"]) if found else False,
                "state": derivation.get("state"),
            }

        def walk(
            name: str,
            adjacency: Mapping[str, list[str]],
            into: dict[str, list[str]],
            seen: set[str],
        ) -> None:
            note(name)
            # Guarded before the edges are written rather than after, so a
            # relation reached twice is one node with one edge list, and a
            # cycle — which a derivation graph should not have and might —
            # terminates instead of recurring.
            if name in seen:
                return
            seen.add(name)
            reached = adjacency.get(name, [])
            if reached:
                into[name] = list(reached)
            for other in reached:
                walk(other, adjacency, into, seen)

        rests_on: dict[str, list[str]] = {}
        supports: dict[str, list[str]] = {}
        walk(relation, upward, rests_on, set())
        walk(relation, downward, supports, set())

        run: dict[str, Any] | None = None
        if record["mode"] == "DERIVED":
            held = self._store.query(
                "SELECT sql, definition_revision, execution_status, "
                "last_run_world_revision, result_fingerprint, output_cardinality, "
                "last_error FROM _world_derivations WHERE relation_name = ?",
                (relation,),
            )
            if held:
                taken = {
                    row["input_relation"]: row
                    for row in self._store.query(
                        "SELECT input_relation, relation_version, cardinality "
                        "FROM _world_derivation_run_inputs WHERE relation_name = ?",
                        (relation,),
                    )
                }
                declared = set(upward.get(relation, []))
                inputs: list[dict[str, Any]] = []
                for name in sorted(declared | set(taken)):
                    note(name)
                    found = described.get(name)
                    at_run = taken.get(name)
                    version_now = found["relation_version"] if found else None
                    version_at_run = at_run["relation_version"] if at_run else None
                    inputs.append(
                        {
                            "relation": name,
                            "declared": name in declared,
                            "version_at_run": version_at_run,
                            "count_at_run": at_run["cardinality"] if at_run else None,
                            "version_now": version_now,
                            "count_now": found["row_count"] if found else None,
                            "moved": (
                                version_at_run is not None
                                and version_now is not None
                                and version_now != version_at_run
                            ),
                        }
                    )
                run = {
                    "sql": held[0]["sql"],
                    "state": held[0]["execution_status"],
                    "definition_revision": held[0]["definition_revision"],
                    "last_run_world_revision": held[0]["last_run_world_revision"],
                    "output_cardinality": held[0]["output_cardinality"],
                    "last_error": held[0]["last_error"],
                    "inputs": inputs,
                }

        return {
            "relation": relation,
            "mode": record["mode"],
            "rests_on": rests_on,
            "supports": supports,
            "nodes": nodes,
            "run": run,
        }

    #: Candidate support tuples reported per input relation, before the answer
    #: stops being an explanation and starts being an extension.
    MAX_SUPPORT = 8

    def derivation_support(self, assertion_id: str) -> dict[str, Any]:
        """Input tuples that mention this derived tuple's referents.

        §8.6 asks for drill-down from relation-level dependency into
        tuple-level provenance *where available* — and here it is not. WorldStore
        records lineage per relation, not per row: no table in this world says
        which input rows produced this output row. Rather than invent that edge
        and draw it as if the world had asserted it, this answers the question
        the store can actually answer — which tuples of each declared input
        mention the referents this tuple is about — and is named for what it
        is. They are candidates, ranked by how many of the referents they
        mention, and the derivation's SQL beside them is the recorded truth
        about how inputs combine. An exact miss stays an exact miss; a search
        result stays a candidate.
        """
        head = self.assertion(assertion_id)
        out: dict[str, Any] = {
            "assertion_id": assertion_id,
            "relation": head["relation"],
            "derived": head["mode"] == "DERIVED",
            "referents": [],
            "inputs": [],
        }
        if not out["derived"]:
            return out

        wanted = [
            str(head["values"][role["name"]])
            for role in head["roles"]
            if role["referent"] and head["values"].get(role["name"]) is not None
        ]
        out["referents"] = wanted
        if not wanted:
            return out
        marks = ",".join("?" * len(wanted))

        for name in self.derivation_inputs(head["relation"]):
            record = self._relation(name)
            roles = self._roles(record)
            referent_roles = [role for role in roles if role.referent]
            answer: dict[str, Any] = {
                "relation": name,
                "mode": record["mode"],
                "stale": record["stale"],
                "count": record["row_count"],
                "matched": 0,
                "roles": [
                    {"name": role.name, "type": role.type, "referent": role.referent}
                    for role in roles
                ],
                "tuples": [],
            }
            if referent_roles:
                score = " + ".join(
                    f'(CASE WHEN "{role.column}" IN ({marks}) THEN 1 ELSE 0 END)'
                    for role in referent_roles
                )
                # The score is repeated rather than referenced by alias: an
                # alias in WHERE is a SQLite extension, and this file is the
                # one place a portability accident would be silent.
                values = wanted * len(referent_roles)
                answer["matched"] = self._store.query(
                    f'SELECT COUNT(*) AS n FROM "{name}" WHERE ({score}) > 0', values
                )[0]["n"]
                rows = self._store.query(
                    f'SELECT *, ({score}) AS _support FROM "{name}" '
                    f"WHERE ({score}) > 0 ORDER BY _support DESC LIMIT ?",
                    [*values, *values, self.MAX_SUPPORT],
                )
                answer["tuples"] = [
                    {**self._row_out(roles, row), "mentions": int(row["_support"])}
                    for row in rows
                ]
            out["inputs"].append(answer)
        return out

    # -- Legacy Purpose frontier -------------------------------------------

    def demand(self) -> dict[str, Any] | None:
        """What a declared purpose asked of this world, and what it did not get.

        Returns `None` when no legacy Purpose demand is loaded. Durable
        law-generated Obligations are read through ``obligations()`` instead;
        they are never appended to this payload.
        """
        return self._purpose_frontier()

    def _governed_obligation_rows(self) -> list[dict[str, Any]]:
        obligations: list[dict[str, Any]] = []
        generated = (
            (self._obligations_document or {}).get("obligations", {})
            if isinstance(self._obligations_document, Mapping)
            else {}
        )
        for item in self._world.obligations():
            obligation_id = str(item["obligation_id"])
            provenance = generated.get(obligation_id, {})
            obligation = {
                "obligation_id": obligation_id,
                "question": item["question"],
                "relation": None,
                "values": {},
                "reason": item["reason"] or None,
                "demanded_by": {
                    "kind": "contract",
                    "name": obligation_id,
                    "contract_id": item["contract_id"],
                    "contract_revision": item["contract_revision"],
                },
                "state": item["state"],
                "assertion_id": None,
                "record_id": None,
                "grounding_ref": None,
                "contract_id": item["contract_id"],
                "contract_revision": item["contract_revision"],
                "candidates": self._contract_candidates(obligation_id),
            }
            if provenance:
                obligation.update(
                    {
                        "dimension": provenance.get("dimension"),
                        "generated_by_rule": provenance.get("rule_id"),
                        "law_provenance": provenance.get("law_provenance"),
                        "structural_bindings": provenance.get("bindings", {}),
                    }
                )
            resolution_status = item.get("resolution_status")
            if resolution_status:
                obligation["resolution"] = {
                    "resolution_id": f"resolution:{obligation_id}",
                    "obligation_id": obligation_id,
                    "status": resolution_status,
                    "selected_commitment_id": item.get("selected_commitment_id"),
                    "reason": item.get("resolution_reason") or "",
                    "contract_id": item["contract_id"],
                    "contract_revision": item["contract_revision"],
                    "candidate_assessments": item.get("candidate_assessments", []),
                    "adjudication_assessments": item.get(
                        "adjudication_assessments", []
                    ),
                    "resolution_basis": item.get("resolution_basis", []),
                }
            obligations.append(obligation)
        return obligations

    def _contract_candidates(
        self,
        obligation_id: str,
        *,
        detailed: bool = False,
        resolution: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Read the kernel candidate association, not a domain relation."""

        links = [
            {
                # Keep the human-facing name for the association while making
                # clear that it has no semantic assertion id of its own.
                "relation": "candidate_for",
                "association_id": item["association_id"],
                "obligation_id": item["obligation_id"],
                "commitment_id": item["commitment_id"],
                "created_revision": item["created_revision"],
            }
            for item in self._world.candidate_associations()
            if item["obligation_id"] == obligation_id
        ]
        if not detailed:
            for item in links:
                item.pop("obligation_id", None)
            return links

        candidate_assessments = {
            str(assessment.get("commitment_id")): assessment
            for assessment in (
                resolution.get("candidate_assessments", [])
                if isinstance(resolution, Mapping)
                else []
            )
            if isinstance(assessment, Mapping) and assessment.get("commitment_id")
        }
        selected = (
            str(resolution.get("selected_commitment_id"))
            if isinstance(resolution, Mapping)
            and resolution.get("selected_commitment_id")
            else None
        )
        detailed_links: list[dict[str, Any]] = []
        for link in links:
            commitment = self.assertion(str(link["commitment_id"]))
            detailed_links.append(
                {
                    **link,
                    "commitment": {
                        "commitment_id": commitment["commitment_id"],
                        "assertion_id": commitment["assertion_id"],
                        "relation": commitment["relation"],
                        "roles": commitment["roles"],
                        "values": commitment["values"],
                        "origin": commitment["origin"],
                        "created_revision": commitment["created_revision"],
                    },
                    "warrant": commitment["warrant"],
                    "grounding": commitment["grounding"],
                    "assessment": candidate_assessments.get(
                        str(link["commitment_id"])
                    ),
                    "governing": selected == str(link["commitment_id"]),
                }
            )
        return detailed_links

    def _purpose_frontier(self) -> dict[str, Any] | None:
        """The same frontier, read off a world rebuilt by the v1 boundary.

        Every obligation here is unresolved. `purpose_requirement_failure`
        holds only what a requirement did *not* get; a requirement the world
        satisfied leaves no row. So this lineage cannot show the quiet resolved
        half of a frontier the way a frozen obligation set can — where the
        frontier moved is a question about two revisions, which is what the
        delta answers, not something a single world can be asked.
        """
        rows = self._failure_rows()
        document = self._purpose_document
        if document is None and not rows:
            return None
        requirements = list((document or {}).get("requirements", []))
        obligations: list[dict[str, Any]] = []
        for row in rows:
            subject = self._failure_subject(row["subject_json"])
            # `reason` is prose the constructor wrote about why this is
            # unresolved, not a value of any role. Left inside `values` it
            # would be printed as part of the demanded tuple.
            reason = subject.pop("reason", None)
            obligations.append(
                {
                    "relation": row["relation_name"],
                    "values": subject,
                    "reason": reason,
                    "demanded_by": {
                        "kind": "requirement",
                        "name": row["requirement_id"],
                        "failure_kind": row["failure_kind"],
                    },
                    "state": "UNRESOLVED",
                    # No assertion establishes the demanded meaning — that is
                    # what makes it unresolved. `record_id` is the failure
                    # tuple itself, an ordinary assertion, readable as one.
                    "assertion_id": None,
                    "record_id": row["_assertion_id"],
                    "grounding_ref": row["grounding_ref"] or None,
                }
            )
        failures_by_requirement: dict[str, int] = {}
        for row in rows:
            name = str(row["requirement_id"])
            failures_by_requirement[name] = failures_by_requirement.get(name, 0) + 1
        return {
            "purpose": {"statement": str((document or {}).get("text", "")).strip()},
            "rule": None,
            "demanded": len(requirements) or len(rows),
            "obligations": obligations,
            # Relation-level, and additive: the declarations themselves, each
            # carrying how many tuples failed it. An obligation says a tuple is
            # missing; a requirement says what was wanted in the first place.
            "requirements": [
                {
                    "name": item.get("name"),
                    "kind": item.get("kind"),
                    "relation": item.get("relation"),
                    "note": item.get("note", ""),
                    "failures": failures_by_requirement.get(str(item.get("name")), 0),
                }
                for item in requirements
            ],
        }

    def _failure_rows(self) -> list[dict[str, Any]]:
        """Read through, every call. These are world state, not a sidecar."""
        if not any(
            record["name"] == PURPOSE_FAILURE_RELATION for record in self._described()
        ):
            return []
        return self._store.query(
            f'SELECT _assertion_id, requirement_id, affected_identity, failure_kind, '
            f'relation_name, subject_json, grounding_ref FROM "{PURPOSE_FAILURE_RELATION}"'
        )

    @staticmethod
    def _failure_subject(raw: Any) -> dict[str, Any]:
        """The subject a requirement failed on, opened up.

        Stored as a JSON string because it is one role of an ordinary relation.
        A subject this layer cannot parse is still a subject: it comes back
        under `subject` rather than being dropped, for the same reason a
        grounding whose detail will not parse keeps its text.
        """
        try:
            parsed = json.loads(raw) if raw else {}
        except (TypeError, ValueError):
            return {"subject": raw}
        return parsed if isinstance(parsed, dict) else {"subject": parsed}


def _quote_identifier(value: str) -> str:
    return '"' + str(value).replace('"', '""') + '"'


def open_world(path: Path | str, *, world_id: str | None = None) -> WorldExplorerAdapter:
    return WorldExplorerAdapter(path, world_id=world_id)


__all__ = [
    "MAX_FIELDS",
    "MAX_ROWS",
    "PURPOSE_FAILURE_RELATION",
    "world_id_of",
    "UNKNOWN_ORIGIN",
    "Role",
    "WorldExplorerAdapter",
    "open_world",
]
