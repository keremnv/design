/**
 * The field — a referent and the neighborhood someone grows around it.
 *
 * §7.2, and the mode the product actually lives in. What the schema canvas does
 * for vocabulary this does for instances, in the same two marks: discs are
 * referents, chips are assertions, and a bond is a chip that has a line to ride.
 *
 * Three behaviours are deliberate rather than defaults.
 *
 * **Marks are draggable.** A neighborhood is something a person arranges to
 * think with, so nodes are moved by hand and stay where they are put — dragged
 * positions are read back out of the renderer before any rebuild, so growing
 * the field never undoes the arrangement.
 *
 * **Naming lights the bond.** At rest the field is discs and filaments and no
 * words but the referents' own; hovering a disc names what it touches. A
 * filament is not a hover target — pointing at the line does not name it, does
 * not light it, and does not change the cursor. Selection still names, because
 * that is a choice rather than a pass.
 *
 * **Selection is marching ants.** The mark the reader is open on is ringed by
 * travelling beads — the product canvas's selection, brought over whole. It
 * replaces a translucent halo, which on a field of discs read as a smudge
 * rather than as a choice, and it generalises: a disc takes a circle, a plate
 * takes a square-cornered box, and a bond — which has no mark of its own — has
 * the beads march along the filament itself.
 *
 * **Focus only names.** Hover and selection reveal the labels belonging to the
 * subject without fading unrelated matter. This matches the product canvas and
 * keeps scanning the wider neighborhood possible while a relation is named.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Graph } from "@antv/g6";
import {
  bondFilament,
  bondPlateAlong,
  roleEnds,
  spokeLabelStation,
  BOND_LABEL_ALONG_PX,
  BOND_LABEL_STACK_MAX,
  SPOKE_LABEL_ALONG_PX,
  bondLabelLayout,
  bondLabelStep,
  chipKindOf,
  chipNode,
  chipWidth,
  discNode,
  discLabelTruncated,
  discRim,
  filamentEdge,
  furnitureOf,
  isDecoration,
  paintOf,
  plateRim,
  shelfNode,
  spokeEdge,
  spokeFilament,
  summaryEdge,
  MARK_DEPTH_STEP,
  NAME_RANK_SPAN,
  PAINT_LAYER_MARK,
  PAINT_LAYER_NAME,
  type MarkParams,
  type Paint,
} from "./marks";
import {
  GRAPH_DNA_INTERACTION,
  GRAPH_DNA_PROVISIONAL_THEME,
  GRAPH_DNA_THEME,
  type ThemeMode,
} from "../styles/graphDna";
import {
  DEFAULT_MOTION_PLANS,
  NODE_BIRTH_PLAN,
  NODE_COLLAPSE_PLAN,
  scaleMotionPlan,
  type MotionPlan,
  type MotionPlans,
} from "../styles/motion";
import { g6KeyframeMotion } from "../styles/motionG6";
import {
  bondStation,
  defaultStation,
  spokeStation,
  type Station,
  type StationMemory,
  type StationSubjects,
} from "./stations";
import {
  DEFAULT_LIGHT_FIELD,
  lift,
  NAMING_HOPS,
  reflected,
  type LightField,
} from "../styles/light";
import {
  ensureWorldFilamentRegistered,
  filamentLabelAnchor,
  type RoleEnds,
} from "./filaments";
import { labelUnderPointer } from "./labelPick";
import {
  createSpreadField,
  SPREAD_FRAME_EVENT,
  spreadOwnerForSelection,
  spreadYieldsToHold,
  type SpreadField,
  type SpreadYieldScope,
} from "./spread";
import {
  compareRanks,
  paintedLabelBox,
  paintedMarkBox,
  resolveVisibility,
  stampLabelStrength,
  visibilityKindOf,
  VISIBILITY_STRENGTHS_ON,
  type VisibilityBox,
  type VisibilityOccluder,
  type VisibilityRank,
} from "./visibility";
import { hopsFrom } from "./hops";
import { SelectionAnts, type AntTarget } from "../styles/SelectionAnts";
import { observeHostSize } from "./canvasHost";
import {
  convergeStrandedToFrame,
  paintLabelStrength,
  restyleCanvasData,
  transitionCanvasData,
  type CanvasData,
  type CanvasDatum,
} from "./canvasMotion";
import {
  resolveFocusId,
  useFocusPan,
  type CameraInsets,
} from "./canvasFocus";
import type { FieldBond, WorkingSet } from "./workingSet";
import {
  paintDepths,
  plateSeatClear,
  rankedDepths,
  restackTop,
} from "./workingSet";
import { createCameraRecorder, type CameraRecorder } from "./cameraMemory";
import {
  assertionShown,
  unsettled,
  type ShowState,
} from "./show";
import {
  IDLE_CONTACT,
  contactId,
  transitionContact,
  type ContactEvent,
  type ContactState,
} from "./canvasInteraction";

/**
 * The element id a bond's filament is drawn under.
 *
 * A tuple that folds is the same assertion in two drawings, but G6 keys nodes
 * and edges in **one** namespace, so the plate and the filament cannot share
 * the assertion's id: on `open`, G6 sees an element by that id already in the
 * scene and keeps the edge's `path` rather than building the plate's `rect`.
 * The plate keeps the assertion id — it is the form the shelf, the crown and
 * the spokes all hang off — and the filament is namespaced. Everything the
 * reader deals in is still the assertion id; `subjectOfBond` is where the
 * drawing's id turns back into the tuple's.
 */
function bondElementId(assertionId: string): string {
  return `bond:${assertionId}`;
}

/** One observer label for several assertions sharing the same filament. */
function bundleElementId(assertionId: string): string {
  return `bundle:${assertionId}`;
}

function subjectOfBundle(elementId: string): string | null {
  return elementId.startsWith("bundle:") ? elementId.slice(7) : null;
}

/**
 * The mark an element belongs to.
 *
 * Three suffixes and prefixes this surface adds on its own: a spoke carries
 * its index (`demand#0:1`), a filament is namespaced (`bond:…`, with the
 * shared stroke under `filament:…`), and furniture hangs off its chip
 * (`shelf:…`, `crown:…`). None of them are marks a reader deals in, so
 * anything asking *what is this part of* — a click, a hover, or how much
 * light falls on it — goes through here.
 */
export function markOfElement(elementId: string): string {
  const withoutIndex = elementId.replace(/:\d+$/, "");
  const withoutBond = subjectOfBond(withoutIndex);
  const withoutFilament = withoutBond.startsWith("filament:")
    ? withoutBond.slice(9)
    : withoutBond;
  return isDecoration(withoutFilament)
    ? withoutFilament.slice(withoutFilament.indexOf(":") + 1)
    : withoutFilament;
}

function subjectOfBond(elementId: string): string {
  return elementId.startsWith("bond:") ? elementId.slice(5) : elementId;
}

/**
 * One label's visibility rank from the attention subjects.
 *
 * The single place the field rank is computed: the strength pass settles ink
 * from it and the frame author stamps paint order from it, so the two systems
 * cannot disagree on who outranks whom. Lane-local, because the mapping from
 * element id to mark is this lane's own — the schema lane maps its own ids
 * to the same `VisibilityRank` shape.
 */
export function rankOfLabel(
  elementId: string,
  labelFontFamily: unknown,
  subjects: {
    selection: string | null;
    hover: string | null;
    named: Set<string> | null;
  },
): VisibilityRank {
  const owner = subjectOfBundle(elementId) ?? subjectOfBond(elementId);
  // A mark may itself end in a number. Match attention against its whole
  // address before interpreting a trailing number as a spoke index.
  const directlyNamed =
    owner === subjects.selection ||
    owner === subjects.hover ||
    subjects.named?.has(owner);
  const mark = directlyNamed ? owner : markOfElement(elementId);
  return {
    selection: mark === subjects.selection,
    hover: mark === subjects.hover,
    named: subjects.named?.has(mark) ?? false,
    kind: visibilityKindOf(labelFontFamily),
  };
}

/** Press and drag are node-local; edges and labels stay at rest until release. */
function contactOwnsPointer(phase: ContactState["phase"]) {
  return phase === "pressed" || phase === "dragging";
}

function liveAt(
  live: Map<string, { x: number; y: number }>,
  stored: Map<string, { x: number; y: number }>,
  id: string,
  fallback: { x: number; y: number } = { x: 0, y: 0 },
) {
  return live.get(id) ?? stored.get(id) ?? fallback;
}

/**
 * The live G6 edge, for a drag that must restation a plate without a draw.
 *
 * `graph.draw()` would re-apply stored node data and snap the mark back under
 * the pointer. The edge already re-strokes on each drag frame (`onframe`);
 * writing the 44px placement onto that same object is what keeps the plate
 * a fixed distance from the rim as the filament shortens.
 */
function liveEdge(
  graph: Graph,
  id: string,
): { parsedAttributes: Record<string, unknown>; onframe: () => void } | null {
  const context = (
    graph as unknown as {
      context?: { element?: { getElement: (id: string) => unknown } };
    }
  ).context;
  const el = context?.element?.getElement(id);
  if (!el || typeof el !== "object") return null;
  const edge = el as {
    parsedAttributes?: Record<string, unknown>;
    onframe?: () => void;
  };
  if (!edge.parsedAttributes || typeof edge.onframe !== "function") return null;
  // `onframe` calls other G6 edge methods through `this`. Returning the bare
  // method detaches it from the element, so dragging any connected node throws
  // while an isolated node appears to work — the inconsistency is topology,
  // not load. Preserve the receiver at this one renderer boundary.
  return {
    parsedAttributes: edge.parsedAttributes,
    onframe: edge.onframe.bind(el),
  };
}

/** Centre a restored field once, after the renderer has its real host size. */
async function centreStandingField(
  graph: Graph,
  ids: string[],
  insets: CameraInsets,
) {
  const [width, height] = graph.getSize();
  const points = ids
    .map((id) => graph.getElementPosition(id))
    .filter((point): point is [number, number, number] => Boolean(point))
    .map((point) => graph.getViewportByCanvas(point));
  if (!width || !height || !points.length) return;
  const minX = Math.min(...points.map((point) => point[0]));
  const maxX = Math.max(...points.map((point) => point[0]));
  const minY = Math.min(...points.map((point) => point[1]));
  const maxY = Math.max(...points.map((point) => point[1]));
  await graph.translateBy(
    [
      (insets.left + width - insets.right - minX - maxX) / 2,
      (insets.top + height - insets.bottom - minY - maxY) / 2,
    ],
    false,
  );
}

/** What a selection ring is drawn with. The DNA is the product's answer. */
export type AntTuning = {
  clearance: number;
  dotGap: number;
  lineWidth: number;
  speed: number;
  animated: boolean;
};

export const ANT_DEFAULTS: AntTuning = {
  clearance: GRAPH_DNA_INTERACTION.selectionClearance,
  dotGap: GRAPH_DNA_INTERACTION.selectionDotGap,
  lineWidth: GRAPH_DNA_INTERACTION.selectionLine,
  speed: GRAPH_DNA_INTERACTION.selectionSpeed,
  animated: GRAPH_DNA_INTERACTION.selectionMotion,
};

/** Competing observer-field treatments kept together for the trial. */
export type SelectionTreatment =
  | "outer-field"
  | "excited-boundary"
  | "hollow";

/**
 * The treatment both surfaces ship. Named rather than repeated, so the lab
 * opens on what the product draws instead of on a remembered string.
 */
export const SELECTION_TREATMENT_DEFAULT: SelectionTreatment = "hollow";

export type MaterialTuning = {
  /**
   * Whether a mark answers the pointer's load.
   *
   * The lab trial is adjudicated: on, on both surfaces. A disc that does not
   * yield under a press reads as a picture of a disc, and the deformation is
   * the cheapest way this canvas says a mark is a thing rather than a label.
   * Still a switch, because the lab is where it was decided and has to be able
   * to show the other answer.
   */
  contact: boolean;
  /** Resting diameter retained while pointer load is applied. */
  pressScale: number;
};

export const MATERIAL_DEFAULTS: MaterialTuning = {
  // Temporarily off: no press compression on nodes or their labels. The
  // mechanics stay (`animateContact`, `pressScale`) so this comes back by
  // flipping this to `true`; the lab can still opt a surface back in.
  contact: false,
  pressScale: 0.96,
};

