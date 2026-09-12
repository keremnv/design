/**
 * The `/world` read plane, typed.
 *
 * Every shape here is what the World read adapter returns, named once so a
 * surface cannot invent a field the server does not send. Nothing writes:
 * there is no route to write to, and this file imports only `read`.
 */

import { read } from "./plane";

export type RoleKindList = string[];

export type WorldRole = {
  name: string;
  type: string;
  column?: string;
  referent: boolean;
  /** Referent namespaces this role has actually been filled with. */
  kinds?: RoleKindList;
};

export type WorldCompleteness = {
  status: "COMPLETE" | "INCOMPLETE" | "UNKNOWN";
  universe: string | null;
  current: boolean;
  known_gaps: unknown[];
};

export type WorldRelation = {
  name: string;
  description: string | null;
  mode: "BASE" | "DERIVED";
  arity: number;
  referent_arity: number;
  roles: WorldRole[];
  count: number;
  stale: boolean;
  /**
   * Construction origins observed in this relation's tuples.
   *
   * SHOW reads this, not mode: a BASE relation can be SEMANTIC
   * (`acceptable_replacement`) or MECHANICAL (`listing_of`), and collapsing
   * those onto BASE would hide the semantic seam the toggle exists to keep.
   */
  origins: string[];
  /**
   * WORLD or PURPOSE, from the admission sidecar — `null` where none was
   * recorded.
   *
   * Not derivable from anything else here: a PURPOSE relation is an artefact
   * of one purpose's bookkeeping, a WORLD relation is a claim about the world,
   * and nothing about mode, arity or origin separates them. `null` means the
   * world carries no admission document — never assume WORLD, which is the
   * stronger claim.
   */
  scope: "WORLD" | "PURPOSE" | null;
  completeness: WorldCompleteness | null;
  derivation?: { state?: string; inputs: string[] } & Record<string, unknown>;
};

export type WorldOverview = {
  world_id: string;
  revision: number;
  contract?: Record<string, string> | null;
  governance?: Record<string, string> | null;
  evidence_authority?: Record<string, string> | null;
  adjudication_authority?: Record<string, string> | null;
  relations: number;
  referents: number;
  assertions: number;
  origins: Record<string, number>;
  stale: string[];
  /** Relations whose completeness receipt exists and is not COMPLETE. */
  incomplete: string[];
  /** Null when no purpose is loaded — see `WorldDemand` for the id/revision. */
  demand: {
    purpose: { id?: string; revision?: number; statement: string };
    obligations: number;
    demanded: number;
  } | null;
  /** Durable Law-generated questions; independent of Purpose demand. */
  governed_obligations: {
    count: number;
    resolved: number;
    unresolved: number;
  } | null;
};

export type WorldGrounding = {
  kind: string;
  reference: string;
  native_handle?: string;
  native_location?: string;
  provider?: string;
  source_revision?: string;
  construction_method?: string;
  construction_origin?: string;
  detail?: Record<string, unknown>;
  detail_text?: string;
};

export type WorldWarrantBase = {
  kind: string;
  reference: string;
  detail?: Record<string, unknown>;
  detail_text?: string;
  [key: string]: unknown;
};

export type WorldWarrant = {
  commitment_id: string;
  relation: string;
  assertion_origin: string;
  recorded_construction_origin: string;
  construction_origins: string[];
  created_revision: number;
  bases: WorldWarrantBase[];
};

export type WorldResolutionStatus =
  | "RESOLVED"
  | "NO_CANDIDATE"
  | "INSUFFICIENT_WARRANT"
  | "CONFLICT"
  | "AMBIGUOUS";

export type WorldCandidateAssessment = {
  commitment_id: string;
  status: "SUFFICIENT" | "INSUFFICIENT";
  reason: string;
  warrant_authorities: string[];
  authority_basis: Record<string, unknown>[];
};

export type WorldAdjudicationAssessment = {
  adjudication_id: string;
  selected_commitment_id: string;
  status: "SUFFICIENT" | "INSUFFICIENT";
  reason: string;
  adjudicative_authorities: string[];
  authority_basis: Record<string, unknown>[];
};

export type WorldResolution = {
  resolution_id: string;
  obligation_id: string;
  status: WorldResolutionStatus;
  selected_commitment_id: string | null;
  reason: string;
  contract_id: string;
  contract_revision: string;
  candidate_assessments: WorldCandidateAssessment[];
  adjudication_assessments: WorldAdjudicationAssessment[];
  resolution_basis: Record<string, unknown>[];
};

export type WorldCandidateLink = {
  relation: "candidate_for";
  association_id: string;
  commitment_id: string;
  created_revision: number;
};

export type WorldCommitment = {
  commitment_id: string;
  assertion_id: string;
  relation: string;
  roles: WorldRole[];
  values: Record<string, unknown>;
  origin: string;
  created_revision: number;
};