function reducedMotion(): boolean {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/**
 * Which presses put the fan down while the pointer owns the field.
 *
 * The fan's own mark and its immediate neighbours: pressing the selected
 * mark to move it drops the fan for the gesture, the way it always did,
 * and so does pressing the other endpoint of one of its strokes, whose
 * drag pulls the geometry the elbows were solved for — see the note on the
 * `node:pointerdown` handler. `"owner"` keeps the fan up under a
 * neighbour's drag; `"any"` restores the old answer for every mark;
 * `"none"` switches the behaviour off entirely.
 */
const SPREAD_YIELDS_TO_HOLD: SpreadYieldScope = "neighbourhood";

type MaterialAnimation = {
  currentTime: number | null;
  finished: Promise<unknown>;
  cancel: () => void;
};

type MaterialShape = {
  attr: {
    (name: string): unknown;
    (attributes: Record<string, unknown>): void;
  };
  animate: (
    keyframes: Record<string, unknown>[],
    options: KeyframeAnimationOptions,
  ) => MaterialAnimation | null;
};

type MaterialElement = {
  getShape: (name: string) => MaterialShape | undefined;
};

type CanvasFrame = {
  nodes: CanvasDatum[];
  edges: CanvasDatum[];
  animateInitial: boolean;
  still: boolean;
  fieldIds: Set<string>;
  /**
   * This frame re-places matter that was already standing, because a person
   * asked it to. The one case where `marksNeverMove` is suspended, so it is
   * carried on the frame rather than inferred: a mark that moves for any other
   * reason is a bug, and a canvas that guessed could not tell them apart.
   */
  arranged: boolean;
};

export type CanvasSelection =
  | { kind: "referent"; id: string }
  | { kind: "assertion"; id: string }
  /** An obligation, which has no assertion to read — see §8.7. */
  | { kind: "demand"; id: string }
  | null;

export function WorldCanvas({
  set,
  mode,
  params,
  hovered,
  selection,
  show,
  focusId = null,
  focusToken = 0,
  arrangeToken = 0,
  foldSeed = null,
  animateInitial = false,
  still = false,
  insets,
  ants,
  motion = DEFAULT_MOTION_PLANS,
  material,
  selectionTreatment = SELECTION_TREATMENT_DEFAULT,
  spreadOnSelect = true,
  light,
  world = null,
  revision = null,
  onHover,
  onSelect,
  onPositions,
  onRemove,
}: {
  set: WorkingSet;
  mode: ThemeMode;
  params: MarkParams;
  hovered: string | null;
  selection: CanvasSelection;
  show: ShowState;
  /** A table-named mark to fly to. Canvas clicks do not set this. */
  focusId?: string | null;
  focusToken?: number;
  /**
   * Bumped when a person arranged the field.
   *
   * A token rather than a flag because the canvas has to distinguish *this*
   * arrangement from the next redraw of the same positions, and a flag would
   * have to be unset by whoever set it.
   */
  arrangeToken?: number;
  /**
   * The claim whose fold this frame answers, if the last act was an opening.
   *
   * The store seats the plate on the line's midpoint; the canvas reseats it
   * once where the bond's name actually stood, which a fan may have carried
   * elsewhere. Newborn-gated on the drawn ids rather than consumed, so a
   * rebuilt frame reseats the same way and a stale seed is a no-op.
   */
  foldSeed?: { id: string } | null;
  /** The first mark was just requested, rather than restored from memory. */
  animateInitial?: boolean;
  /**
   * Draw arrivals in this render without their lifecycle — a bulk add's pages
   * land as data, and the loading state lives on the control that asked for
   * them. Read where the frame is built, like `arranged`: the pump coalesces,
   * so a ref read at draw time could only say what the latest render wants.
   */
  still?: boolean;
  insets: CameraInsets;
  /**
   * The selection ring's tuning, for a surface that exists to tune it.
   *
   * Defaults to the DNA, which is what the product ships. It is a prop rather
   * than a second set of constants so the design lab drives the *same*
   * component the field draws: hand-drawn ant specimens had already grown
   * their own dash arithmetic and stopped matching what a selection looks
   * like.
   */
  ants?: Partial<AntTuning>;
  /** Shared plans; the lab may slow the same laws for inspection. */
  motion?: MotionPlans;
  /** Contact mechanics; see `MATERIAL_DEFAULTS`. On unless a caller says not. */
  material?: Partial<MaterialTuning>;
  /**
   * How a selected referent binds to the observer field.
   *
   * `hollow` on both surfaces. Selection withdraws the disc's optical fill
   * into its marching boundary without changing identity, geometry, or what
   * the mark is joined to — the aperture is the observer's, not the world's,
   * which is why it takes the fill and leaves everything else where it was.
   * The other two treatments stay so the lab can still put them side by side.
   */
  selectionTreatment?: SelectionTreatment;
  /**
   * Whether a selected mark spreads its strokes so their names can be read.
   *
   * Offered rather than assumed, because it is the one thing on this canvas
   * that draws a filament somewhere other than between its two ends. What is
   * joined to what does not change — only the angle a stroke leaves the held
   * mark on, and the far end never moves; see `spread.ts`. A reader who would
   * rather trust the straight line can say so.
   */
  spreadOnSelect?: boolean;
  /**
   * The light field's tuning, for a surface that exists to tune it.
   *
   * Defaults to the kernel's. Two numbers — how far light reaches, and how
   * much of the world remains readable where it does not.
   */
  light?: Partial<LightField>;
  /** World identity for the camera store; null until the overview lands. */
  world?: string | null;
  revision?: number | null;
  onHover: (id: string | null) => void;
  onSelect: (selection: CanvasSelection) => void;
  onPositions: (
    positions: Map<string, { x: number; y: number }>,
    droppedId?: string,
  ) => void;
  /**
   * A right-button press landed on a mark: take it off the field, at once.
   *
   * Removal begins on the hold, not the release — a tap, a click and a long
   * hold all remove, because the press is the decision and there is nothing
   * to stage for. The collapse plays from the set change; the release after
   * it has nothing further to do.
   */
  onRemove: (selection: NonNullable<CanvasSelection>) => void;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<Graph | null>(null);
  const motionRef = useRef(motion);
  motionRef.current = motion;
  const lifecycleMotion = useMemo(
    () => ({
      birth: scaleMotionPlan(
        NODE_BIRTH_PLAN,
        DEFAULT_MOTION_PLANS.emit.durationMs / motion.emit.durationMs,
      ),
      collapse: scaleMotionPlan(
        NODE_COLLAPSE_PLAN,
        DEFAULT_MOTION_PLANS.absorb.durationMs / motion.absorb.durationMs,
      ),
    }),
    [motion],
  );
  const lifecycleMotionRef = useRef(lifecycleMotion);
  lifecycleMotionRef.current = lifecycleMotion;
  const materialTuning = useMemo<MaterialTuning>(
    () => ({ ...MATERIAL_DEFAULTS, ...material }),
    [material],
  );
  const materialRef = useRef(materialTuning);
  materialRef.current = materialTuning;
  const contactRef = useRef<ContactState>(IDLE_CONTACT);
  const [contact, setContact] = useState<ContactState>(IDLE_CONTACT);
  const pointerOwnsLoad = contactOwnsPointer(contact.phase);
  const litHover = pointerOwnsLoad ? null : hovered;
  const litSelection = pointerOwnsLoad ? null : selection;
  /**
   * The two marks a name may be stationed from, which a press does not change.
   *
   * `litHover` and `litSelection` are the *lit* subjects: taking hold of a mark
   * puts the light out across the field, because a body under load is
   * node-local and relighting its neighbourhood while someone moves it is
   * motion nobody caused. That rule is about light, and a station is not light.
   *
   * Read off the lit subject, taking hold of a mark withdrew the very subject
   * its own names were stationed from, every incident label lost its end, and
   * the names slid to the midpoint of their filaments for exactly as long as
   * the pointer was down, then snapped back on release.
   *
   * So the station keeps the ungated subjects. Nothing about what is *lit*
   * changes here: `litHover` and `litSelection` still stand down under load,
   * and still decide light and naming. This is only where a name stands, and
   * a name must not move because a mark is being moved.
   */
  const frozenSubjects = useRef<StationSubjects>({
    hovered: null,
    selected: null,
  });
  const stationSubjects = useMemo<StationSubjects>(() => {
    /**
     * Taking hold of a mark freezes who the names are stationed from.
     *
     * Not nulls — that was the first attempt, and withdrawing the subjects
     * withdrew the ends too, so every incident name lost its station for
     * exactly as long as the pointer was down. Frozen: the subjects keep the
     * last values they had before the press, so a station provably cannot
     * change while a mark is held, whatever the pointer wanders over on its
     * way. Moving a mark is not an instruction to restation anything.
     */
    if (pointerOwnsLoad) return frozenSubjects.current;
    const next = { hovered, selected: selection?.id ?? null };
    frozenSubjects.current = next;
    return next;
  }, [hovered, selection, pointerOwnsLoad]);
  /**
   * The one group the person has opened, if any.
   *
   * Held rather than derived because it is a thing someone did, not a thing the
   * pointer is currently doing: it survives the pointer moving off the count
   * and onto the claims the count just revealed. It ends when the group stops
   * being looked at at all, which is the only exit a person would predict.
   */
  const [openedBundle, setOpenedBundle] = useState<string | null>(null);
  const openedBundleRef = useRef<string | null>(null);
  openedBundleRef.current = openedBundle;
  /**
   * The pose each parallel group was last drawn in, for the drag path.
   *
   * A drag restations plates without a draw, so it needs what the draw decided
   * — which plates are showing and which carries the count — while recomputing
   * the geometry the movement changed.
   */
  const groupPosesRef = useRef<
    ReadonlyMap<
      string,
      {
        bundleId: string | null;
        shown: string[];
        bundleSteps: number;
      }
    >
  >(new Map());
  /** Pending hover stand-down: leaving a disc is a reach before it is an exit. */
  const hoverStandDown = useRef<number | undefined>(undefined);
  const insetsRef = useRef(insets);
  insetsRef.current = insets;
  const [stageSize, setStageSize] = useState({ width: 0, height: 0 });
  /** Marks on the field last time we drew, so growth can be noticed. */
  const drawnRef = useRef(0);
  const drawnFieldIds = useRef(new Set([
    ...set.referents.keys(), ...set.assertions.keys(), ...set.demands.keys(),
  ]));
  /**
   * G6 has one mutable scene, so it also gets one reconciliation lane.
   *
   * Selection, naming and expansion can all change React data while an
   * animated draw is in flight. Keeping only the newest waiting frame avoids
   * drawing stale intermediate states, while the promise lane prevents two
   * calls from mutating the same scene concurrently. A frame received during
   * a drag waits here instead of being discarded.
   */
  const pendingFrameRef = useRef<CanvasFrame | null>(null);
  /**
   * The frame this canvas last put on the field.
   *
   * The baseline a restyle diffs against, and deliberately not
   * `graph.getNodeData()`: the store is the renderer's copy, carrying the
   * renderer's own bookkeeping, so a frame compared against it looks like it
   * has dropped keys it never wrote.
   */
  const authoredRef = useRef<CanvasData | null>(null);
  /**
   * What the visibility pass remembers per label.
   *
   * The strength it settled on last, and the authored base it multiplies —
   * the builder's own `labelFillOpacity`, recorded at build time, because a
   * base re-derived from a value the pass already dimmed would compound the
   * whisper every frame. The builder stamps `base × strength` onto each new
   * frame so a transition paints strengths directly instead of flashing full
   * and yielding after; the pass owns everything between draws.
   */
  const labelStrengthsRef = useRef(new Map<string, { strength: number; base: number }>());
  /**
   * Who the names are ranked from, for passes that run outside a render.
   *
   * The pass runs after the pump draws and under the fan — neither is a
   * render — so it reads the lit subjects through here rather than closing
   * over them. Mirrored below, beside `namedMarks`.
   */
  const visibilitySubjectsRef = useRef<{
    hover: string | null;
    selection: string | null;
    named: Set<string> | null;
  }>({ hover: null, selection: null, named: null });
  /** The arrangement this canvas has already drawn. */
  const drawnArrangeToken = useRef(0);
  const drawLaneRef = useRef<Promise<void>>(Promise.resolve());
  /**
   * The current working set, for handlers registered once at mount.
   *
   * The renderer's listeners are attached when the canvas is created and never
   * again — re-registering them on every expansion is how a canvas ends up
   * firing a click five times. That means their closure is the *first* render's,
   * where the field is empty, so asking `set.assertions.has(id)` inside one
   * always answered no and every chip click was routed as a referent. Read
   * through a ref instead, which is the only part of the state a handler needs
   * to be current about.
   */
  const setRef = useRef(set);
  setRef.current = set;
  const paramsRef = useRef(params);
  paramsRef.current = params;
  /**
   * The station each filament resolved to on the frame that drew it.
   *
   * Held rather than recomputed by the drag path, because the two lanes
   * answering the same question separately is what let a drag disagree with
   * the draw it started from. The draw decides; the drag reads.
   */
  const stationsRef = useRef<ReadonlyMap<string, Station>>(new Map());
  /**
   * The role names each bond clears, by assertion.
   *
   * `roleEnds` builds a fresh object every call, and the restyle lane
   * compares style values by identity — so an uncached call would read as
   * changed on every frame and re-render every bond's roles on every hover.
   * The names depend on the set, the paint, and the params, so the cache
   * lives exactly as long as all three stand still.
   */
  const roleEndsCacheRef = useRef(new Map<string, RoleEnds>());
  const roleEndsScopeRef = useRef<{
    set: WorkingSet;
    paint: Paint;
    params: MarkParams;
  } | null>(null);
  const onHoverRef = useRef(onHover);
  const onSelectRef = useRef(onSelect);
  const onRemoveRef = useRef(onRemove);
  onHoverRef.current = onHover;
  onSelectRef.current = onSelect;
  onRemoveRef.current = onRemove;
  /**
   * Positions the renderer currently has, including a drag in flight.
   *
   * Hover rebuilds the element data (to name a bond) and used to read
   * `set.positions`, which is a render behind the pointer. That is the snap
   * back. This map is written on every drag tick so a redraw mid-gesture keeps
   * the mark under the hand.
   */
  const liveRef = useRef(new Map(set.positions));
  /**
   * Which stored map the live cache was last taken from.
   *
   * The cache is a *copy*, and this is what says when to take a new one. It
   * used to be the stored map itself, aliased — and `followFurniture`, which
   * writes the pointer's position on every drag tick, therefore wrote drag
   * positions straight into the working set. That is the renderer editing the
   * model behind the store's back: no `onPositions`, no new map, so nothing
   * downstream could see it had happened, and any code that compared the set
   * against its own previous positions was comparing a map with itself.
   */
  const liveSourceRef = useRef(set.positions);
  /**
   * What each filament last measured from — see `StationMemory`.
   *
   * A ref because it is not a rendered quantity: nothing reads it to draw. It
   * answers one question, asked only while the pointer is on a name.
   */
  const stationMemory = useRef<StationMemory>(new Map());
  /**
   * This room's camera, kept level with the store — see `cameraMemory`. Null
   * until the world identity lands; the draw lane and listeners below read it
   * through the ref so they never hold a stale recorder.
   */
  const recorder = useMemo(
    () =>
      world != null && revision != null
        ? createCameraRecorder("field", world, revision)
        : null,
    [world, revision],
  );
  const recorderRef = useRef<CameraRecorder | null>(null);
  recorderRef.current = recorder;
  useEffect(() => () => recorder?.dispose(), [recorder]);
  const holdCamera = useCallback(
    () => recorderRef.current?.hold() ?? (() => {}),
    [],
  );
  const draggingRef = useRef(false);
  const spreadFieldRef = useRef<SpreadField | null>(null);
  const spreadOnSelectRef = useRef(spreadOnSelect);
  spreadOnSelectRef.current = spreadOnSelect;
  /**
   * The node that owns the current fan. It can differ from `selection` when a
   * person picks one of the binary labels revealed by that fan on the canvas:
   * the label is the selected assertion, but the node is still what keeps
   * the fan open. Travel — a roster row, a table row, the finder — takes
   * ownership itself instead: arriving somewhere new must not leave the old
   * mark's fan bent behind it.
   */
  const spreadOwnerRef = useRef<string | null>(null);
  /**
   * The mark the canvas itself just picked, consumed by the selection effect
   * below. A canvas label pick keeps the fan that revealed it, so the name
   * stays put under its own outline and the pointer that just landed on it;
   * anything that reaches the selection without passing through here is
   * travel, and travel closes what it leaves. Set beside the two pick sites
   * and nowhere else, cleared on every consume, so it can never go stale.
   */
  const labelPickRef = useRef<string | null>(null);
  /**
   * The selection the fan was last settled for. A re-run with the same key —
   * a lab-switch flip, StrictMode's second pass, a re-select of what is
   * already selected — re-asserts the standing owner instead of re-deciding
   * it, so the fan never moves for a selection that did not.
   */
  const settledFanRef = useRef<string | null>(null);
  /**
   * Whether a press has put the fan down. Only the press ending picks it back
   * up; until then nothing else may re-open it — not the draw a press's own
   * hover change triggers, which re-committed the fan under the hand.
   */
  const spreadSuspendedRef = useRef(false);
  /** Whether the renderer exists yet, so the ants can be handed a live graph. */
  const [ready, setReady] = useState(false);
  const paint = useMemo(() => paintOf(GRAPH_DNA_THEME[mode], mode === "dark"), [mode]);
  const tuning = useMemo<AntTuning>(
    () => ({ ...ANT_DEFAULTS, ...ants }),
    [ants],
  );
  const provisional = useMemo(
    () => paintOf(GRAPH_DNA_PROVISIONAL_THEME[mode], mode === "dark"),
    [mode],
  );

  /**
   * The light on the field.
   *
   * One source — what the pointer is on, or failing that what is selected —
   * and `luminance` falls off from it through the graph. Hover outranks
   * selection because the pointer is the more recent act, and light follows
   * acts.
   *
   * With nothing acted on there is no source, every mark is at 1, and the law
   * changes nothing. That is deliberate: this is a lamp, not a vignette.
   */
  const lightField = useMemo(
    () => ({ ...DEFAULT_LIGHT_FIELD, ...light }),
    [light],
  );

  /**
   * Graph distance from whatever a person is acting on.
   *
   * Hover outranks selection because the pointer is the more recent act. With
   * nothing acted on there is no source and the two things below — naming and
   * light — both stand down, which is the resting state of the field.
   */
  const hops = useMemo(() => {
    const source = litHover ?? (litSelection ? litSelection.id : null);
    return source ? hopsFrom(set, source) : null;
  }, [litHover, litSelection, set]);

  /**
   * How much light reaches an element.
   *
   * Furniture takes the light of the chip it hangs off, and a spoke the light
   * of the plate it belongs to — otherwise the rule under a derived plate
   * lifts out of step with the plate it is part of.
   */
  const incident = useMemo(() => {
    if (!hops) return null;
    return (elementId: string) => {
      const mark = markOfElement(elementId);
      return lift(hops.has(mark) ? (hops.get(mark) as number) : null, lightField);
    };
  }, [hops, lightField]);

  /**
   * Which marks name themselves: the one you touched, and what it is joined to.
   *
   * A plain hop count, not a light threshold. Reading naming off the light
   * made retuning the falloff silently change which labels appear, and they
   * are different questions — see `NAMING_HOPS`.
   */
  const namedMarks = useMemo(() => {
    const sources = [litHover, litSelection?.id].filter(
      (source, index, all): source is string =>
        Boolean(source) && all.indexOf(source) === index,
    );
    if (!sources.length) return null;

    const activeSource = litHover ?? (litSelection ? litSelection.id : null);
    const named = new Set<string>();
    for (const source of sources) {
      const distances = source === activeSource ? hops : hopsFrom(set, source);
      if (!distances) continue;
      for (const [mark, distance] of distances) {
        if (distance <= NAMING_HOPS) named.add(mark);
      }
    }
    /**
     * Parallel claims on one filament name each other. Hovering one plate
     * used to unname its neighbour (two hops via the disc), which collapsed
     * the stack and sent the remaining plate onto the line — the jump that
     * read as "back to centre".
     */
    for (const source of sources) {
      const origin = set.bonds.find((bond) => bond.assertion_id === source);
      if (!origin) continue;
      for (const bond of set.bonds) {
        const same =
          (bond.source === origin.source && bond.target === origin.target) ||
          (bond.source === origin.target && bond.target === origin.source);
        if (same) named.add(bond.assertion_id);
      }
    }
    return named;
  }, [hops, litHover, litSelection, set]);
  visibilitySubjectsRef.current = {
    hover: litHover,
    selection: litSelection?.id ?? null,
    named: namedMarks,
  };

  /**
   * What the ants trace: the geometry the selected mark already has.
   *
   * Nothing is traced around a mark a filter is hiding — the ants are a mark's
   * outline, and an outline with nothing inside it is a claim that something is
   * there. Selection survives the filter; only its drawing does not.
   */
  const antTarget = useMemo<AntTarget | null>(() => {
    if (!selection) return null;
    const id = selection.id;
    if (set.referents.has(id)) {
      return {
        shape: "circle",
        id,
        diameter: params.discDiameter,
        ...(selectionTreatment === "outer-field" ? {} : { clearance: 0 }),
      };
    }
    const assertion = set.assertions.get(id);
    if (assertion) {
      return assertionShown(assertion.origins ?? assertion.origin, assertion.mode, show)
        ? { shape: "rect", id }
        : null;
    }
    // An obligation's plate is the one that is dotted already, so its ants take
    // over the pattern rather than morphing into it.
    if (set.demands.has(id)) {
      return show.unresolved ? { shape: "rect", id, dotted: true } : null;
    }
    const bond = set.bonds.find((edge) => edge.assertion_id === id);
    if (bond && assertionShown(bond.origins ?? bond.origin, bond.mode, show)) {
      return {
        shape: "edge-label",
        id: bondElementId(id),
        text: bond.relation,
      };
    }
    return null;
  }, [params.discDiameter, selection, selectionTreatment, set, show]);

  /**
   * Whether the ants' mark left the field with the selection, so the leave
   * can stand down at once instead of handing a border back to a stroke that
   * is never redrawn. Element ids arrive namespaced — a bond's plate most of
   * all — so they go through the same mapping a click does.
   */
  const antsGone = useCallback(
    (id: string): boolean => {
      const mark = markOfElement(id);
      return !(
        set.referents.has(mark) ||
        set.assertions.has(mark) ||
        set.demands.has(mark) ||
        set.bonds.some((bond) => bond.assertion_id === mark)
      );
    },
    [set],
  );

  const selectionArrivalDelay = useMemo(() => {
    const graph = graphRef.current;
    if (!ready || !selection || !graph || graph.destroyed) return 0;
    return resolveFocusId(graph, selection.id) ? 0 : NODE_BIRTH_PLAN.durationMs;
  }, [ready, selection]);

  /**
   * The live cache adopts stored positions the moment they change.
   *
   * During render, not in an effect, because `data` is built through `liveAt`
   * in this same render: an effect would leave one frame drawn from the
   * positions before the change. That never showed while placement only ever
   * *added* marks — a mark that has just arrived is not in the cache, so the
   * cache had nothing stale to say about it — but an arrangement moves marks
   * that are in it, and a cache of where the renderer last put something
   * cannot be allowed to outrank a person saying where it now goes.
   *
   * A drag is the exception it has always been: the cache is then ahead of the
   * store rather than behind it, and holds the only copy of where the pointer
   * has taken the mark.
   *
   * Adopting means copying, and only when the store hands over a map it has
   * not handed over before. Copying is what keeps drag ticks out of the model;
   * the identity guard is what keeps the frames between release and the
   * store's acknowledgement from throwing away what `harvest` just read back.
   */
  if (!draggingRef.current && liveSourceRef.current !== set.positions) {
    liveSourceRef.current = set.positions;
    liveRef.current = new Map(set.positions);
  }

  const data = useMemo(() => {
    const nodes: unknown[] = [];
    const edges: unknown[] = [];
    const paintFor = (_id: string, overlay = false) =>
      overlay ? provisional : paint;
    const roleScope = roleEndsScopeRef.current;
    if (
      !roleScope ||
      roleScope.set !== set ||
      roleScope.paint !== paint ||
      roleScope.params !== params
    ) {
      roleEndsScopeRef.current = { set, paint, params };
      roleEndsCacheRef.current.clear();
    }
    /**
     * The role names a bond clears — every bond, selected or not.
     *
     * The plate stands clear of its ends' names whether they are showing, so
     * selecting a bond fades names in at room already kept for them instead
     * of shoving the plate along the line. Cached: the builder hands back a
     * fresh object every call, and the restyle lane reads a fresh identity
     * as a change.
     */
    const rolesFor = (bond: FieldBond, bondPaint: Paint): RoleEnds => {
      const cached = roleEndsCacheRef.current.get(bond.assertion_id);
      if (cached) return cached;
      const built = roleEnds(
        {
          source: bond.spokes.find((spoke) => spoke.id === bond.source)?.role ?? null,
          target: bond.spokes.find((spoke) => spoke.id === bond.target)?.role ?? null,
        },
        bondPaint,
        params,
      );
      roleEndsCacheRef.current.set(bond.assertion_id, built);
      return built;
    };
    const named = (id: string) => Boolean(namedMarks?.has(id));
    /**
     * Stations, not light — see `stationSubjects` above. A frame authored
     * while a mark is held has to agree with what the drag path is writing
     * directly, or the first draw after a release moves every name twice.
     *
     * Every station this frame resolves is recorded, and the drag path reads
     * the record rather than resolving again. One answer per filament, decided
     * once, in the lane that is drawing it.
     */
    const stations = new Map<string, Station>();
    const selectedReferent =
      selection?.kind === "referent" ? selection.id : null;
    /** The two ends of whatever plate the pointer is on, if it is on one. */
    const endsOfPlate = (assertionId: string) => {
      const parallel = set.bonds.find(
        (bond) => bond.assertion_id === assertionId,
      );
      if (parallel) return { source: parallel.source, target: parallel.target };
      const subject = subjectOfBundle(assertionId);
      if (!subject) return null;
      const counted = set.bonds.find((bond) => bond.assertion_id === subject);
      return counted ? { source: counted.source, target: counted.target } : null;
    };
    const stationOfBond = (bond: FieldBond): Station => {
      const near = bondStation(
        bond,
        stationSubjects,
        stationMemory.current,
        bond.assertion_id,
        endsOfPlate,
        defaultStation(bond),
      );
      stations.set(bondElementId(bond.assertion_id), near);
      return near;
    };
    const stationOfSpoke = (
      elementId: string,
      referentId: string,
      plateId: string,
    ): Station => {
      const near = spokeStation(
        { source: referentId, target: plateId },
        stationSubjects,
        stationMemory.current,
        elementId,
      );
      stations.set(elementId, near);
      return near;
    };
    const at = (id: string, fallback: { x: number; y: number } = { x: 0, y: 0 }) =>
      liveAt(liveRef.current, set.positions, id, fallback);
    const visibleBonds = set.bonds.filter(
      (bond) =>
        set.referents.has(bond.source) &&
        set.referents.has(bond.target) &&
        assertionShown(bond.origins ?? bond.origin, bond.mode, show),
    );
    /**
     * One stroke per pair of ends. Several claims between the same two
     * referents are still one filament — two wires would invent a geometry
     * the tuples do not have. The plates of those claims share the 44px
     * station and step along the filament's normal so each stays selectable.
     */
    const byEndpoints = new Map<string, typeof visibleBonds>();
    for (const bond of visibleBonds) {
      const key = [bond.source, bond.target].sort().join("\u0000");
      const group = byEndpoints.get(key) ?? [];
      group.push(bond);
      byEndpoints.set(key, group);
    }
    const stackByAssertion = new Map<string, { x: number; y: number }>();
    /**
     * One station for a shared filament, by member assertion.
     *
     * Siblings resolving separately could split ends or stand at different
     * distances out — a ragged stack whose members answered the same question
     * differently, with the selected one jutting out to clear names only it
     * shows. The group resolves once, off its first member, and the distance
     * is the widest any member needs, roles included.
     */
    const groupLayoutByAssertion = new Map<
      string,
      {
        near: Station;
        station: number;
        half: number;
      }
    >();
    /**
     * One stroke per pair of ends, on the layer below every plate — see
     * `bondFilament` and `PAINT_LAYER_STROKE`. Collected here, prepended at
     * the return, so the born order stays strokes-first within the layer;
     * the layering itself is what keeps a later stroke off an earlier name.
     */
    const filaments: {
      id: string;
      source: string;
      target: string;
      paint: Paint;
      /** Present on a spoke's stroke, which dots like its obligation. */
      spoke?: { dotted: boolean };
    }[] = [];
    /** Grouped claims are named by their group, not one at a time. */
    const namedBond = new Map<string, boolean>();
    /** Per endpoint-pair, the pose the drawn frame settled on. See below. */
    const groupPoses = new Map<
      string,
      {
        bundleId: string | null;
        shown: string[];
        bundleSteps: number;
      }
    >();
    const bundles: {
      id: string;
      source: string;
      target: string;
      label: string;
      shown: boolean;
      interactive: boolean;
      stack: { x: number; y: number };
      near: Station;
      station: number;
      half: number;
    }[] = [];
    for (const unsorted of byEndpoints.values()) {
      const group = [...unsorted].sort((a, b) =>
        `${a.relation}\u0000${a.assertion_id}`.localeCompare(
          `${b.relation}\u0000${b.assertion_id}`,
        ),
      );
      if (group[0]) {
        const first = group[0];
        filaments.push({
          id: `filament:${first.assertion_id}`,
          source: first.source,
          target: first.target,
          paint: paintFor(
            first.assertion_id,
            unsettled(first.stale, first.completeness),
          ),
        });
      }
      /**
       * Three states, not two, and selection is what crosses the second.
       *
       * At rest a filament says nothing. Named — an endpoint hovered, or a
       * mark two hops off selected — a group says how many claims it carries,
       * because a single line standing for three of them is a lie by omission.
       * Opened, it says what they are.
       *
       * **Selecting an endpoint opens every group on it.** Selection already
       * means "this mark is what I am working on", and a mark cannot be what
       * you are working on while three of the claims it makes are still folded
       * behind a number. The count was never a thing anyone wanted to click;
       * it was a toll on the way to the claims. So the act that opens a group
       * is the act you were going to perform anyway, and the count survives
       * only for groups you have *not* selected into — a marker for where you
       * have not looked yet, rather than a control.
       *
       * A count that does survive is opened by clicking it. Under hover it
       * opened on the way past, and closed while you were reaching for what it
       * had revealed.
       */
      const first = group[0];
      const grouped = group.length > 1 && Boolean(first);
      // No fit test here: every intended name is laid out, and where boxes
      // overlap the visibility pass dims the loser instead of hiding it — see
      // `visibility.ts`. There is nothing to hold a seat against.
      if (grouped && first) {
        const near = stationOfBond(first);
        let station = BOND_LABEL_ALONG_PX;
        let half = 0;
        for (const bond of group) {
          const overlay = unsettled(bond.stale, bond.completeness);
          station = Math.max(
            station,
            bondPlateAlong(
              bond.relation,
              rolesFor(bond, paintFor(bond.assertion_id, overlay)),
              params,
            ),
          );
          half = Math.max(half, chipWidth(bond.relation, params) / 2);
        }
        for (const bond of group) {
          // The filament's memory, not each member's own.
          stationMemory.current.set(bond.assertion_id, near);
          stations.set(bondElementId(bond.assertion_id), near);
          groupLayoutByAssertion.set(bond.assertion_id, { near, station, half });
        }
      } else if (first) {
        // Alone on its filament, a bond is still laid out here: one record
        // per filament, decided once, whether it carries one name or several.
        // Its seat is trivially the station, so its fit settles now.
        const bond = first;
        const near = stationOfBond(bond);
        const overlay = unsettled(bond.stale, bond.completeness);
        const station = Math.max(
          BOND_LABEL_ALONG_PX,
          bondPlateAlong(
            bond.relation,
            rolesFor(bond, paintFor(bond.assertion_id, overlay)),
            params,
          ),
        );
        const half = chipWidth(bond.relation, params) / 2;
        groupLayoutByAssertion.set(bond.assertion_id, { near, station, half });
      }
      const isOpenBundle =
        first !== undefined && openedBundle === bundleElementId(first.assertion_id);
      /** The group hangs off the mark a person has chosen to work on. */
      const onSelectedMark =
        selectedReferent !== null &&
        first !== undefined &&
        (first.source === selectedReferent || first.target === selectedReferent);
      /**
       * An opened group names itself.
       *
       * Naming and light are different questions — `NAMING_HOPS` exists
       * because reading one off the other made retuning the falloff silently
       * change which labels appear — and this is the case that proves it. The
       * pointer reaching a count has left the disc, so no light falls here any
       * more; what the person is looking at is nonetheless this group.
       */
      const groupNamed =
        group.some((bond) => named(bond.assertion_id)) || isOpenBundle;
      /**
       * A selected claim holds its group open; hover can open one too but
       * never closes what selection opened, or the selected plate folds away
       * under its own outline as the pointer passes any other mark.
       */
      const selectedBond =
        group.find((bond) => bond.assertion_id === selection?.id) ?? null;
      const opened =
        !grouped ||
        isOpenBundle ||
        onSelectedMark ||
        selectedBond !== null ||
        (litHover !== null &&
          group.some((bond) => bond.assertion_id === litHover));
      /**
       * The selected claim is always one of the plates drawn. Past the cap it
       * takes the last seat, so a claim chosen from a table or roster is never
       * outlined on a plate the stack is not showing.
       */
      const capped = group.slice(0, BOND_LABEL_STACK_MAX);
      const seated =
        selectedBond && !capped.includes(selectedBond)
          ? [...capped.slice(0, -1), selectedBond]
          : capped;
      const shown = grouped && opened ? seated : group;
      // How far apart two plates on one filament stand: `bondLabelStep`.
      const step = bondLabelStep(params);
      // The stack centres on what is actually drawn, so a capped group is not
      // pushed off its own filament by the plates it is not showing.
      const middle = (shown.length - 1) / 2;
      const stepped = (count: number) => ({
        x: step.x * count,
        y: step.y * count,
      });
      group.forEach((bond) =>
        stackByAssertion.set(bond.assertion_id, { x: 0, y: 0 }),
      );
      shown.forEach((bond, index) => {
        stackByAssertion.set(bond.assertion_id, stepped(index - middle));
      });
      for (const bond of group) {
        namedBond.set(
          bond.assertion_id,
          grouped
            ? groupNamed && opened && shown.includes(bond)
            : named(bond.assertion_id),
        );
      }
      /**
       * What the drag path needs to restate this group, and could not derive.
       *
       * Which plates a group is showing, and which one of them carries the
       * count, follow from naming and from whether a person opened it — none
       * of which a drag changes and none of which the drag path can see. The
       * geometry it *must* recompute, because the filament's normal turns as
       * the mark moves. Recording the pose here and the geometry there is what
       * keeps the resting stack and the dragged stack the same stack.
       */
      groupPoses.set(
        [group[0]?.source ?? "", group[0]?.target ?? ""].sort().join("\u0000"),
        {
          bundleId: grouped && first ? bundleElementId(first.assertion_id) : null,
          shown: shown.map((bond) => bond.assertion_id),
          // In steps, not pixels: how wide a step is belongs to `marks.ts`,
          // and both lanes have to be reading the same one.
          bundleSteps: opened ? shown.length - (shown.length - 1) / 2 : 0,
        },
      );
      if (grouped && first) {
        // Past the cap the stack is not showing the claim, and the count is
        // what says so.
        const remainder = group.filter(
          (bond) => !shown.includes(bond),
        ).length;
        const bundleNear = stationOfBond(first);
        const label = opened
          ? `+${remainder} more`
          : `${group.length} assertions`;
        const stack =
          opened ? stepped(shown.length - middle) : { x: 0, y: 0 };

        bundles.push({
          id: bundleElementId(first.assertion_id),
          source: first.source,
          target: first.target,
          // Opened, the count stops being a stand-in and becomes the one thing
          // the stack cannot say for itself: that it is not all of them.
          label,
          shown: groupNamed && (!opened || remainder > 0),
          // Reachable whenever it is legible. Requiring a selection meant a
          // count that had appeared under the pointer, said how many claims it
          // stood for, and then would not answer being pointed at.
          interactive: !opened && groupNamed,
          stack,
          // The count stands where its claims stand, which means it asks the
          // same filament the same question rather than a global one.
          near: bundleNear,
          // The count stands where its claims stand: same station, so the two
          // halves of the fade happen in one place — but its own width, so a
          // short count is not pushed out by the claims it stands in for.
          station:
            groupLayoutByAssertion.get(first.assertion_id)?.station ??
            BOND_LABEL_ALONG_PX,
          half: chipWidth(label, params) / 2,
        });
        stations.set(bundleElementId(first.assertion_id), bundleNear);
      }
    }

    for (const referent of set.referents.values()) {
      const stored = at(referent.id);
      const node = discNode(
        referent.id,
        stored.x,
        stored.y,
        referent.label,
        paintFor(referent.id),
        params,
      );
      /**
       * Observer aperture. Selection withdraws the disc's optical fill into
       * its marching boundary without changing identity, geometry or incident
       * constraints. Returning to rest condenses the authored fill again.
       */
      if (
        selectionTreatment === "hollow" &&
        selection?.kind === "referent" &&
        selection.id === referent.id
      ) {
        node.style.fill = paint.canvas;
        node.style.fillOpacity = 1;
        node.style.labelFill = paint.ink;
      }
      nodes.push(node);
    }

    for (const assertion of set.assertions.values()) {
      if (!assertionShown(assertion.origins ?? assertion.origin, assertion.mode, show)) continue;
      const atChip = at(assertion.assertion_id);
      const overlay = unsettled(assertion.stale, assertion.completeness);
      const kind = chipKindOf(assertion.origins ?? assertion.origin);
      const chipPaint = paintFor(assertion.assertion_id, overlay);
      const chip = chipNode(
        assertion.assertion_id,
        atChip.x,
        atChip.y,
        assertion.relation,
        kind,
        chipPaint,
        params,
      );
      if (
        selectionTreatment === "hollow" &&
        selection?.id === assertion.assertion_id &&
        chip.style.fillOpacity > 0
      ) {
        chip.style.fill = chipPaint.canvas;
        chip.style.fillOpacity = 1;
        chip.style.labelFill = chipPaint.ink;
      }
      nodes.push(chip);
      // A shelf beneath says the assertion rests on other relations; a crown
      // above says a person put it there. Both can be true of one chip — a
      // human verdict is still maintained by whatever derives from it — so
      // these are independent tests rather than a chain.
      //
      // Both withdraw with a hollowed plate: the one above just opened into
      // its marching boundary, and a rule left standing beside an opened
      // plate is the fill refusing to have gone. The restyle lane fades the
      // withdrawal rather than cutting it — see `restyleCanvasData`.
      const furnitureOpacity =
        selectionTreatment === "hollow" &&
        selection?.id === assertion.assertion_id
          ? 0
          : 1;
      if (assertion.mode === "DERIVED") {
        nodes.push(
          shelfNode(
            `shelf:${assertion.assertion_id}`,
            atChip.x,
            atChip.y,
            assertion.relation,
            chipPaint,
            params,
            "under",
            furnitureOpacity,
          ),
        );
      }
      if (kind === "adjudicated") {
        nodes.push(
          shelfNode(
            `crown:${assertion.assertion_id}`,
            atChip.x,
            atChip.y,
            assertion.relation,
            chipPaint,
            params,
            "over",
            furnitureOpacity,
          ),
        );
      }
      assertion.spokes.forEach((spoke, index) => {
        if (!set.referents.has(spoke.id)) return;
        const near = stationOfSpoke(
          `${assertion.assertion_id}:${index}`,
          spoke.id,
          assertion.assertion_id,
        );
        filaments.push({
          id: `filament:${assertion.assertion_id}:${index}`,
          source: spoke.id,
          target: assertion.assertion_id,
          paint: paintFor(assertion.assertion_id, overlay),
          spoke: { dotted: false },
        });
        // Half the role's own plate, and the air it may spend to keep
        // clear of the disc — past the middle if the name is wide
        // enough to need it. See `spokeLabelStation`.
        const { halfPlate, air } = spokeLabelStation(spoke.role, params);
        const layout = bondLabelLayout(
          at(spoke.id),
          at(assertion.assertion_id),
          near,
          { x: 0, y: 0 },
          params,
          discRim(params),
          plateRim(assertion.relation, params),
          SPOKE_LABEL_ALONG_PX,
          halfPlate,
          air,
        );
        edges.push(
          spokeEdge(
            `${assertion.assertion_id}:${index}`,
            spoke.id,
            assertion.assertion_id,
            paintFor(assertion.assertion_id, overlay),
            params,
            {
              role: spoke.role,
              showRole: named(assertion.assertion_id),
              labelPlacement: layout.placement,
              bondAlong: layout.along,
            },
          ),
        );
      });
    }

    // §8.7 and §9: an obligation is a hollow, dotted chip with dotted spokes —
    // present enough to be found, unfilled because nothing has filled it. It is
    // never drawn as a bond, at any arity: a line between two discs is a claim
    // that they are joined, and the point of this mark is that no such claim
    // has been made.
    for (const demand of set.demands.values()) {
      if (!show.unresolved) continue;
      const atDemand = at(demand.key);
      nodes.push(
        chipNode(
          demand.key,
          atDemand.x,
          atDemand.y,
          demand.relation,
          "unresolved",
          paintFor(demand.key),
          params,
        ),
      );
      demand.spokes.forEach((spoke, index) => {
        if (!set.referents.has(spoke.id)) return;
        const near = stationOfSpoke(
          `${demand.key}:${index}`,
          spoke.id,
          demand.key,
        );
        filaments.push({
          id: `filament:${demand.key}:${index}`,
          source: spoke.id,
          target: demand.key,
          paint: paintFor(demand.key),
          spoke: { dotted: true },
        });
        const { halfPlate, air } = spokeLabelStation(spoke.role, params);
        const layout = bondLabelLayout(
          at(spoke.id),
          at(demand.key),
          near,
          { x: 0, y: 0 },
          params,
          discRim(params),
          plateRim(demand.relation, params),
          SPOKE_LABEL_ALONG_PX,
          halfPlate,
          air,
        );
        edges.push(
          spokeEdge(
            `${demand.key}:${index}`,
            spoke.id,
            demand.key,
            paintFor(demand.key),
            params,
            {
              role: spoke.role,
              showRole: named(demand.key),
              labelPlacement: layout.placement,
              bondAlong: layout.along,
            },
          ),
        );
      });
    }

    for (const bond of set.bonds) {
      if (!set.referents.has(bond.source) || !set.referents.has(bond.target)) continue;
      if (!assertionShown(bond.origins ?? bond.origin, bond.mode, show)) continue;
      const overlay = unsettled(bond.stale, bond.completeness);
      // A grouped bond stands where its filament stands — see the group loop.
      // Resolving here as well would let siblings split ends again.
      const shared = groupLayoutByAssertion.get(bond.assertion_id);
      const near = shared?.near ?? stationOfBond(bond);
      const bondPaint = paintFor(bond.assertion_id, overlay);
      const roles = rolesFor(bond, bondPaint);
      const along = shared?.station ?? bondPlateAlong(bond.relation, roles, params);
      const layout = bondLabelLayout(
        at(bond.source),
        at(bond.target),
        near,
        stackByAssertion.get(bond.assertion_id) ?? { x: 0, y: 0 },
        params,
        discRim(params),
        discRim(params),
        along,
        // Half its own plate, so a long relation name stands off the rim by
        // the same air a short one does instead of overlapping the disc.
        // Grouped, the widest member's: one stack, one station.
        shared?.half ?? chipWidth(bond.relation, params) / 2,
      );
      const filament = filamentEdge(
        bondElementId(bond.assertion_id),
        bond.source,
        bond.target,
        bondPaint,
        params,
        {
          label: bond.relation,
          named: namedBond.get(bond.assertion_id) ?? named(bond.assertion_id),
          kind: chipKindOf(bond.origins ?? bond.origin),
          labelPlacement: layout.placement,
          labelOffsetX: layout.offsetX,
          labelOffsetY: layout.offsetY,
          // Shown on selection; cleared always — see `rolesFor`.
          roles: selection?.id === bond.assertion_id ? roles : null,
          bondAlong: along,
          bondHalf: shared?.half ?? chipWidth(bond.relation, params) / 2,
        },
      );
      /**
       * The aperture, on a bond's plate.
       *
       * A bond is selected the same way a disc or a chip is, and the observer
       * does the same thing to it: the plate's fill withdraws into the ants
       * already tracing its outline. Without this, selecting an authored bond
       * left the one filled rectangle on a field where everything else the
       * observer touched had opened — which read as the plate refusing to be
       * looked at rather than as a different origin.
       *
       * Origin is not lost. A knocked-out plate under a marching outline is
       * still a plate, and its fill returns the moment selection moves on.
       */
      if (
        selectionTreatment === "hollow" &&
        selection?.id === bond.assertion_id &&
        filament.style.labelBackgroundOpacity > 0
      ) {
        filament.style.labelBackgroundFill = bondPaint.canvas;
        filament.style.labelFill = bondPaint.ink;
      }
      edges.push(filament);
    }
    /**
     * The observer's count, pushed after the claims so it draws over the
     * filament it is counting rather than under it.
     *
     * It is shown exactly when the individual names are not, which is what
     * makes the pair a cross-fade rather than two independent fades: one
     * `emit` takes the count out as the same `emit` brings the claims in, and
     * at no frame is the filament either unnamed or named twice over.
     */
    for (const bundle of bundles) {
      /**
       * The count stands exactly where the claims will. Pinned to the
       * filament's geometric midpoint it was a different station from the
       * 44px one the plates use, so the two halves of the fade happened in
       * two places and read as one thing dying while others were born
       * elsewhere — on a long filament, a long way elsewhere.
       */
      const station = bondLabelLayout(
        at(bundle.source),
        at(bundle.target),
        bundle.near,
        bundle.stack,
        params,
        discRim(params),
        discRim(params),
        bundle.station,
        bundle.half,
      );
      edges.push(
        summaryEdge(bundle.id, bundle.source, bundle.target, paint, params, {
          label: bundle.label,
          shown: bundle.shown,
          interactive: bundle.interactive,
          placement: station.placement,
          offsetX: station.offsetX,
          offsetY: station.offsetY,
          bondAlong: bundle.station,
          bondHalf: bundle.half,
        }),
      );
    }
    /**
     * Light applied last, over everything the marks authored.
     *
     * Reflected rather than replaced: a filament authored quiet stays quieter
     * than the disc beside it, because illumination scales what a thing is
     * instead of overwriting it. With no source `incident` is null and this
     * loop does not run, so at rest the field draws exactly as it did before
     * there was a law.
     */
    if (incident) {
      /**
       * Each mark reflects on the channels it is made of, and never on
       * `opacity`.
       *
       * `opacity` is presence — the channel birth and absorption own, and the
       * one G6 composites into the label group. Lighting it would light the
       * names too, and a name is not lit, it is read. So a disc reflects on
       * its fill, an outlined plate on its stroke, a filament on its stroke,
       * and every one of them keeps its label at the strength it was stated
       * at. See `discNode` and `spokeEdge`.
       *
       * A channel absent from the datum is not lit into existence: a hollow
       * plate has `fillOpacity: 0` on purpose, and `reflected` leaves a zero
       * where it found one — nothing is what an obligation is made of.
       */
      const reflect = (
        mark: { id: string; style?: Record<string, unknown> },
        channels: readonly ("fillOpacity" | "strokeOpacity")[],
      ) => {
        if (!mark.style) return;
        const incidentHere = incident(mark.id);
        for (const channel of channels) {
          const albedo = mark.style[channel] as number | undefined;
          if (albedo === undefined || albedo === 0) continue;
          mark.style[channel] = reflected(albedo, incidentHere);
        }
      };
      for (const node of nodes as { id: string; style?: Record<string, unknown> }[]) {
        reflect(node, ["fillOpacity", "strokeOpacity"]);
      }
      for (const edge of edges as { id: string; style?: Record<string, unknown> }[]) {
        reflect(edge, ["strokeOpacity"]);
      }
    }
    /**
     * The selected plate hands its border to the ants.
     *
     * Two rectangles is what the ants used to draw, and dropping the standoff
     * alone would only have stacked them: a solid border with beads sitting on
     * it is still a solid border. So the plate's own stroke goes, the ants
     * arrive solid in exactly its place, and what a person sees is one border
     * that becomes dotted. It comes straight back on deselect, and it never
     * tweens — `meaningIsStructural`; the width is a fact about construction
     * origin, and a plate caught between outlined and not draws an origin that
     * does not exist.
     */
    if (antTarget && antTarget.shape === "rect") {
      const plate = (nodes as { id: string; style?: Record<string, unknown> }[]).find(
        (node) => node.id === antTarget.id,
      );
      if (plate?.style) plate.style.lineWidth = 0;
    }
    /**
     * A bond's plate opens the same way. Its box is the edge label's
     * background rect, so the withdrawal is restated in label channels: the
     * fill goes to the canvas and the name reads in ink, whatever origin
     * filled it — the marching boundary is then the plate's only border.
     */
    if (antTarget && antTarget.shape === "edge-label") {
      const edge = (
        edges as { id: string; style?: Record<string, unknown> }[]
      ).find((item) => item.id === antTarget.id);
      if (edge?.style) {
        edge.style.labelBackgroundFill = paint.canvas;
        edge.style.labelBackgroundOpacity = 1;
        edge.style.labelFill = paint.ink;
      }
    }
    groupPosesRef.current = groupPoses;
    stationsRef.current = stations;
    edges.unshift(
      ...filaments.map((stroke) =>
        stroke.spoke
          ? spokeFilament(
              stroke.id,
              stroke.source,
              stroke.target,
              stroke.paint,
              params,
              { dotted: stroke.spoke.dotted },
            )
          : bondFilament(stroke.id, stroke.source, stroke.target, stroke.paint, params),
      ),
    );
    // Strengths, stated, so a draw paints what the pass settled rather
    // than flashing full and yielding after — see `stampLabelStrength`.
    for (const datum of [...nodes, ...edges] as {
      id: string;
      style?: Record<string, unknown>;
    }[]) {
      stampLabelStrength(datum, labelStrengthsRef.current);
    }
    /**
     * Depth, stated: drops restack within the mark layer — see `restack`.
     *
     * G6 fronts the held mark for the gesture and the drop's redraw would
     * otherwise sink it back to its creation slot, behind whatever it now
     * overlaps. Ranked, not sequenced: the fractions always land strictly
     * between the mark layer and the name layer however many drops land, so
     * no normalization pass ever owes anyone a visit. Marks with no entry
     * keep the layer's own `zIndex` and paint in creation order behind every
     * restacked mark — an empty stack is exactly today's drawing.
     */
    const nodeById = new Map(
      (nodes as { id: string; style?: Record<string, unknown> }[]).map(
        (datum) => [datum.id, datum] as const,
      ),
    );
    const stackedDepths = rankedDepths(
      set.depth,
      (nodes as { id: string }[]).map((datum) => datum.id),
    );
    // Stamped verbatim: these numbers are the drops' own record, and
    // restating anything else's is the reshuffle step two killed.
    const depthPaint = paintDepths(set.depth);
    for (const { id } of stackedDepths) {
      const style = nodeById.get(id)?.style;
      const z = depthPaint.get(id);
      if (!style || z === undefined) continue;
      style.zIndex = z;
    }
    const stackedCount = stackedDepths.length;
    /**
     * Labels sink with occluded owners, and rise with rank.
     *
     * A label at the name layer paints over every mark, including one
     * stacked above the mark it names — a hidden plate impersonating the
     * disc hiding it. So a labeled edge lifts half a drop step above its
     * fronter endpoint: over its own marks, under any mark stacked above
     * them, because the next band up is always at least a step away. A
     * fixed lift, not half the band it stands in — a new top landing
     * overhead must not move it, and half the band would halve with every
     * ceiling the stack climbs toward. Past eighty-nine stacked marks the
     * dense bands narrow below a step, and the lift takes half the band
     * instead: the same floor the marks stand on. Strictly between the
     * bands by construction, and the span cap keeps the topmost label below
     * the names. Unlabeled strokes keep the stroke layer — they never
     * needed to beat a mark.
     *
     * Within the lift, rank decides: the labels sort strongest-first by the
     * same `rankOfLabel` the strength pass settles, so the brighter of two
     * overlapping names is also the one on top. Endpoint depth still
     * dominates — rank only orders labels that share a base — because a
     * bright plate over the disc hiding its endpoint would be the same
     * impersonation. With no restack every label shares the name layer as
     * its base, and rank orders the whole field instead of creation order.
     */
    const rankSubjects = visibilitySubjectsRef.current;
    const rankShare = new Map(
      (
        edges as {
          id: string;
          style?: Record<string, unknown>;
        }[]
      )
        .filter(
          (edge) =>
            typeof edge.style?.labelText === "string" && edge.style.labelText,
        )
        .map((edge) => ({
          id: edge.id,
          rank: rankOfLabel(edge.id, edge.style?.labelFontFamily, rankSubjects),
        }))
        .sort(
          (a, b) =>
            compareRanks(a.rank, b.rank) ||
            (a.id < b.id ? -1 : a.id > b.id ? 1 : 0),
        )
        .map(
          (entry, index, all) =>
            [entry.id, (all.length - index) / all.length] as const,
        ),
    );
    const markZ = new Map<string, number>();
    for (const datum of nodes as {
      id: string;
      style?: Record<string, unknown>;
    }[]) {
      const z = datum.style?.zIndex;
      markZ.set(datum.id, typeof z === "number" ? z : PAINT_LAYER_MARK);
    }
    // Half the room above the base, capped at half a drop step — the cap
    // is what keeps a new top from moving every label standing under it.
    const liftOver = (over: number): number => {
      let next = PAINT_LAYER_NAME;
      for (const z of markZ.values()) {
        if (z > over && z < next) next = z;
      }
      return Math.min(MARK_DEPTH_STEP / 2, (next - over) / 2);
    };
    for (const edge of edges as {
      id: string;
      source?: unknown;
      target?: unknown;
      style?: Record<string, unknown>;
    }[]) {
      const style = edge.style;
      if (!style) continue;
      if (typeof style.labelText !== "string" || !style.labelText) continue;
      const over = stackedCount
        ? Math.max(
            typeof edge.source === "string"
              ? (markZ.get(edge.source) ?? PAINT_LAYER_MARK)
              : PAINT_LAYER_MARK,
            typeof edge.target === "string"
              ? (markZ.get(edge.target) ?? PAINT_LAYER_MARK)
              : PAINT_LAYER_MARK,
          )
        : PAINT_LAYER_NAME;
      const lift = stackedCount ? liftOver(over) : NAME_RANK_SPAN;
      style.zIndex = over + lift * (rankShare.get(edge.id) ?? 1);
    }
    return { nodes, edges };
  }, [
    set,
    paint,
    provisional,
    params,
    antTarget,
    contact.phase,
    litHover,
    litSelection,
    // The station subjects, which outlive a press — see `stationSubjects`.
    stationSubjects,
    selection,
    selectionTreatment,
    incident,
    namedMarks,
    openedBundle,
    show,
  ]);

  /**
   * An opened group closes when the pointer leaves the group, not the label.
   *
   * The first thing the pointer does after opening a group is move onto the
   * claims it revealed, so a group that shut on the count's own `pointerleave`
   * would be a door that only stays open while you hold it. What closes it is
   * leaving the whole neighbourhood — the count, the claims it opened, or the
   * two discs they run between — and even that waits out a reach, because the
   * gaps between those things are places the pointer passes through rather
   * than places it has gone.
   *
   * This used to be read off `namedMarks`, which made the group's own light
   * the thing holding it open; a count reached from a hover went dark on the
   * way and took the answer with it.
   */
  useEffect(() => {
    if (!openedBundle) return;
    // The claim it stands for, in `bonds` — `assertions` is the plates that
    // have been placed on the field, which a grouped claim never is.
    const subject = subjectOfBundle(openedBundle);
    const held = set.bonds.some((bond) => bond.assertion_id === subject);
    if (!held) setOpenedBundle(null);
  }, [openedBundle, set]);

  /** Dragged positions belong to the person, so they are read back before use. */
  /**
   * Read the renderer's places back into the store, naming what was dropped.
   *
   * The dropped id travels with the positions so the page can restack it in
   * the same set — positions and depth land in one frame, and the drop's own
   * transition paints both. Whether the drop moved anything is the page's
   * call: it holds the stored places to compare against.
   */
  const harvest = useCallback((droppedId?: string) => {
    const graph = graphRef.current;
    if (!graph) return;
    const out = new Map<string, { x: number; y: number }>();
    for (const node of graph.getNodeData()) {
      const id = String(node.id);
      if (isDecoration(id)) continue;
      const position = graph.getElementPosition(id);
      /**
       * `getElementPosition` answers `[null, null, 0]` for an element whose
       * transform it cannot resolve, and the array itself is always truthy.
       * Rounding that gives `NaN`, and `NaN` is what then goes to the store as
       * where the person put the mark — a place nothing can draw, hit-test or
       * lay out from, kept across reloads. A position that cannot be read is
       * not a position; the stored one stands.
       */
      if (!position || !Number.isFinite(position[0]) || !Number.isFinite(position[1])) {
        continue;
      }
      out.set(id, { x: Math.round(position[0]), y: Math.round(position[1]) });
    }
    if (!out.size) return;
    liveRef.current = new Map([...liveRef.current, ...out]);
    onPositions(out, droppedId);
  }, [onPositions]);

  /**
   * Whether a drag actually moved its mark, read after `harvest`.
   *
   * The harvest has just written where the renderer put everything, and the
   * store still says where it was — the acknowledgement has not rendered yet.
   * Equal means the gesture drew nothing, so whatever the release owes the
   * field has to happen now; different means a draw is coming for it.
   */
  const dragMoved = (id: string | null): boolean => {
    if (!id) return false;
    const live = liveRef.current.get(id);
    const stored = setRef.current.positions.get(id);
    return (
      !!live && !!stored && (live.x !== stored.x || live.y !== stored.y)
    );
  };

  /**
   * Bring a frame that waited out a drag up to where the drag actually ended.
   *
   * A frame built mid-gesture — a filter toggled with the other hand, a hover
   * that changed what is lit — is held because a redraw under a pointer that
   * is down would fight the person for the mark. It carries the position the
   * mark had at the moment it was built, and the mark has moved since. Flushed
   * as-is on release it puts the mark back there, and the frame that follows
   * from `onPositions` puts it right again: a yank and a return, for a change
   * that had nothing to do with where anything is.
   *
   * Only the dragged mark and its furniture can be stale — nothing else moved
   * — so only those are restated, from the cache `harvest` has just made
   * authoritative. The frame is rebuilt rather than written through: its data
   * belongs to a memo, and a memo whose contents are edited from an event
   * handler is a memo that no longer says what it computed.
   */
  const restatePendingDrag = useCallback(
    (id: string) => {
      const frame = pendingFrameRef.current;
      const at = liveRef.current.get(id);
      if (!frame || !at) return;
      const offset = params.chipHeight / 2 + params.shelfGap;
      const furniture = new Set(furnitureOf(id));
      let restated = false;
      const nodes = frame.nodes.map((node) => {
        const crown = node.id.startsWith("crown:");
        if (node.id !== id && !furniture.has(node.id)) return node;
        const y = node.id === id ? at.y : crown ? at.y - offset : at.y + offset;
        if (node.style?.x === at.x && node.style?.y === y) return node;
        restated = true;
        return { ...node, style: { ...node.style, x: at.x, y } };
      });
      if (restated) pendingFrameRef.current = { ...frame, nodes };
    },
    [params.chipHeight, params.shelfGap],
  );

  /**
   * Which contact phases hold the lane, and why `releasing` is not one of them.
   *
   * A pointer that is down owns the field: `pressed` and `dragging` are both
   * cases where the person is still authoring, and a global redraw underneath
   * them would answer a question they have not finished asking.
   *
   * `releasing` is the opposite. The pointer is already up, the click has
   * already committed, and what is still running is one body relaxing a load
   * on its own two shapes — a transform G6 leaves alone across `setData`, so
   * nothing about a redraw disturbs it. Holding the lane through it made the
   * observer's aperture wait out the body's viscoelastic return, which are two
   * different causes with no reason to be serialized: the person acted once
   * and should see one answer, not the slower of two.
   */
  const contactHoldsLane = (phase: ContactState["phase"]) =>
    phase === "pressed" || phase === "dragging";

  /**
   * Settle which names read at full strength, off the drawing in front of
   * the reader.
   *
   * The boxes are painted ones — fans, fonts and stations already accounted
   * for — so this runs after a draw lands and under the fan (see
   * `SPREAD_FRAME_EVENT` below), never from a render. Only changed strengths
   * are written, and they go three places at once: the live text (through
   * `paintLabelStrength`, on the strength channel naming never touches), the
   * G6 store (so it keeps telling the truth), and the authored baseline (so
   * the next restyle diffs against what is actually painted rather than
   * restating yesterday's strengths as a change).
   *
   * A label whose box cannot be read keeps its last strength: an unlaid name
   * is not a lost contest. Strengths for elements that left the frame are
   * dropped, so a returning name re-contests rather than inheriting a
   * whisper from a crowd that is gone.
   */
  const applyVisibility = useCallback((graph: Graph) => {
    const frame = authoredRef.current;
    if (!frame || graph.destroyed) return;
    const remembered = labelStrengthsRef.current;
    const standing = new Set([...frame.nodes, ...frame.edges].map((datum) => datum.id));
    for (const id of [...remembered.keys()]) {
      if (!standing.has(id)) remembered.delete(id);
    }
    let settled: Map<string, number>;
    if (VISIBILITY_STRENGTHS_ON) {
      const subjects = visibilitySubjectsRef.current;
      const boxes: VisibilityBox[] = [];
      const ranks = new Map<string, VisibilityRank>();
      const depths = new Map<string, number>();
      for (const datum of [...frame.nodes, ...frame.edges]) {
        const style = datum.style as Record<string, unknown> | undefined;
        if (!style) continue;
        if (typeof style.labelText !== "string" || !style.labelText) continue;
        const shown = (style.labelOpacity as number | undefined) ?? 1;
        if (!(shown > 0)) continue;
        const box = paintedLabelBox(graph, datum.id);
        if (!box) continue;
        boxes.push({ id: datum.id, ...box });
        ranks.set(datum.id, rankOfLabel(datum.id, style.labelFontFamily, subjects));
        if (typeof style.zIndex === "number") depths.set(datum.id, style.zIndex);
      }
      // What the names are under: a label fully covered by a mark standing
      // above it leaves the fight — see `resolveVisibility`. Bodies only, and
      // authored depth, the same numbers the frame stamped.
      const occluders: VisibilityOccluder[] = [];
      for (const datum of frame.nodes) {
        const style = datum.style as Record<string, unknown> | undefined;
        const z = typeof style?.zIndex === "number" ? style.zIndex : PAINT_LAYER_MARK;
        const mark = paintedMarkBox(graph, datum.id);
        if (mark) occluders.push({ ...mark, z });
      }
      const prev = new Map(
        [...remembered].map(([id, record]) => [id, record.strength] as const),
      );
      settled = resolveVisibility(boxes, ranks, prev, {
        occluders,
        depths,
      });
    } else {
      // Strengths off: every standing name reads at its full authored
      // strength. Anything still dimmed from before the switch restores
      // through the normal paint below; afterwards this settles nothing.
      settled = new Map(
        [...remembered.keys()].map((id) => [id, 1] as const),
      );
    }
    const byId = new Map<string, { datum: CanvasDatum; node: boolean }>();
    for (const datum of frame.nodes) byId.set(datum.id, { datum, node: true });
    for (const datum of frame.edges) byId.set(datum.id, { datum, node: false });
    const nodePatches: CanvasDatum[] = [];
    const edgePatches: CanvasDatum[] = [];
    const paint: { id: string; from: number; to: number }[] = [];
    for (const [id, strength] of settled) {
      const record = remembered.get(id);
      if ((record?.strength ?? 1) === strength) continue;
      const entry = byId.get(id);
      const style = entry?.datum.style as Record<string, unknown> | undefined;
      if (!entry || !style) continue;
      const base =
        record?.base ??
        (typeof style.labelFillOpacity === "number" ? style.labelFillOpacity : 1);
      remembered.set(id, { strength, base });
      // The baseline carries what is painted — see above.
      style.labelFillOpacity = base * strength;
      // A drag owns the live position. Writing the whole authored datum here
      // would put its old coordinates back into G6's store between moves.
      // But an edge patch without a numeric zIndex makes G6 rewrite the
      // edge's depth from its endpoints (`runtime/data.js` sets it to the
      // fronter end minus one), sinking the name to the stroke layer — so
      // the authored depth rides along. Nodes skip that rewrite on update.
      const patchStyle: Record<string, unknown> = {
        labelFillOpacity: base * strength,
      };
      if (!entry.node && typeof style.zIndex === "number") {
        patchStyle.zIndex = style.zIndex;
      }
      (entry.node ? nodePatches : edgePatches).push({ id, style: patchStyle });
      paint.push({ id, from: base * (record?.strength ?? 1), to: base * strength });
    }
    if (!paint.length) return;
    if (nodePatches.length) graph.updateNodeData(nodePatches as never);
    if (edgePatches.length) graph.updateEdgeData(edgePatches as never);
    const plans = motionRef.current;
    // Pointer travel already supplies the motion. Restarting a fade at each
    // position makes strength trail the hand and settle only after release.
    const tracking = draggingRef.current || reducedMotion();
    paintLabelStrength(graph, paint, {
      weakenPlan: tracking ? undefined : plans.absorb,
      restorePlan: tracking ? undefined : plans.emit,
    });
  }, []);

  const queueCanvasDraw = useCallback(() => {
    const scheduledGraph = graphRef.current;
    if (
      !scheduledGraph ||
      draggingRef.current ||
      contactHoldsLane(contactRef.current.phase)
    ) return;

    drawLaneRef.current = drawLaneRef.current
      .catch(() => undefined)
      .then(async () => {
        const graph = graphRef.current;
        if (!graph || graph !== scheduledGraph || graph.destroyed) return;

        // Whether any frame landed this run, for the visibility pass below:
        // strengths settle off the drawing, so only a run that drew owes one.
        let drew = false;
        while (
          pendingFrameRef.current &&
          !draggingRef.current &&
          !contactHoldsLane(contactRef.current.phase)
        ) {
          const next = pendingFrameRef.current;
          pendingFrameRef.current = null;

          try {
            /**
             * Restored data was already rendered by the constructor. Do not
             * send it through a no-op animated draw before centring: G6
             * completes that camera-affecting frame after the draw promise and
             * used to undo the vertical half of the centre operation.
             */
            const restoring =
              !next.animateInitial &&
              drawnRef.current === 0 &&
              next.nodes.length > 0;
            /**
             * Only if the constructor really held it. The stored field is put
             * back once the world's overview arrives, which can be after the
             * graph was built empty — then nothing was rendered, centring
             * asks for positions of elements that do not exist, and the field
             * stays blank until something else changes.
             */
            if (restoring && authoredRef.current?.nodes.length) {
              drawnRef.current = next.nodes.length;
              /**
               * A stored camera is the establishment: the person framed this
               * field last visit, and centring over it would spend their
               * framing on the default. Nothing stored, centre as always.
               */
              if (!(await recorderRef.current?.restore(graph))) {
                if (next.nodes.length === 1) {
                  await graph.zoomTo(1, { duration: 0 });
                }
                await centreStandingField(
                  graph,
                  next.nodes
                    .map((node) => node.id)
                    .filter((id) => !isDecoration(id)),
                  insetsRef.current,
                );
              }
              drew = true;
              continue;
            }

            /**
             * The frame only changes what standing marks look like.
             *
             * Hover is the pointer-direct case the lifecycle was never for:
             * nothing arrives, nothing leaves, and `marksNeverMove` means
             * nothing is anywhere new. `graph.draw()` cannot express that
             * cheaply — with an update animation declared it builds one for
             * every element on the field whether or not it changed — so the
             * restyle goes to the elements and the draw is not asked for.
             *
             * An arrangement is excluded by name rather than by shape: the
             * marks did move, and `settle` is a body finding a new rest.
             */
            if (
              !next.arranged &&
              restyleCanvasData(graph, authoredRef.current, next, {
                // The one channel a restyle is not allowed to cut. A name
                // arriving is a body leaving its home, on this lane as on the
                // draw's — see `fadeShape`. Furniture withdrawing with its
                // plate takes the lifecycle's own release and reveal.
                labelPlan: reducedMotion() ? undefined : motionRef.current.emit,
                revealPlan: reducedMotion() ? undefined : motionRef.current.emit,
                releasePlan: reducedMotion()
                  ? undefined
                  : motionRef.current.absorb,
              })
            ) {
              authoredRef.current = next;
              drawnFieldIds.current = next.fieldIds;
              drawnRef.current = next.nodes.length;
              /**
               * Debts a cancelled lifecycle owed — see
               * `convergeStrandedToFrame`. The schema lane converges
               * asynchronously behind its flight; this lane is serial, so the
               * guard runs inline: a restyle that patched stranded poses
               * redraws before the loop continues, and the visibility pass
               * below reads the healed boxes. Positions are never converged —
               * a draw that re-applied stored positions mid-gesture would snap
               * the mark out from under the pointer, and the lane holds all
               * draws while one is held anyway.
               */
              if (convergeStrandedToFrame(graph, next)) {
                try {
                  await graph.draw();
                } catch {
                  // Healing is best-effort; the lane continues settled.
                }
              }
              drew = true;
              continue;
            }

            // A restyle has already continued above. Reaching this path means
            // identities, topology or authored positions changed, which is
            // the only reason the D3 body set should be rebuilt.
            authoredRef.current = next;
            await transitionCanvasData(
              graph,
              next,
              () => graphRef.current !== graph || graph.destroyed,
              {
                // A restored field was standing when this person left it.
                still: next.still || restoring,
                birthPlan: lifecycleMotionRef.current.birth,
                collapsePlan: lifecycleMotionRef.current.collapse,
                releasePlan: motionRef.current.absorb,
                /**
                 * Standing marks are `still` — rule 1 — so `hold` is all the
                 * appearance plan usually has to carry: a colour, a light, a
                 * name. An arrangement is the one frame where matter that was
                 * already placed goes somewhere else, and a body moving to a
                 * new rest is `settle`. It is not `hold`, because `hold` means
                 * *you are moving it*, and nobody's pointer is on these.
                 */
                appearancePlan: next.arranged
                  ? motionRef.current.settle
                  : motionRef.current.hold,
                labelPlan: motionRef.current.emit,
                bindingDelayMs: motionRef.current.hold.durationMs,
                staggerWindowMs: motionRef.current.absorb.durationMs,
                retainedNode: (id) => next.fieldIds.has(markOfElement(id)),
                returningNode: (id) => drawnFieldIds.current.has(markOfElement(id)),
                returningEdge: (id) => {
                  const bundle = subjectOfBundle(id);
                  return drawnFieldIds.current.has(bundle ?? markOfElement(id));
                },
                revealPlan: motionRef.current.emit,
              },
            );
            drawnFieldIds.current = next.fieldIds;
            if (graphRef.current !== graph || graph.destroyed) return;
            drew = true;

            const count = next.nodes.length;
            const grew = count > drawnRef.current;
            drawnRef.current = count;
            if (grew && count === 1) {
              await graph.zoomTo(1, { duration: 0 });
            }
            if (restoring && !(await recorderRef.current?.restore(graph))) {
              await centreStandingField(
                graph,
                next.nodes
                  .map((node) => node.id)
                  .filter((id) => !isDecoration(id)),
                insetsRef.current,
              );
            }
          } catch (problem: unknown) {
            if (graphRef.current === graph) console.error(problem);
          }
        }
        // The drawing changed, so which names overlap is a different answer
        // than it was before the draw. Before the fan commits: the fan moves
        // names without drawing, and follows frame by frame off its own
        // event below — this settles the strengths the fan starts from.
        if (drew && graphRef.current === graph && !graph.destroyed) {
          applyVisibility(graph);
        }
        // Matter arrived, left or was re-placed, so which strokes the held
        // mark carries — and where they point — is a different answer than it
        // was before the draw.
        if (
          graphRef.current === graph &&
          !graph.destroyed &&
          !spreadSuspendedRef.current
        ) {
          spreadFieldRef.current?.commit(spreadOwnerRef.current);
        }
      });
  }, []);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const blockMenu = (event: Event) => event.preventDefault();
    host.addEventListener("contextmenu", blockMenu);
    // Before the graph, because G6 resolves an edge's type as it builds it.
    ensureWorldFilamentRegistered();
    const graph = new Graph({
      container: host,
      data: (animateInitial ? { nodes: [], edges: [] } : data) as never,
      animation: false,
      padding: 60,
      // Transparent on purpose. G6's `setOptions({ background })` stores the
      // colour but never paints it, so an opaque field set at mount stuck
      // through every theme flip. The live field is `--matter-canvas` on the
      // stage, the same path the product canvas uses.
      background: "transparent",
      // No `selected` element state. Selection is drawn over the canvas by the
      // ants, so the renderer is not also asked to thicken a line or lay a
      // halo under a disc — two marks for one fact, and the quieter one was
      // the only one anybody read.
      node: { style: { cursor: "grab" } },
      edge: { style: { cursor: "default" } },
      behaviors: [
        "zoom-canvas",
        {
          type: "drag-canvas",
          enable: (event: { targetType?: string }) => event.targetType === "canvas",
        },
        {
          type: "drag-element",
          key: "drag-element",
          // Product nodes are not combo containers. G6's default `move`
          // effect refreshes combo data on every pointer event, which is pure
          // bookkeeping here and makes the held object trail the pointer.
          dropEffect: "none",
          animation: false,
          enable: (event: unknown) => {
            const id = (event as { target?: { id?: unknown } })?.target?.id;
            return typeof id === "string" && !isDecoration(id);
          },
        },
      ],
    });
    graphRef.current = graph;
    // What the graph was built holding is what is on the field, so it is the
    // baseline the first restyle diffs against. An animated initial load is
    // built empty and everything is a birth, which the lifecycle owns.
    authoredRef.current = animateInitial
      ? { nodes: [], edges: [] }
      : (data as CanvasData);
    spreadFieldRef.current = createSpreadField({
      graph,
      params: () => paramsRef.current,
      motion: () => motionRef.current,
      enabled: () => spreadOnSelectRef.current,
      reduced: reducedMotion,
    });
    /**
     * Strengths under the fan and the pointer, frame by frame.
     *
     * The fan moves names without drawing — spread writes the strokes
     * directly — so a pass that only ran after draws would freeze strengths
     * at their pre-fan values: names the fan just cleared would keep the
     * whisper they no longer owe. The field announces every frame it moves
     * something on, and the outline already follows it the same way — see
     * `SelectionAnts`. Coalesced to one pass per frame; at rest nothing is
     * announced and nothing runs.
     */
    let visibilityFrame = 0;
    const scheduleVisibility = () => {
      if (visibilityFrame) return;
      visibilityFrame = window.requestAnimationFrame(() => {
        visibilityFrame = 0;
        if (graphRef.current === graph && !graph.destroyed) {
          applyVisibility(graph);
        }
      });
    };
    // Resolved once the first render lands: the canvas does not exist until
    // then, and the fan cannot move names before it either.
    let spreadContainer: HTMLElement | null = null;

    const idOf = (event: unknown): string | null => {
      const target = (event as { target?: { id?: unknown } } | undefined)?.target;
      return typeof target?.id === "string" ? target.id : null;
    };
    const subject = (id: string | null) =>
      id && !isDecoration(id) ? id : null;
    /**
     * The mark an element belongs to.
     *
     * A spoke's id is its mark's id with `:index` appended, and cutting at the
     * *first* colon was wrong for everything: an assertion id is already
     * `assertion:<digest>`, so a bond's filament resolved to the literal string
     * "assertion" and hovering or clicking one selected nothing at all. Only
     * the trailing index is a suffix this surface added, so only that is taken
     * off.
     */
    // A bundle is furniture with an edge's id. Nothing that turns an element
    // into a mark may accept one, or the reader opens on an assertion whose id
    // is a label's.
    const markOf = (id: string | null) =>
      id && !subjectOfBundle(id) ? markOfElement(id) : null;

    /** One mark's crown and shelf, brought to where the pointer has it. */
    const followFurniture = (id: string) => {
      const position = graph.getElementPosition(id);
      // A body still nucleating answers `[null, null, 0]`, which is an array
      // and therefore truthy. Passed on, the nulls reach G6's vector maths and
      // throw out of a `requestAnimationFrame` — so a mark taken hold of while
      // its neighbours were still arriving killed the drag it was in.
      if (!position || !Number.isFinite(position[0]) || !Number.isFinite(position[1])) {
        return;
      }
      liveRef.current.set(id, { x: position[0], y: position[1] });
      const present = new Set(
        graph.getNodeData().map((node) => String(node.id)),
      );
      const offset = params.chipHeight / 2 + params.shelfGap;
      const moved: Record<string, [number, number]> = {};
      for (const furniture of furnitureOf(id)) {
        if (!present.has(furniture)) continue;
        moved[furniture] = [
          position[0],
          furniture.startsWith("crown:")
            ? position[1] - offset
            : position[1] + offset,
        ];
      }
      if (Object.keys(moved).length) {
        void graph.translateElementTo(moved, false);
      }
      relayoutIncidentLabels(id, { [id]: [position[0], position[1]] }, present);
    };

    /**
     * The gesture shows the settled state: the grab carries the depth the
     * drop will stamp.
     *
     * G6 fronts the held mark once, at `dragstart` — `frontElement` in its
     * drag behavior, above even the names — and the drop's redraw would sink
     * it back to the restack top: the release speaking for the gesture. The
     * prediction is the drop's own call — `restackTop`, the number `restack`
     * records — so the grab rides what the release restates by construction,
     * not by agreeing on a formula. Written through `setElementZIndex`, the
     * renderer's own z channel: a targeted re-sort, not a draw, so the mark
     * stays under the pointer.
     *
     * A microtask behind the event, because the behavior's own listener runs
     * behind this one: behaviors bind when the graph initializes, after these
     * listeners attached, so a synchronous write lands under the fronting
     * rather than on top of it. The microtask drains before paint, so the
     * front never shows — the gesture's first frame is already the settled
     * one. The moves after need nothing: the behavior only translates from
     * there.
     */
    const rideSettledDepth = (id: string) => {
      const settled = restackTop(setRef.current.depth, id);
      queueMicrotask(() => {
        if (graph.destroyed) return;
        void graph.setElementZIndex(id, settled);
      });
    };
    /**
     * A press that went nowhere restacks nothing — so neither does its depth.
     *
     * The grab rode the settled depth on the assumption of a drop, and the
     * release owes the mark its rest back: without this the predicted number
     * sticks in the store, because a draw that changed nothing restyles
     * nothing. The rest is the stamped paint, not a recomputation — same
     * readers, same answer.
     */
    const restoreRestDepth = (id: string) => {
      const rest =
        paintDepths(setRef.current.depth).get(id) ?? PAINT_LAYER_MARK;
      void graph.setElementZIndex(id, rest);
    };

    const relayoutIncidentLabels = (
      nodeIds: string | readonly string[],
      knownPositions?: Readonly<Record<string, [number, number]>>,
      knownPresent?: Set<string>,
    ) => {
      const current = setRef.current;
      const p = paramsRef.current;
      const moved = new Set(
        typeof nodeIds === "string" ? [nodeIds] : nodeIds,
      );
      const present =
        knownPresent ??
        new Set(graph.getNodeData().map((node) => String(node.id)));
      const at = (id: string) => {
        const known = knownPositions?.[id];
        if (known) return { x: known[0], y: known[1] };
        // React may already hold an expansion frame that the draw lane is
        // intentionally postponing until this drag ends. Asking G6 for that
        // future element throws; its authored position is enough until its
        // edge actually exists, at which point the queued draw lays it out.
        //
        // A body part-way through nucleation answers with nulls rather than
        // refusing, and a station computed off those is `NaN` — which G6 keeps
        // and the plate then vanishes from the field entirely. The authored
        // position is the right fallback for both.
        const here = present.has(id) ? graph.getElementPosition(id) : null;
        return here && Number.isFinite(here[0]) && Number.isFinite(here[1])
          ? { x: here[0], y: here[1] }
          : liveAt(liveRef.current, current.positions, id);
      };
      const station = (elementId: string, layout: ReturnType<typeof bondLabelLayout>) => {
        const edge = liveEdge(graph, elementId);
        if (!edge) return;
        edge.parsedAttributes.labelPlacement = layout.placement;
        edge.parsedAttributes.labelOffsetX = layout.offsetX;
        edge.parsedAttributes.labelOffsetY = layout.offsetY;
        edge.onframe();
      };
      const visibleBonds = current.bonds.filter(
        (bond) =>
          current.referents.has(bond.source) &&
          current.referents.has(bond.target) &&
          (moved.has(bond.source) || moved.has(bond.target)),
      );
      const byEndpoints = new Map<string, typeof visibleBonds>();
      for (const bond of visibleBonds) {
        const key = [bond.source, bond.target].sort().join("\u0000");
        const group = byEndpoints.get(key) ?? [];
        group.push(bond);
        byEndpoints.set(key, group);
      }
      const poses = groupPosesRef.current;
      /**
       * The station the draw resolved, not a second opinion about it.
       *
       * This pass used to re-answer the question from the pointer subjects it
       * could see, which is how a drag and the frame it started from ended up
       * disagreeing about where a name belongs. Geometry is this pass's to
       * recompute — the filament turns and lengthens under the hand. *Which
       * end* is not: nothing about a drag changes which mark a person is
       * looking at.
       */
      const stations = stationsRef.current;
      const nearEnd = (elementId: string) => stations.get(elementId);
      /**
       * The stack, recomputed exactly the way the draw computes it.
       *
       * This used to be a flat `chipHeight + gap` step, which is the right
       * answer only on a horizontal filament — so parallel names moved apart
       * the instant a drag began and closed up again on release, having been
       * spaced by two different rules. There is one rule now and it is
       * `bondLabelStep`; what this pass still cannot derive is which plates a
       * group is showing, which is why the draw records a pose.
       */
      /**
       * The draw's own station, read back — see the fan's reader.
       *
       * Both numbers, not just the distance: a grouped bond is drawn at the
       * widest member's width rule, and this pass recomputing its own half is
       * a name that jumps on first drag.
       */
      const stored = (elementId: string): { along: number; half: number } => {
        const attrs = liveEdge(graph, elementId)?.parsedAttributes;
        return {
          along: Number(attrs?.bondAlong) || BOND_LABEL_ALONG_PX,
          half: Number(attrs?.bondHalf) || 0,
        };
      };
      const stackByAssertion = new Map<string, { x: number; y: number }>();
      for (const [key, unsorted] of byEndpoints) {
        const group = [...unsorted].sort((a, b) =>
          `${a.relation}\u0000${a.assertion_id}`.localeCompare(
            `${b.relation}\u0000${b.assertion_id}`,
          ),
        );
        const first = group[0];
        if (!first) continue;
        const pose = poses.get(key);
        const shown = pose
          ? pose.shown
          : group.map((bond) => bond.assertion_id);
        const step = bondLabelStep(p);
        const stepped = (count: number) => ({
          x: step.x * count,
          y: step.y * count,
        });
        const middle = (shown.length - 1) / 2;
        for (const bond of group) {
          stackByAssertion.set(bond.assertion_id, { x: 0, y: 0 });
        }
        shown.forEach((assertionId, index) => {
          stackByAssertion.set(assertionId, stepped(index - middle));
        });
        // Fit is the draw's to decide: a drag re-seats plates on the moving
        // filament but never hides or shows one mid-gesture, or names would
        // blink as the line shortened past them and back.
        /**
         * The count rides the station its claims ride.
         *
         * This pass restationed every plate on a moving filament except this
         * one, so a drag left the count's placement frozen while the filament
         * under it changed length — and a frozen share of a changing length is
         * a distance that slides. It is the label a reader watches most, and it
         * was the one that moved.
         */
        if (pose?.bundleId) {
          const { along, half } = stored(pose.bundleId);
          const layout = bondLabelLayout(
            at(first.source),
            at(first.target),
            nearEnd(pose.bundleId),
            // Closed, the count stands on the filament itself; open, one step
            // past the last plate it is standing in for. Which of the two is
            // the draw's to say; how wide a step is, is this pass's.
            stepped(pose.bundleSteps),
            p,
            discRim(p),
            discRim(p),
            along,
            half,
          );
          station(pose.bundleId, { ...layout });
        }
      }
      for (const bond of visibleBonds) {
        const elementId = bondElementId(bond.assertion_id);
        const { along, half } = stored(elementId);
        const layout = bondLabelLayout(
          at(bond.source),
          at(bond.target),
          nearEnd(elementId),
          stackByAssertion.get(bond.assertion_id) ?? { x: 0, y: 0 },
          p,
          discRim(p),
          discRim(p),
          along,
          half,
        );
        station(elementId, { ...layout });
      }
      const stationSpoke = (
        elementId: string,
        fromId: string,
        toId: string,
        relation: string,
        role: string,
      ) => {
        const near = nearEnd(elementId);
        // The same station the draw used, from the same helper. A width-aware
        // station this pass computed differently is a name that jumps the
        // first time its mark is picked up.
        //
        // Recomputed, not read back like a bond's: past a plate the station
        // depends on the angle the spoke arrives at, so the draw's number is
        // stale the moment the filament turns — and standing it off again
        // would stand the standoff off, moving the name twice.
        const { halfPlate, air } = spokeLabelStation(role, p);
        station(
          elementId,
          bondLabelLayout(
            at(fromId),
            at(toId),
            near,
            { x: 0, y: 0 },
            p,
            discRim(p),
            // The plate's own width, not its height: the far rim of a spoke
            // moves with the angle the stroke arrives at, and a station
            // measured against the wrong rim moves with it.
            plateRim(relation, p),
            SPOKE_LABEL_ALONG_PX,
            halfPlate,
            air,
          ),
        );
      };
      for (const assertion of current.assertions.values()) {
        assertion.spokes.forEach((spoke, index) => {
          if (!current.referents.has(spoke.id)) return;
          if (!moved.has(spoke.id) && !moved.has(assertion.assertion_id)) return;
          stationSpoke(
            `${assertion.assertion_id}:${index}`,
            spoke.id,
            assertion.assertion_id,
            assertion.relation,
            spoke.role,
          );
        });
      }
      for (const demand of current.demands.values()) {
        demand.spokes.forEach((spoke, index) => {
          if (!current.referents.has(spoke.id)) return;
          if (!moved.has(spoke.id) && !moved.has(demand.key)) return;
          stationSpoke(
            `${demand.key}:${index}`,
            spoke.id,
            demand.key,
            demand.relation,
            spoke.role,
          );
        });
      }
    };

    let suppressReleaseClick = false;
    let releaseClickTimer: number | undefined;
    type RunningContact = {
      from: number;
      to: number;
      plan: MotionPlan;
      key: MaterialAnimation | null;
      label: MaterialAnimation | null;
    };
    const runningContact = new Map<string, RunningContact>();
    const updateContact = (event: ContactEvent) => {
      const next = transitionContact(contactRef.current, event);
      if (next === contactRef.current) return next;
      contactRef.current = next;
      setContact(next);
      return next;
    };
    const elementOf = (id: string): MaterialElement | undefined =>
      (
        graph as unknown as {
          context?: {
            element?: { getElement: (elementId: string) => MaterialElement };
          };
        }
      ).context?.element?.getElement(id);
    const scaleTransform = (scale: number) => [
      ["scale", scale, scale],
    ];
    /**
     * Contact acts on the two local shapes of one body. It never changes the
     * graph's global node mapper and therefore never asks unrelated matter to
     * refresh. The tracked trajectory also lets a quick release begin at the
     * compression actually reached, rather than jumping to the full load.
     */
    const animateContact = (
      id: string,
      target: number,
      plan: MotionPlan,
    ): Promise<void> => {
      const element = elementOf(id);
      const key = element?.getShape("key");
      const label = element?.getShape("label");
      if (!key) return Promise.resolve();

      const previous = runningContact.get(id);
      const elapsed = Math.max(
        0,
        Math.min(
          previous?.plan.durationMs ?? 0,
          Number(previous?.key?.currentTime ?? previous?.plan.durationMs ?? 0),
        ),
      );
      const progress = previous
        ? previous.plan.sample(elapsed) /
          Math.max(previous.plan.sample(previous.plan.durationMs), 1e-6)
        : 1;
      const from = previous
        ? previous.from + (previous.to - previous.from) * progress
        : target === 1
          ? materialRef.current.pressScale
          : 1;

      previous?.key?.cancel();
      previous?.label?.cancel();
      runningContact.delete(id);

      const start = scaleTransform(from);
      const end = scaleTransform(target);
      key.attr({ transform: start });
      label?.attr({ transform: start });

      if (reducedMotion()) {
        key.attr({ transform: end });
        label?.attr({ transform: end });
        return Promise.resolve();
      }

      const options = g6KeyframeMotion(plan);
      let keyAnimation: MaterialAnimation | null = null;
      let labelAnimation: MaterialAnimation | null = null;
      try {
        keyAnimation = key.animate(
          [{ transform: start }, { transform: end }],
          options,
        );
        labelAnimation =
          label?.animate([{ transform: start }, { transform: end }], options) ??
          null;
      } catch {
        /**
         * The same nucleation race the stations and the ring hit.
         *
         * A body whose shapes are not laid out yet cannot be animated — G's
         * timeline reads a null transform and throws, out of a
         * `requestAnimationFrame` where nothing catches it. Contact is a
         * response to a press that has already happened, so the honest failure
         * is to land on the pose without the travel, not to abandon the frame.
         */
        key.attr({ transform: end });
        label?.attr({ transform: end });
        runningContact.delete(id);
        return Promise.resolve();
      }
      const running = {
        from,
        to: target,
        plan,
        key: keyAnimation,
        label: labelAnimation,
      };
      runningContact.set(id, running);

      const finished = [keyAnimation, labelAnimation]
        .filter((animation): animation is MaterialAnimation =>
          Boolean(animation),
        )
        .map((animation) => animation.finished.catch(() => undefined));
      // G's animation timeline can be replaced by a graph draw. The draw lane
      // is held while contact is live, but this deadline is the final safety
      // law: renderer interruption may shorten a release, never strand it.
      const deadline = new Promise<void>((resolve) => {
        window.setTimeout(resolve, plan.durationMs + 64);
      });
      return Promise.race([
        Promise.all(finished).then(() => undefined),
        deadline,
      ]).then(() => {
        if (runningContact.get(id) !== running) return;
        keyAnimation?.cancel();
        labelAnimation?.cancel();
        key.attr({ transform: end });
        label?.attr({ transform: end });
        runningContact.delete(id);
      });
    };
    const engageContact = (id: string) => {
      if (!materialRef.current.contact || isDecoration(id)) return;
      const next = updateContact({ type: "press", id });
      if (next.phase !== "pressed" || next.id !== id) return;
      void animateContact(
        id,
        materialRef.current.pressScale,
        motionRef.current.hold,
      );
      return next;
    };
    const releaseContact = () => {
      const next = updateContact({ type: "release" });
      if (next.phase !== "releasing") return;
      const { id } = next;
      // A small contact deformation should clear within the pointer-response
      // window: the spring curve, run at `hold`. It is compressed because the
      // load was small, not to get out of the observer's way — nothing waits
      // on it now that `releasing` no longer holds the draw lane.
      const release = scaleMotionPlan(
        motionRef.current.settle,
        motionRef.current.settle.durationMs / motionRef.current.hold.durationMs,
      );
      void animateContact(id, 1, release).finally(() => {
        updateContact({ type: "settled", id });
        queueCanvasDraw();
      });
    };
    const markReleaseClick = () => {
      suppressReleaseClick = true;
      window.clearTimeout(releaseClickTimer);
      releaseClickTimer = window.setTimeout(() => {
        suppressReleaseClick = false;
      }, 0);
    };
    const swallowReleaseClick = () => {
      if (!suppressReleaseClick) return false;
      suppressReleaseClick = false;
      window.clearTimeout(releaseClickTimer);
      return true;
    };
    const hovering = (id: string | null) => {
      if (draggingRef.current) return;
      window.clearTimeout(hoverStandDown.current);
      hoverStandDown.current = undefined;
      if (id !== null) {
        onHoverRef.current(id);
        return;
      }
      /**
       * Standing down is a reach too.
       *
       * What a hover reveals — a count, the names on the bonds around it —
       * stands off the disc, so leaving the disc is the first half of reaching
       * for one of them. Dropping the light on the frame the pointer crosses
       * the rim takes the answer away before the hand arrives, and on a
       * trackpad it also reads as flicker on any pass across the field.
       *
       * Arriving anywhere cancels it, so this only ever delays the moment
       * nothing is being looked at.
       */
      hoverStandDown.current = window.setTimeout(() => {
        hoverStandDown.current = undefined;
        onHoverRef.current(null);
      }, motionRef.current.emit.durationMs);
    };
    const pickNode = (id: string): NonNullable<CanvasSelection> => {
      const current = setRef.current;
      if (current.assertions.has(id)) return { kind: "assertion", id };
      if (current.demands.has(id)) return { kind: "demand", id };
      return { kind: "referent", id };
    };
    const pickEdge = (id: string): NonNullable<CanvasSelection> =>
      setRef.current.demands.has(id)
        ? { kind: "demand", id }
        : { kind: "assertion", id };
    const swallowMenu = (event: unknown) => {
      const e = event as {
        preventDefault?: () => void;
        nativeEvent?: Event;
      };
      e.preventDefault?.();
      e.nativeEvent?.preventDefault?.();
    };

    /**
     * Whether an element belongs to the group a count has opened.
     *
     * The group is the parallel claims between one pair of referents, so
     * membership is the endpoints rather than the ids: the count, every claim
     * it reveals, and the two discs they run between are all one thing to
     * reach for.
     */
    /**
     * A count is opened by being clicked, and stays open until dismissed.
     *
     * It used to open on hover, and the whole apparatus that required — a
     * canvas-space hit test on every `pointermove`, a release timer, and a
     * hold/release hysteresis to survive the pointer crossing unpainted canvas
     * between the claims it had just revealed — existed to make an accident
     * behave like an intention. It opened on the way past and closed while you
     * were reaching for what it had shown you.
     *
     * Selection now opens the groups on a mark, so most counts are never met
     * at all. The ones that remain mark groups nobody has gone to yet, and
     * going to one is a click.
     *
     * The hit test stays, because G6's picker still will not deliver events
     * for these labels — but it runs once per click instead of once per
     * pointer move, and `stopPropagation` keeps the same click from also
     * reaching the canvas and clearing the selection underneath.
     *
     * It reaches bond names as well as counts, and that was the gap. A binary
     * claim has no plate — the name on its filament *is* the claim's only
     * drawing — so while G6 refused those clicks the only way to open one was
     * to find it in a table. Role names on spokes are deliberately not
     * reachable: a role is a coordinate on a claim whose plate is already a
     * few pixels away, and a second way to select one thing is a way to select
     * it by accident.
     */
    const reachableLabel = (id: string) =>
      id.startsWith("bundle:") || id.startsWith("bond:");
    /**
     * The click that follows the press this handler already answered.
     *
     * Swallowing the `pointerdown` does not swallow the `click`: the browser
     * still dispatches one, G6's picker still fails to find the label under
     * it, and what it does find is the canvas — which is the gesture for
     * "nothing here", so the selection this press just made would be undone by
     * the release of the same press. Capture on the host beats the listener G6
     * has on its own canvas.
     *
     * Decided by *where* the click landed, not by how long ago the press was.
     * A time window was the first attempt and it is the wrong instrument: it
     * makes a slow click and a quick one two different gestures, which is a
     * distinction nobody makes on purpose and a bug nobody can describe.
     */
    const swallowLabelClick = (event: MouseEvent) => {
      if (
        !labelUnderPointer(graph, event.clientX, event.clientY, reachableLabel)
      ) {
        return;
      }
      event.stopPropagation();
      event.preventDefault();
    };
    /**
     * Whether the press this release belongs to landed on a name.
     *
     * G6's "click on nothing" does not come from the DOM `click` — swallowing
     * that was not enough, and the reader opened on the press and closed again
     * on the release. Whatever @antv/g derives its click from, it arrives as
     * `canvas:click`, so the answer is given there: every press through this
     * host records whether it hit a reachable label, and the release that
     * follows a hit is not "nothing here".
     *
     * Recorded on *every* press, hit or miss, so it is never stale — a press
     * on empty canvas clears it on the way in.
     */
    let pressedLabel = false;
    const clickLabel = (event: PointerEvent) => {
      if (draggingRef.current) return;
      const hit = labelUnderPointer(
        graph,
        event.clientX,
        event.clientY,
        reachableLabel,
      );
      pressedLabel = Boolean(hit);
      if (!hit) return;
      event.stopPropagation();
      event.preventDefault();
      // A bond's name is its only drawing, and G6 delivers no events for it —
      // so the host hit test above is also the removal path. A right press on
      // one removes what it names, exactly like a right press on a mark; a
      // left press selects, as below. Counts keep their toggle on any button.
      if (event.button === 2 && !subjectOfBundle(hit)) {
        const id = markOf(hit);
        if (id) removeAtPress(pickEdge(id));
        return;
      }
      window.clearTimeout(hoverStandDown.current);
      hoverStandDown.current = undefined;
      if (subjectOfBundle(hit)) {
        setOpenedBundle(openedBundleRef.current === hit ? null : hit);
        return;
      }
      const id = markOf(hit);
      if (!id) return;
      // Same as `node:click`: a count opened elsewhere was a question about a
      // mark this person has now stopped asking about.
      setOpenedBundle(null);
      // A canvas pick, not travel: the fan that revealed this label stays.
      labelPickRef.current = id;
      onSelectRef.current(pickEdge(id));
    };
    host.addEventListener("pointerdown", clickLabel, true);
    host.addEventListener("click", swallowLabelClick, true);

    /**
     * The whole of a name the disc had to cut.
     *
     * A referent's label wraps to two lines and ellipsises the rest, so
     * `Philips Respironics BiPAP A30 family` reads as `Philips Respironics …`
     * and until now the only way to see the rest was to select the mark —
     * which is a different act with a different consequence, and a poor price
     * for reading a word.
     *
     * The host's `title` is the one affordance a canvas has here: it is the
     * browser's, it is inert, it appears because a person held still over the
     * thing, and it moves nothing. Offered only where the name was actually
     * cut, so the field is not covered in tooltips repeating what is already
     * legible, and taken down on the way out so it cannot outlive the mark it
     * belongs to.
     */
    const nameInFull = (id: string | null) => {
      if (!id) return "";
      const referent = setRef.current.referents.get(id);
      const label = referent?.label ?? "";
      return label && discLabelTruncated(label, paramsRef.current) ? label : "";
    };

    graph.on("node:pointerenter", (event) => {
      const id = subject(idOf(event));
      host.title = nameInFull(id);
      hovering(id);
    });
    graph.on("node:pointerleave", () => {
      host.title = "";
      hovering(null);
    });
    /**
     * A bond's own name keeps the light up while the pointer is on it.
     *
     * An edge never becomes `hovered`: hover is a light source, and a label is
     * read rather than lit. All this does is cancel the stand-down, so
     * crossing from a disc onto one of its names does not take the light off
     * the thing the name belongs to.
     */
    graph.on("edge:pointerenter", () => {
      if (draggingRef.current) return;
      window.clearTimeout(hoverStandDown.current);
      hoverStandDown.current = undefined;
    });
    /** The mark keeping the live field awake, whether or not it becomes a drag. */
    let physicsHeld: string | null = null;
    /**
     * Which mouse button a G6 pointer event arrived on, if it says.
     *
     * G6 hands through the renderer's federated event, which mirrors the DOM
     * button — but the only use here is telling a right press from a left one,
     * so both nestings are read and anything unreadable is not a right press.
     */
    const pressButton = (event: unknown): number | null => {
      // G6 spreads the renderer's button onto the forwarded event top level
      // (`behavior.js` forwards `{...event, button}`); the nestings are the
      // DOM event underneath, for a forwarder that does not spread.
      const outer = event as
        | { button?: unknown; nativeEvent?: unknown }
        | undefined;
      const native = outer?.nativeEvent as
        | { button?: unknown; nativeEvent?: { button?: unknown } }
        | undefined;
      const button =
        outer?.button ?? native?.button ?? native?.nativeEvent?.button;
      return typeof button === "number" ? button : null;
    };
    /**
     * The last mark a right press removed, so its menu can stand down.
     *
     * G6 synthesizes `contextmenu` from the right press itself (`behavior.js`
     * emits it inside the `pointerdown` forward), so the menu arrives in the
     * same tick as the removal it would repeat. Only a menu with no press
     * behind it at all — a keyboard-emitted one — falls through.
     */
    let lastRemoved: { id: string; at: number } | null = null;
    const recentlyRemoved = (id: string): boolean =>
      lastRemoved?.id === id && performance.now() - lastRemoved.at < 500;
    const removeAtPress = (mark: NonNullable<CanvasSelection>) => {
      lastRemoved = { id: mark.id, at: performance.now() };
      // A removal is the decision, so the press it arrived on has no claim on
      // the frame that answers it: the draw lane is released before the set
      // changes, and the collapse plays from there.
      releaseContact();
      onRemoveRef.current(mark);
    };
    graph.on("node:pointerdown", (event) => {
      const raw = idOf(event);
      const id = subject(raw);
      if (id) {
        physicsHeld = id;
        engageContact(id);
        // A bundle label is not a mark — pressing one must not remove the
        // bundle's subject, which the press never named.
        if (pressButton(event) === 2 && raw && !subjectOfBundle(raw)) {
          removeAtPress(pickNode(id));
        }
        /**
         * The fan drops on being *held*, not on becoming a drag.
         *
         * A drag cannot happen without a hold, so hanging this off `dragstart`
         * only meant the fan survived the part of the gesture where the mark
         * was already under the pointer and already about to move — and then
         * vanished a few pixels later, on a threshold nobody can see. Held is
         * the thing a person did; the drag is what they may or may not go on
         * to do with it.
         *
         * The fan's own mark and its immediate neighbours. Moving the mark
         * the fan is solved for pulls every stroke it stands on, and moving
         * the other endpoint of one of those strokes pulls the elbows off
         * the geometry they were solved for — so the fan comes down for the
         * gesture either way, and the draw after the drop re-solves it
         * fresh. A stranger's drag touches none of those strokes, so the fan
         * stands through it. `SPREAD_YIELDS_TO_HOLD` carries the scope.
         */
        /**
         * The owner's strokes, when it has any drawn. The owner can be a
         * bond — an edge, which this call refuses — or a mark not on the
         * field, and either way there is no neighbourhood to yield to: the
         * press falls back to owner-only scope rather than failing it.
         */
        let ownerStrokes: { source: unknown; target: unknown }[] = [];
        if (spreadOwnerRef.current) {
          try {
            ownerStrokes = graph.getRelatedEdgesData(spreadOwnerRef.current);
          } catch {
            ownerStrokes = [];
          }
        }
        if (
          spreadOwnerRef.current &&
          pressButton(event) !== 2 &&
          spreadYieldsToHold(
            SPREAD_YIELDS_TO_HOLD,
            spreadOwnerRef.current,
            id,
            ownerStrokes,
          )
        ) {
          spreadFieldRef.current?.suspend();
          spreadSuspendedRef.current = true;
        }
      }
    });
    graph.on("edge:pointerdown", (event) => {
      // Bonds carry no contact and no fan — a right press on one only removes
      // it. The label resolves to its mark the way the menu path reads it.
      if (pressButton(event) !== 2) return;
      const id = markOf(idOf(event));
      if (id) removeAtPress(pickEdge(id));
    });
    graph.on("node:click", (event) => {
      if (swallowReleaseClick()) return;
      const id = subject(idOf(event));
      if (!id) return;
      // Selecting opens this mark's own groups. A count opened somewhere else
      // was a question about a mark the person has now stopped asking about.
      setOpenedBundle(null);
      // The fan this press put down comes back as the new mark's, whichever
      // of this click and the window's release lands first — never the old
      // owner's for a frame.
      if (spreadOwnerRef.current && spreadOwnerRef.current !== id) {
        spreadOwnerRef.current = id;
        spreadFieldRef.current?.commit(id);
      }
      onSelectRef.current(pickNode(id));
    });
    graph.on("edge:click", (event) => {
      if (swallowReleaseClick()) return;
      const raw = idOf(event);
      if (!raw || draggingRef.current) return;
      if (subjectOfBundle(raw)) {
        // Reached only when G6's picker does deliver the click; the host-level
        // hit test above is what normally catches it. Same toggle either way.
        setOpenedBundle(openedBundleRef.current === raw ? null : raw);
        return;
      }
      const id = markOf(raw);
      if (!id) return;
      // Same flag as `clickLabel`: on the occasions G6's picker does deliver
      // a label click itself, it is still a canvas pick, not travel.
      labelPickRef.current = id;
      onSelectRef.current(pickEdge(id));
    });
    graph.on("canvas:click", () => {
      if (pressedLabel) return;
      if (swallowReleaseClick()) return;
      setOpenedBundle(null);
      onSelectRef.current(null);
    });
    graph.on("node:contextmenu", (event) => {
      swallowMenu(event);
      const id = subject(idOf(event));
      if (!id || recentlyRemoved(id)) return;
      /**
       * A menu with no press behind it — keyboard-emitted — removes at once,
       * the way a press does. Let go of the mark first: a press holds the draw
       * lane, which is right while a person is still deciding, and a removal
       * is the decision, so it has no claim on the frame that answers it.
       */
      releaseContact();
      onRemoveRef.current(pickNode(id));
    });
    graph.on("edge:contextmenu", (event) => {
      swallowMenu(event);
      const id = markOf(idOf(event));
      if (!id || recentlyRemoved(id)) return;
      releaseContact();
      onRemoveRef.current(pickEdge(id));
    });
    /** The mark under the pointer, kept because a lost release has no event. */
    let dragged: string | null = null;
    graph.on("node:dragstart", (event) => {
      draggingRef.current = true;
      const id = subject(idOf(event));
      // The fan is already down: `node:pointerdown` dropped it, because a
      // drag cannot begin without a hold. Re-solving it under a moving mark
      // would be both expensive and unreadable, which is why it stays down
      // until the pointer lets go.
      dragged = id;
      if (id) {
        physicsHeld = id;
        updateContact({ type: "drag", id });
        followFurniture(id);
        rideSettledDepth(id);
      }
      scheduleVisibility();
    });
    graph.on("node:drag", (event) => {
      const id = subject(idOf(event));
      if (!id) return;
      /**
       * A microtask behind the event, for the same reason the depth rides
       * one: the behavior translates after this listener runs — behaviors
       * bind when the graph initializes, after these listeners attached — so
       * a synchronous follow reads where the mark was, not where this move
       * put it, and the labels it lays out lag the line by a whole event.
       * The microtask drains before paint, so nothing ever shows the stale
       * frame. `dragstart` needs none of this: nothing has moved yet.
       */
      queueMicrotask(() => {
        if (graph.destroyed) return;
        followFurniture(id);
      });
      scheduleVisibility();
    });
    // Dragging is the one interaction that changes state the model owns, so it
    // is written back rather than left in the renderer to be lost on the next
    // expansion. The product canvas also swallows the click that fires after
    // a real drag, or the reader opens on a mark you were only moving.
    graph.on("node:dragend", (event) => {
      const id = subject(idOf(event)) ?? dragged;
      if (id) followFurniture(id);
      draggingRef.current = false;
      dragged = null;
      markReleaseClick();
      harvest(id ?? undefined);
      if (id) restatePendingDrag(id);
      // A press that went nowhere restacks nothing — see `restoreRestDepth`.
      // A moved mark's draw restates the depth the grab already rode.
      if (id && !dragMoved(id)) restoreRestDepth(id);
      releaseContact();
      physicsHeld = null;
      spreadSuspendedRef.current = false;
      /**
       * A drag that moved matter draws for it, and the draw's own commit
       * opens the fan fresh once the strokes have settled. Committing here
       * as well starts the reopen under that draw, which retargets it
       * mid-flight — the reopen's roughness against the collapse's ease. A
       * drag that went nowhere draws nothing, so it commits now.
       */
      if (!dragMoved(id)) {
        spreadFieldRef.current?.commit(spreadOwnerRef.current);
      }
      queueCanvasDraw();
      scheduleVisibility();
    });
    // Every camera move settles here; the recorder keeps only the settled,
    // person-moved camera — see `cameraMemory`.
    graph.on("aftertransform", () => recorderRef.current?.capture(graph));

    // G6 owns picking, but release belongs to the pointer even when it leaves
    // the canvas. A lost release would leave matter compressed indefinitely.
    const cancelPointer = () => {
      pressedLabel = false;
      const wasDragging = draggingRef.current;
      const id = dragged ?? physicsHeld;
      draggingRef.current = false;
      dragged = null;
      physicsHeld = null;
      spreadSuspendedRef.current = false;
      if (wasDragging) {
        harvest(id ?? undefined);
        if (id) restatePendingDrag(id);
        if (id && !dragMoved(id)) restoreRestDepth(id);
        // Same as `dragend`: a moved mark's draw reopens the fan.
        if (!dragMoved(id)) {
          spreadFieldRef.current?.commit(spreadOwnerRef.current);
        }
      }
      releaseContact();
      queueCanvasDraw();
      scheduleVisibility();
    };
    const releasePointer = () => {
      physicsHeld = null;
      releaseContact();
      // And it comes back on release, whether or not the hold ever became a
      // drag. A press that went nowhere put the fan down, so the same press
      // ending has to pick it back up — `dragend` cannot, because for a plain
      // click it never fires.
      if (spreadSuspendedRef.current) {
        spreadSuspendedRef.current = false;
        spreadFieldRef.current?.commit(spreadOwnerRef.current);
      }
    };
    window.addEventListener("pointerup", releasePointer);
    window.addEventListener("pointercancel", cancelPointer);
    window.addEventListener("blur", cancelPointer);

    void graph
      .render()
      .then(async () => {
        if (graphRef.current !== graph) return;
        if (!animateInitial && data.nodes.length) {
          if (data.nodes.length === 1) await graph.zoomTo(1, { duration: 0 });
        }
        // The canvas exists now, so the fan's frames have somewhere to be
        // announced on. Subscribed here rather than above — see
        // `spreadContainer`.
        spreadContainer = graph.getCanvas()?.getContainer() ?? null;
        spreadContainer?.addEventListener(SPREAD_FRAME_EVENT, scheduleVisibility);
        if (graphRef.current === graph) setReady(true);
      })
      .catch((problem: unknown) => {
        if (graphRef.current === graph) console.error(problem);
      });
    // A canvas has no DOM to address, so in development the field graph is
    // reachable for a browser-automated material check. This has its own name:
    // SchemaCanvas also exposes a graph, and a lab may mount both at once.
    if (import.meta.env.DEV) {
      (window as unknown as { __worldFieldGraph?: Graph }).__worldFieldGraph = graph;
    }
    return () => {
      host.removeEventListener("contextmenu", blockMenu);
      host.removeEventListener("pointerdown", clickLabel, true);
      host.removeEventListener("click", swallowLabelClick, true);
      window.removeEventListener("pointerup", releasePointer);
      window.removeEventListener("pointercancel", cancelPointer);
      window.removeEventListener("blur", cancelPointer);
      window.clearTimeout(releaseClickTimer);
      for (const running of runningContact.values()) {
        running.key?.cancel();
        running.label?.cancel();
      }
      runningContact.clear();
      window.clearTimeout(hoverStandDown.current);
      hoverStandDown.current = undefined;
      window.cancelAnimationFrame(visibilityFrame);
      visibilityFrame = 0;
      spreadContainer?.removeEventListener(SPREAD_FRAME_EVENT, scheduleVisibility);
      pendingFrameRef.current = null;
      authoredRef.current = null;
      spreadFieldRef.current?.dispose();
      spreadFieldRef.current = null;
      graphRef.current = null;
      setReady(false);
      if (
        (window as unknown as { __worldFieldGraph?: Graph }).__worldFieldGraph ===
        graph
      ) {
        delete (window as unknown as { __worldFieldGraph?: Graph })
          .__worldFieldGraph;
      }
      graph.destroy();
    };
    // The graph is created once. Data changes go through the effect below, so
    // an expansion never re-mounts the canvas and never resets the view.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (
      !ready ||
      !stageSize.width ||
      !stageSize.height ||
      !graphRef.current
    ) return;
    const arranged = arrangeToken !== drawnArrangeToken.current;
    drawnArrangeToken.current = arrangeToken;
    /**
     * A plate opens where its name stood.
     *
     * The store seats the fold on the line's midpoint, which is where the
     * name is until a fan carries it elsewhere — and the fan is renderer
     * state the store cannot see. So the canvas asks the bond still on the
     * graph where its name stands and seats the newborn plate there, once:
     * the plate is new to this frame and the last draw had no such mark.
     * An unreadable anchor, an occupied seat, or a plate that is not new
     * all keep the stored seat, which is the midpoint the fold always had.
     */
    let nodes = data.nodes as CanvasDatum[];
    const seed = foldSeed?.id ?? null;
    if (seed && !drawnFieldIds.current.has(seed)) {
      const plate = nodes.find((node) => node.id === seed);
      const graph = graphRef.current;
      const anchor = graph ? filamentLabelAnchor(graph, bondElementId(seed)) : null;
      if (anchor && plate?.style && plateSeatClear(set, anchor, seed)) {
        const x = Math.round(anchor.x);
        const y = Math.round(anchor.y);
        if (plate.style.x !== x || plate.style.y !== y) {
          nodes = nodes.map((node) =>
            node.id === seed ? { ...node, style: { ...node.style, x, y } } : node,
          );
        }
      }
    }
    pendingFrameRef.current = {
      nodes,
      edges: data.edges as CanvasDatum[],
      animateInitial,
      still,
      fieldIds: new Set([
        ...set.referents.keys(), ...set.assertions.keys(), ...set.demands.keys(),
      ]),
      arranged,
    };
    queueCanvasDraw();
    // `still` is read but not depended on: the release render carries no new
    // data, and a frame for it would overwrite the still bulk frame the pump
    // has not drawn yet — coalescing would un-still the run it ends.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    animateInitial,
    arrangeToken,
    data,
    foldSeed,
    queueCanvasDraw,
    ready,
    set,
    stageSize.height,
    stageSize.width,
  ]);

  // A renderer sized once is sized wrong the moment anything else on the page
  // takes room. The camera is left alone — resizing is not new matter.
  // Panel drags are the exception: the CSS grid follows the pointer, but G6
  // waits for pointer-up. Redrawing every move is both expensive and the
  // jitter. Existing marks stay put; there is no fitView here.
  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    return observeHostSize(host, (width, height) => {
      const graph = graphRef.current;
      if (!graph) return;
      graph.resize(width, height);
      setStageSize((current) =>
        current.width === width && current.height === height
          ? current
          : { width, height },
      );
    });
  }, []);

  /**
   * Nothing spreads that a person did not cause. The cause is a selection —
   * hover is not one, because a fan opening as the pointer passes over the
   * field would be the field moving under a pointer that is only looking.
   */
  useEffect(() => {
    if (!ready) return;
    if (!selection) {
      spreadOwnerRef.current = null;
      settledFanRef.current = null;
      labelPickRef.current = null;
      spreadFieldRef.current?.commit(null);
      return;
    }
    const settled = `${selection.kind}:${selection.id}`;
    if (settledFanRef.current === settled) {
      // Decided already: re-assert the standing owner so the lab switch
      // still takes — `commit` snaps shut or re-solves on its own — but
      // never re-decide for a selection that did not move.
      spreadFieldRef.current?.commit(spreadOwnerRef.current);
      return;
    }
    settledFanRef.current = settled;
    // Consumed, whatever it holds: a canvas label pick keeps the fan that
    // revealed it — see `spreadOwnerForSelection` — and anything else is
    // travel and takes ownership itself. A bond names an owner that stands
    // nowhere, which is already what closing looks like, and the outline
    // follows the retraction frame by frame off `SPREAD_FRAME_EVENT`, so
    // nothing strands.
    const canvasPick = labelPickRef.current;
    labelPickRef.current = null;
    // The set is read through the ref so a placement does not re-decide what
    // a selection already settled.
    const bond =
      setRef.current.bonds.find((item) => item.assertion_id === selection.id) ??
      null;
    spreadOwnerRef.current =
      canvasPick === selection.id
        ? spreadOwnerForSelection(selection.id, bond, spreadOwnerRef.current)
        : selection.id;
    spreadFieldRef.current?.commit(spreadOwnerRef.current);
  }, [ready, selection, spreadOnSelect]);

  useFocusPan(graphRef, ready, focusId, focusToken, insetsRef, holdCamera);

  return (
    <div
      className="world__stage"
      data-contact-phase={contact.phase}
      data-selection-treatment={selectionTreatment}
    >
      <div className="world__surface" ref={hostRef} />
      <SelectionAnts
        graph={ready ? graphRef.current : null}
        target={antTarget}
        clearance={tuning.clearance}
        dotGap={tuning.dotGap}
        lineWidth={tuning.lineWidth}
        speed={tuning.animated ? tuning.speed : 0}
        color={
          antTarget?.shape === "circle" &&
          selectionTreatment === "excited-boundary"
            ? paint.canvas
            : paint.ink
        }
        motion={motion}
        arrivalDelay={selectionArrivalDelay}
        animated={tuning.animated}
        held={contactId(contact) === selection?.id}
        traceToken={stationSubjects}
        gone={antsGone}
      />
    </div>
  );
}