export type WorldCandidate = WorldCandidateLink & {
  obligation_id: string;
  commitment: WorldCommitment;
  warrant: WorldWarrant;
  grounding: WorldGrounding[];
  assessment: WorldCandidateAssessment | null;
  governing: boolean;
};

export type WorldLawProvenance = {
  rule_id?: string;
  source_id?: string;
  source_revision?: string;
  source_location?: string;
  source_excerpt?: string;
  interpretation_method?: string;
  [key: string]: unknown;
};

export type WorldObligation = {
  obligation_id: string;
  question: string;
  dimension?: string | null;
  relation: null;
  values: Record<string, unknown>;
  reason: string | null;
  demanded_by: Record<string, unknown>;
  state: "RESOLVED" | "UNRESOLVED";
  assertion_id: null;
  record_id: null;
  grounding_ref: null;
  contract_id: string;
  contract_revision: string;
  generated_by_rule?: string | null;
  law_provenance?: WorldLawProvenance | null;
  structural_bindings?: Record<string, unknown>;
  candidates: WorldCandidateLink[];
  resolution?: WorldResolution;
};

/** A durable governed Obligation as returned by the collection read. */
export type WorldObligationSummary = WorldObligation;

export type WorldObligationsRead = {
  contract: Record<string, string> | null;
  governance: Record<string, string> | null;
  obligations: WorldObligationSummary[];
};

export type WorldAdjudicationInspection = {
  record: {
    adjudication_id: string;
    obligation_id: string;
    selected_commitment_id: string;
    authority_basis: Record<string, unknown>;
    contract_id: string;
    contract_revision: string;
    [key: string]: unknown;
  };
  assessment: WorldAdjudicationAssessment | null;
};

export type WorldObligationInspection = Omit<WorldObligation, "candidates"> & {
  candidates: WorldCandidate[];
  adjudications: WorldAdjudicationInspection[];
  context: {
    contract: Record<string, string> | null;
    governance: Record<string, string> | null;
    evidence_authority: Record<string, string> | null;
    adjudication_authority: Record<string, string> | null;
  };
};

export type WorldTuple = {
  assertion_id: string;
  /** Scalar compatibility summary; use `origins` for the complete answer. */
  origin: string;
  /** Every construction/support-path origin represented by this assertion. */
  origins?: string[];
  values: Record<string, unknown>;
};

export type WorldAssertion = WorldTuple & {
  relation: string;
  mode: "BASE" | "DERIVED";
  arity: number;
  roles: WorldRole[];
  assertion_state: string;
  created_revision: number;
  relation_stale: boolean;
  completeness: WorldCompleteness | null;
  grounding: WorldGrounding[];
  warrant: WorldWarrant;
  commitment_id: string;
  candidate_for: string[];
  governing_obligations: string[];
  candidate_assessments: (WorldCandidateAssessment & {
    obligation_id: string;
  })[];
  derivation?: { inputs: string[] } & Record<string, unknown>;
};

export type WorldReferent = {
  id: string;
  label: string | null;
  grounding: WorldGrounding[];
  fields: {
    relation: string;
    role: string;
    value: unknown;
    assertion_id: string;
    origin: string;
    origins?: string[];
  }[];
  relations: {
    name: string;
    arity: number;
    mode: string;
    stale: boolean;
    count: number;
  }[];
};

export type WorldRows = {
  relation: string;
  mode: "BASE" | "DERIVED";
  stale: boolean;
  total: number;
  offset: number;
  roles: WorldRole[];
  rows: WorldTuple[];
};

/**
 * §8.6. What a relation rests on, and what rests on it.
 *
 * Adjacency rather than a nested tree, because a relation can sit at more than
 * one place in the closure — `part_type` feeds both compatibility relations —
 * and a tree would either duplicate it or drop the second path. The panel
 * draws a tree from this; the closure is what is true.
 */
export type WorldDerivation = {
  relation: string;
  mode: "BASE" | "DERIVED";
  /** relation → the relations it reads, for the whole upward closure. */
  rests_on: Record<string, string[]>;
  /** relation → the relations that read it, for the whole downward closure. */
  supports: Record<string, string[]>;
  nodes: Record<
    string,
    {
      name: string;
      mode: "BASE" | "DERIVED";
      arity: number;
      count: number;
      stale: boolean;
      state: string | null;
    }
  >;
  run: {
    sql: string;
    state: string;
    definition_revision: number;
    last_run_world_revision: number | null;
    output_cardinality: number | null;
    last_error: string;
    /** Each input as it stood when the derivation last ran, beside now. */
    inputs: {
      relation: string;
      declared: boolean;
      version_at_run: number | null;
      count_at_run: number | null;
      version_now: number | null;
      count_now: number | null;
      moved: boolean;
    }[];
  } | null;
};

/**
 * Tuple-level drill-down, and it is candidates rather than lineage.
 *
 * The world records derivation per relation, not per row, so nothing here says
 * which input rows produced this one. What it says is which input tuples
 * mention the same referents, and how many of them each mentions. The
 * derivation's SQL is the recorded truth about how they combine.
 */
export type WorldSupport = {
  assertion_id: string;
  relation: string;
  derived: boolean;
  referents: string[];
  inputs: {
    relation: string;
    mode: "BASE" | "DERIVED";
    stale: boolean;
    count: number;
    matched: number;
    roles: WorldRole[];
    tuples: (WorldTuple & { mentions: number })[];
  }[];
};

/**
 * The legacy unresolved frontier recorded for a World Purpose. Durable
 * governed Obligations are returned by `/world/obligations` and are not tuple
 * failures.
 *
 * `rule` is optional because a purpose is prose plus construction state, not a
 * separate obligation compiler.
 * `requirements` is the relation-level summary of what the purpose asked for,
 * alongside any unresolved tuples.
 */
export type LegacyWorldObligation = {
  relation: string;
  values: Record<string, unknown>;
  demanded_by: Record<string, unknown>;
  state: "ASSERTED" | "UNRESOLVED";
  assertion_id: string | null;
  /** The failure tuple itself, where unresolvedness is world state. */
  record_id?: string;
  /** Why it is unresolved, where the constructor said so. Not a role value. */
  reason?: string | null;
  grounding_ref?: string | null;
};

export type WorldDemand = {
  purpose: { id?: string; revision?: number; statement: string };
  rule: string | null;
  demanded: number;
  obligations: LegacyWorldObligation[];
  requirements?: {
    name: string;
    kind: string;
    relation: string | null;
    note: string;
    failures: number;
  }[];
};

export const worldApi = {
  overview: () => read<WorldOverview>("/world/overview"),
  schema: () =>
    read<{ relations: WorldRelation[] }>("/world/schema").then((r) => r.relations),
  /**
   * The referent directory — bounded, and it says when it is short.
   *
   * The canvas holds this and filters it as you type, which is right until the
   * world is large enough that opening the explorer costs a payload nobody
   * asked for. Past the plane's ceiling `truncated` is true and find has to ask
   * the plane instead of the array in front of it.
   */
  referents: () =>
    read<{
      referents: { id: string; label: string | null }[];
      total: number;
      truncated: boolean;
    }>("/world/referents"),
  /**
   * Ask the plane for referents matching a substring.
   *
   * The counterpart to a short directory. Results are candidates — the plane
   * matched a substring, which is not a claim that any of them is the thing
   * you meant.
   */
  search: (query: string, limit = 10) =>
    read<{
      results: { kind: string; id: string; label: string | null }[];
    }>(
      `/world/search?q=${encodeURIComponent(query)}&limit=${limit}`,
    ).then((r) => r.results),
  /** Labels for ids the directory did not carry. A lookup, not a search. */
  labels: (ids: string[]) =>
    ids.length
      ? read<{ labels: Record<string, string | null> }>(
          `/world/labels?ids=${ids.map(encodeURIComponent).join(",")}`,
        ).then((r) => r.labels)
      : Promise.resolve({} as Record<string, string | null>),
  referent: (id: string) =>
    read<WorldReferent>(`/world/referent?id=${encodeURIComponent(id)}`),
  expand: (id: string, relation: string) =>
    read<{ relation: string; arity: number; roles: WorldRole[]; tuples: WorldTuple[] }>(
      `/world/expand?id=${encodeURIComponent(id)}&relation=${encodeURIComponent(relation)}`,
    ),
  rows: (
    relation: string,
    options: {
      search?: string;
      limit?: number;
      offset?: number;
      order?: string | null;
      desc?: boolean;
      /** Narrow the extension to one referent's tuples. */
      subject?: string | null;
    } = {},
  ) => {
    const query = new URLSearchParams({
      relation,
      limit: String(options.limit ?? 200),
      offset: String(options.offset ?? 0),
    });
    // Ordering is the database's, not the page's: a client-side sort would only
    // ever reach the rows already fetched, which for a windowed table is a
    // handful out of thousands.
    if (options.search) query.set("search", options.search);
    if (options.order) query.set("order", options.order);
    if (options.desc) query.set("desc", "1");
    if (options.subject) query.set("subject", options.subject);
    return read<WorldRows>(`/world/rows?${query}`);
  },
  assertion: (id: string) =>
    read<WorldAssertion>(`/world/assertion?id=${encodeURIComponent(id)}`),
  demand: () => read<{ demand: WorldDemand | null }>("/world/demand").then((r) => r.demand),
  obligations: () => read<WorldObligationsRead>("/world/obligations"),
  derivation: (relation: string) =>
    read<WorldDerivation>(`/world/derivation?relation=${encodeURIComponent(relation)}`),
  support: (id: string) =>
    read<WorldSupport>(`/world/support?id=${encodeURIComponent(id)}`),
  obligation: (id: string) =>
    read<WorldObligationInspection | null>(
      `/world/obligation?obligation_id=${encodeURIComponent(id)}`,
    ),
};
