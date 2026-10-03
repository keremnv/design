import { test as base, expect, type Page, type Route } from "@playwright/test";
import type { Graph } from "@antv/g6";
import type { WorldAssertion, WorldRelation, WorldTuple } from "../src/api/world";

type CanvasWindow = Window & {
  __worldVocabulary: Graph;
  __worldFieldGraph: Graph;
};

type LabelShape = {
  style: { fillOpacity: number; opacity: number };
  getAnimations: () => { playState: string; effect: { getKeyframes: () => { fillOpacity: number }[] } }[];
};
const vocabularyText = (page: Page) => page.evaluate(() => {
  const graph = (window as unknown as CanvasWindow).__worldVocabulary;
  const text = (graph as unknown as {
    context: { element: { getElement: (id: string) => {
      getShape: (name: string) => { getShape: (name: string) => LabelShape };
    } } };
  })?.context?.element?.getElement("kind:entity")?.getShape("label")?.getShape("text");
  return Number(text?.style.fillOpacity);
});
type Field = {
  assertions: [string, unknown][];
  referents: [string, unknown][];
  bonds: { assertion_id: string }[];
};

function deferred() {
  let resolve!: () => void;
  const promise = new Promise<void>((done) => { resolve = done; });
  return { promise, resolve };
}

class FixtureWorld {
  count = 3;
  hub = false;
  binary = false;
  requests: URL[] = [];
  private blocked = new Map<string, {
    reached: ReturnType<typeof deferred>;
    released: ReturnType<typeof deferred>;
    status: number;
  }>();

  block(key: string, status = 200) {
    const gate = { reached: deferred(), released: deferred(), status };
    this.blocked.set(key, gate);
    return { requested: gate.reached.promise, release: gate.released.resolve };
  }

  releaseAll() {
    for (const gate of this.blocked.values()) gate.released.resolve();
  }

  get relation(): WorldRelation {
    return {
      name: "property", description: "Fixture property", mode: "BASE",
      arity: this.binary ? 3 : 2, referent_arity: this.binary ? 2 : 1,
      roles: [
        { name: "item", type: "REFERENT", referent: true, kinds: ["entity"] },
        ...(this.binary ? [{ name: "peer", type: "REFERENT", referent: true, kinds: ["entity"] }] : []),
        { name: "value", type: "TEXT", referent: false },
      ],
      count: this.count, stale: false, origins: ["SEMANTIC"],
      scope: "WORLD", completeness: null,
    };
  }

  tuples(): WorldTuple[] {
    return Array.from({ length: this.count }, (_, i) => ({
      assertion_id: `assertion:${i}`, origin: "SEMANTIC", origins: ["SEMANTIC"],
      values: { item: `entity:${this.hub ? 0 : i}`, value: `value-${i}`,
        ...(this.binary ? { peer: `entity:${i + 1}` } : {}) },
    }));
  }

  async respond(route: Route) {
    const url = new URL(route.request().url());
    if (!url.pathname.startsWith("/world/")) return route.continue();
    this.requests.push(url);
    const name = url.pathname.slice("/world/".length);
    const id = url.searchParams.get("id") ?? "";
    const offset = Number(url.searchParams.get("offset") ?? 0);
    const key = name === "rows" ? `rows:${offset}` : `${name}${id ? `:${id}` : ""}`;
    const gate = this.blocked.get(key);
    if (gate) {
      gate.reached.resolve();
      await gate.released.promise;
      this.blocked.delete(key);
      if (gate.status !== 200) return route.fulfill({ status: gate.status, json: { error: "Fixture read failed" } });
    }
    let answer: unknown;
    switch (name) {
      case "overview":
        answer = {
          world_id: "review", revision: 1, relations: 1, referents: this.count + 1,
          assertions: this.count, origins: { SEMANTIC: this.count }, stale: [], incomplete: [],
          demand: { purpose: { statement: "fixture" }, obligations: 0, demanded: 0 },
          governed_obligations: { count: 0, resolved: 0, unresolved: 0 },
        };
        break;
      case "schema": answer = { relations: [this.relation] }; break;
      case "referents":
        answer = { referents: Array.from({ length: this.count + 1 }, (_, i) => ({
          id: `entity:${i}`, label: `Entity ${i}`,
        })), total: this.count + 1, truncated: false };
        break;
      case "rows": {
        const subject = url.searchParams.get("subject");
        const rows = this.tuples().filter((tuple) => !subject || Object.values(tuple.values).includes(subject));
        answer = { relation: "property", mode: "BASE", stale: false, roles: this.relation.roles,
          offset, total: rows.length, rows: rows.slice(offset, offset + Number(url.searchParams.get("limit") ?? 200)) };
        break;
      }
      case "assertion": {
        const tuple = this.tuples().find((item) => item.assertion_id === id)!;
        answer = {
          ...tuple, relation: "property", mode: "BASE", arity: this.relation.arity, roles: this.relation.roles,
          assertion_state: "ASSERTED", created_revision: 1, relation_stale: false,
          completeness: null, grounding: [], commitment_id: id, candidate_for: [],
          governing_obligations: [], candidate_assessments: [],
          warrant: { commitment_id: id, relation: "property", assertion_origin: "SEMANTIC",
            recorded_construction_origin: "SEMANTIC", construction_origins: ["SEMANTIC"],
            created_revision: 1, bases: [] },
        } satisfies WorldAssertion;
        break;
      }
      case "referent":
        // Entity 0 carries one fact from a tuple never placed, so the
        // reader's back-link reads past the field.
        answer = { id, label: `Entity ${id.split(":")[1]}`, grounding: [],
          fields: id === "entity:0"
            ? [{ relation: "property", role: "value", value: "value-7",
                assertion_id: "assertion:7", origin: "SEMANTIC" }]
            : [],
          relations: [{ name: "property", arity: this.relation.arity, mode: "BASE", stale: false,
            count: this.tuples().filter((tuple) => Object.values(tuple.values).includes(id)).length }] };
        break;
      case "demand": answer = { demand: {
        purpose: { statement: "fixture" }, rule: null, demanded: 0, obligations: [],
      } }; break;
      case "obligations": answer = { obligations: [] }; break;
      default: throw new Error(`Unexpected fixture read: ${url}`);
    }
    return route.fulfill({ json: answer });
  }
}

const test = base.extend<{ world: FixtureWorld }>({
  world: async ({ page }, use) => {
    const world = new FixtureWorld();
    await page.route("**/world/**", (route) => world.respond(route));
    try { await use(world); } finally { world.releaseAll(); }
  },
});

const reader = (page: Page) => page.locator(".node-reader .motion-swap__is");
const rows = (page: Page) => page.locator(".table__row[data-loaded]");
const field = (page: Page) => page.evaluate(() =>
  JSON.parse(localStorage.getItem("worldir.field:review:1") ?? "null") as Field | null);

async function openProperty(page: Page) {
  await page.goto("/");
  await page.locator(".table__row").filter({ has: page.locator('[title="property"]') }).click();
  await expect(rows(page).first()).toBeVisible();
}

async function readRow(page: Page, index: number) {
  await rows(page).nth(index).click();
  await expect(reader(page)).toContainText(`value-${index}`);
}

async function selectReferent(page: Page, id: string) {
  await page.evaluate((id) => {
    (window as unknown as CanvasWindow).__worldFieldGraph.emit("node:click", { target: { id } });
  }, id);
}

for (const motion of ["reduce", "no-preference"] as const) {
  test(`a small vocabulary is visible with ${motion} motion`, async ({ page, world }) => {
    world.count = 1;
    await page.emulateMedia({ reducedMotion: motion });
    await page.goto("/");
    const camera = () => page.evaluate(() => {
      const graph = (window as unknown as CanvasWindow).__worldVocabulary;
      if (!graph?.getNodeData().length) return false;
      const [x, y] = graph.getViewportByCanvas(graph.getElementPosition("kind:entity"));
      return x > 450 && x < 1350 && y > 150 && y < 850 && graph.getZoom() <= 2;
    });
    await expect.poll(camera).toBe(true);
    // A user reframe uses the same bounded placement, including after panning.
    await page.evaluate(async () => {
      const graph = (window as unknown as CanvasWindow).__worldVocabulary;
      await graph.translateBy([0, -1500], false);
    });
    await expect.poll(camera).toBe(false);
    await page.evaluate(() => {
      (window as unknown as CanvasWindow).__worldVocabulary.emit("canvas:dblclick", {});
    });
    await expect.poll(camera).toBe(true);
  });
}

test("text strength fades from its painted value, including an interrupted recovery", async ({ page, world }) => {
  world.count = 1;
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.goto("/");
  await expect.poll(() => vocabularyText(page)).toBe(0.85);
  // Let establishment finish before probing the painter independently of
  // the initial lifecycle's own reconciliation of authored label styles.
  await expect.poll(() => page.evaluate(() => {
    const graph = (window as unknown as CanvasWindow).__worldVocabulary;
    return graph.getViewportByCanvas(graph.getElementPosition("kind:entity"))[1];
  })).toBeCloseTo(499.99, 2);
  const paint = async (to: number, animate = true) => page.evaluate(async ({ to, animate }) => {
    const motionPath = "/src/styles/motion.ts";
    const painterPath = "/src/world/canvasMotion.ts";
    const { DEFAULT_MOTION_PLANS } = await import(motionPath);
    const { paintLabelStrength } = await import(painterPath);
    const graph = (window as unknown as CanvasWindow).__worldVocabulary;
    const text = (graph as unknown as {
      context: { element: { getElement: (id: string) => {
        getShape: (name: string) => { getShape: (name: string) => LabelShape };
      } } };
    }).context.element.getElement("kind:entity").getShape("label").getShape("text");
    const before = Number(text.style.fillOpacity);
    // The previous target can differ from the value currently being painted.
    paintLabelStrength(graph, [{ id: "kind:entity", from: 0.85, to }], animate ? {
      weakenPlan: DEFAULT_MOTION_PLANS.absorb, restorePlan: DEFAULT_MOTION_PLANS.emit,
    } : {});
    const running = text.getAnimations().find((animation) => animation.playState === "running" &&
      animation.effect.getKeyframes().some((frame) => typeof frame.fillOpacity === "number"));
    return { before, after: Number(text.style.fillOpacity), frames: running?.effect.getKeyframes() };
  }, { to, animate });
  const yielding = await paint(0.25);
  expect(yielding.frames?.map((frame) => frame.fillOpacity)).toEqual([0.85, 0.25]);
  expect(yielding.after).toBe(0.85);
  await expect.poll(async () => (await vocabularyText(page)) < 0.84).toBe(true);
  const recovering = await paint(0.85);
  expect(recovering.frames?.[0].fillOpacity).toBe(recovering.before);
  expect(recovering.frames?.[1].fillOpacity).toBe(0.85);
  expect(recovering.after).toBe(recovering.before);
  await expect.poll(() => vocabularyText(page)).toBe(0.85);
  await paint(0.25);
  // Switching to reduced motion must cancel a running fade as well as snap.
  const reduced = await paint(0.6, false);
  expect(reduced.after).toBe(0.6);
  expect(reduced.frames).toBeUndefined();
  await expect.poll(() => vocabularyText(page)).toBe(0.6);
});

test("the field paints partial crowding and recovers without changing mark opacity", async ({ page, world }, testInfo) => {
  world.count = 2;
  await openProperty(page);
  await readRow(page, 0);
  await readRow(page, 1);
  await reader(page).locator(".world__roles button").click();
  await expect(reader(page).locator("h2")).toHaveText("Entity 1");
  const place = async (crowded: boolean) => page.evaluate(async (crowded) => {
    const visibilityPath = "/src/world/visibility.ts";
    const { paintedLabelBox } = await import(visibilityPath);
    const graph = (window as unknown as CanvasWindow).__worldFieldGraph;
    const a = paintedLabelBox(graph, "entity:0")!;
    const b = paintedLabelBox(graph, "entity:1")!;
    const [x, y] = graph.getElementPosition("entity:0");
    graph.emit("node:dragstart", { target: { id: "entity:0" } });
    await graph.translateElementTo("entity:0", [
      x + b.minX + (crowded ? (a.maxX - a.minX) * 0.7 : 200) - a.minX,
      y + b.minY - a.minY,
    ], false);
    graph.emit("node:dragend", { target: { id: "entity:0" } });
    graph.getCanvas().getContainer()?.dispatchEvent(new Event("world:spreadframe"));
  }, crowded);
  const strengths = () => page.evaluate(() => {
    const graph = (window as unknown as CanvasWindow).__worldFieldGraph;
    return ["entity:0", "entity:1"].map((id) => graph.getNodeData(id).style!);
  });
  const before = await strengths();
  await place(true);
  await expect.poll(async () => {
    const [yielding, selected] = await strengths();
    return Number(yielding.labelFillOpacity) < Number(before[0].labelFillOpacity) &&
      Number(yielding.labelFillOpacity) > Number(before[0].labelFillOpacity) * 0.25 &&
      selected.labelFillOpacity === before[1].labelFillOpacity;
  }).toBe(true);
  expect((await strengths())[0]).toMatchObject({ opacity: before[0].opacity, fillOpacity: before[0].fillOpacity });
  await page.screenshot({ path: testInfo.outputPath("partial-crowding.png") });
  await place(false);
  await expect.poll(async () => (await strengths())[0].labelFillOpacity).toBe(before[0].labelFillOpacity);
});

for (const canvas of ["field", "vocabulary"] as const) {
  test(`${canvas} text follows crowding before a drag is released`, async ({ page, world }) => {
    world.count = 2;
    world.binary = canvas === "vocabulary";
    if (canvas === "field") {
      await openProperty(page);
      await readRow(page, 0);
      await readRow(page, 1);
      await reader(page).locator(".world__roles button").click();
      await expect(reader(page).locator("h2")).toHaveText("Entity 1");
    } else {
      await page.goto("/");
      await expect.poll(() => vocabularyText(page)).toBe(0.85);
      await page.evaluate(() => {
        (window as unknown as CanvasWindow).__worldVocabulary.emit("node:click", { target: { id: "rel:property" } });
      });
      await expect(reader(page).locator("h2")).toHaveText("property");
    }
    const ids = canvas === "field" ? ["entity:0", "entity:1"] : ["kind:entity", "rel:property"];
    // Establish the scene without lifecycle travel, then exercise the gesture
    // with ordinary motion enabled.
    await expect.poll(() => page.evaluate(({ canvas, ids }) => {
      const graph = (window as unknown as CanvasWindow)[canvas === "field" ? "__worldFieldGraph" : "__worldVocabulary"];
      return ids.every((id) => graph?.getNodeData(id)?.style &&
        Number(graph.getNodeData(id).style!.labelOpacity ?? 1) > 0);
    }, { canvas, ids })).toBe(true);
    await page.emulateMedia({ reducedMotion: "no-preference" });
    const sample = () => page.evaluate(({ canvas, ids }) => {
      const graph = (window as unknown as CanvasWindow)[canvas === "field" ? "__worldFieldGraph" : "__worldVocabulary"];
      const shape = (graph as unknown as {
        context: { element: { getElement: (id: string) => {
          getShape: (name: string) => { getShape: (name: string) => LabelShape };
        } } };
      }).context.element.getElement(ids[0]).getShape("label").getShape("text");
      return {
        painted: Number(shape.style.fillOpacity),
        target: Number(graph.getNodeData(ids[0]).style!.labelFillOpacity),
        selected: Number(graph.getNodeData(ids[1]).style!.labelFillOpacity),
        fading: shape.getAnimations().some((animation) => animation.playState === "running" &&
          animation.effect.getKeyframes().some((frame) => typeof frame.fillOpacity === "number")),
      };
    }, { canvas, ids });
    const before = await sample();
    const move = async (coverage: number, start = false) => page.evaluate(async ({ canvas, ids, coverage, start }) => {
      const visibilityPath = "/src/world/visibility.ts";
      const { paintedLabelBox } = await import(visibilityPath);
      const graph = (window as unknown as CanvasWindow)[canvas === "field" ? "__worldFieldGraph" : "__worldVocabulary"];
      if (start) graph.emit("node:dragstart", { target: { id: ids[0] } });
      const a = paintedLabelBox(graph, ids[0])!;
      const b = paintedLabelBox(graph, ids[1])!;
      const [x, y] = graph.getElementPosition(ids[0]);
      const destination = [
        x + b.minX + (a.maxX - a.minX) * (1 - coverage) - a.minX,
        y + b.minY - a.minY,
      ] as [number, number];
      // Feed the same deltas G6 receives from a pointer, so its native drag
      // behavior moves the mark and the visibility listener observes it.
      graph.emit("node:drag", {
        target: { id: ids[0] },
        dx: (destination[0] - x) * graph.getZoom(),
        dy: (destination[1] - y) * graph.getZoom(),
      });
      // Observe live paint within two frames, while the drag is still held.
      await new Promise<void>((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve())));
      return { destination, position: graph.getElementPosition(ids[0]).slice(0, 2) };
    }, { canvas, ids, coverage, start });
    const moved = await move(0.3, true);
    expect(moved.position[0]).toBeCloseTo(moved.destination[0], 6);
    expect(moved.position[1]).toBeCloseTo(moved.destination[1], 6);
    const partial = await sample();
    expect(partial.target).toBeLessThan(before.target);
    expect(partial.target).toBeGreaterThan(before.target * 0.25);
    expect(partial.painted).toBeCloseTo(partial.target, 6);
    expect(partial.fading).toBe(false);
    expect(partial.selected).toBe(before.selected);
    await move(0.55);
    const crowded = await sample();
    expect(crowded.painted).toBeLessThan(partial.painted);
    expect(crowded.painted).toBeCloseTo(crowded.target, 6);
    await move(-2);
    const clear = await sample();
    expect(clear.painted).toBe(before.target);
    expect(clear.fading).toBe(false);
    await page.evaluate(({ canvas, ids }) => {
      const graph = (window as unknown as CanvasWindow)[canvas === "field" ? "__worldFieldGraph" : "__worldVocabulary"];
      graph.emit("node:dragend", { target: { id: ids[0] } });
    }, { canvas, ids });
    await expect.poll(async () => (await sample()).painted).toBe(before.target);
  });
}

test("an assertion stays readable until its replacement arrives", async ({ page, world }) => {
  await openProperty(page);
  await readRow(page, 0);
  const gate = world.block("assertion:assertion:1");
  await rows(page).nth(1).click();
  await gate.requested;
  await expect(reader(page)).toContainText("value-0");
  await expect(reader(page)).not.toContainText("Reading assertion");
  gate.release();
  await expect(reader(page)).toContainText("value-1");
});

test("a referent stays readable until its replacement arrives", async ({ page, world }) => {
  await openProperty(page);
  await readRow(page, 0);
  await readRow(page, 1);
  await reader(page).locator(".world__roles button").click();
  await expect(reader(page).locator("h2")).toHaveText("Entity 1");
  const gate = world.block("referent:entity:0");
  await selectReferent(page, "entity:0");
  await gate.requested;
  await expect(reader(page).locator("h2")).toHaveText("Entity 1");
  gate.release();
  await expect(reader(page).locator("h2")).toHaveText("Entity 0");
});

test("a retained assertion's remove button leaves the newly selected referent", async ({ page, world }) => {
  await openProperty(page);
  await readRow(page, 0);
  const gate = world.block("referent:entity:0");
  await reader(page).locator(".world__roles button").click();
  await gate.requested;
  await reader(page).getByRole("button", { name: "Take off the field", exact: true }).click();
  await expect.poll(async () => (await field(page))?.assertions.length).toBe(0);
  expect((await field(page))?.referents.map(([id]) => id)).toEqual(["entity:0"]);
  gate.release();
  await expect(reader(page).locator("h2")).toHaveText("Entity 0");
});

test("a retained assertion can still open its own bond", async ({ page, world }) => {
  world.binary = true;
  await openProperty(page);
  await readRow(page, 0);
  const gate = world.block("referent:entity:0");
  await reader(page).locator(".world__roles button").first().click();
  await gate.requested;
  await reader(page).getByRole("button", { name: "Open on the field", exact: true }).click();
  await expect.poll(async () => (await field(page))?.assertions.map(([id]) => id)).toEqual(["assertion:0"]);
  expect((await field(page))?.bonds).toHaveLength(0);
  gate.release();
});

test("a retained referent expands and retracts its own neighborhood", async ({ page, world }) => {
  world.binary = true;
  world.hub = true;
  await openProperty(page);
  await readRow(page, 0);
  await reader(page).locator(".world__roles button").first().click();
  await expect(reader(page).locator("h2")).toHaveText("Entity 0");
  const gate = world.block("referent:entity:1");
  await selectReferent(page, "entity:1");
  await gate.requested;
  const expand = reader(page).locator(".gm__list button").filter({ hasText: "property" }).first();
  const claims = async () => {
    const current = await field(page);
    return (current?.assertions.length ?? 0) + (current?.bonds.length ?? 0);
  };
  await expand.click();
  await expect.poll(claims).toBe(3);
  expect(world.requests.filter((url) => url.pathname === "/world/rows" && url.searchParams.has("subject"))
    .map((url) => url.searchParams.get("subject"))).toEqual(["entity:0"]);
  await expect(expand).toContainText("take off");
  await expand.click();
  await expect.poll(claims).toBe(0);
  gate.release();
  await expect(reader(page).locator("h2")).toHaveText("Entity 1");
});

test("a failed replacement shows its error rather than the previous claim", async ({ page, world }) => {
  await openProperty(page);
  await readRow(page, 0);
  const gate = world.block("assertion:assertion:1", 500);
  await rows(page).nth(1).click();
  await gate.requested;
  await expect(reader(page)).toContainText("value-0");
  gate.release();
  await expect(reader(page).getByRole("alert")).toBeVisible();
  await expect(reader(page)).not.toContainText("value-0");
});

test("frontier reads settle after selection and table changes", async ({ page, world }) => {
  await openProperty(page);
  await readRow(page, 0);
  const demand = world.block("demand");
  const obligations = world.block("obligations");
  await page.getByRole("button", { name: "purpose frontier", exact: true }).first().click();
  await Promise.all([demand.requested, obligations.requested]);
  await selectReferent(page, "entity:0");
  await page.getByRole("button", { name: "obligations", exact: true }).first().click();
  demand.release();
  obligations.release();
  await expect(page.locator(".table__meta").first()).toContainText("0 governed obligations");
  await page.getByRole("button", { name: "purpose frontier", exact: true }).first().click();
  await expect(page.locator(".table__meta").first()).toContainText("0 unresolved of 0 obligations");
  await expect(page.locator(".table__meta").first()).not.toContainText("Reading");
  expect(world.requests.filter((url) => url.pathname === "/world/demand")).toHaveLength(1);
  expect(world.requests.filter((url) => url.pathname === "/world/obligations")).toHaveLength(1);
});

test("expansion reads every page and can retract the whole neighborhood", async ({ page, world }) => {
  world.count = 250;
  world.hub = true;
  await openProperty(page);
  await readRow(page, 0);
  await reader(page).locator(".world__roles button").click();
  const expand = reader(page).locator(".gm__list button").filter({ hasText: "property" }).first();
  await expand.click();
  await expect.poll(async () => (await field(page))?.assertions.length).toBe(250);
  await expect(expand).toContainText("take off");
  const offsets = world.requests.filter((url) => url.pathname === "/world/rows" && url.searchParams.get("subject") === "entity:0")
    .map((url) => Number(url.searchParams.get("offset")));
  expect(offsets).toEqual([0, 200]);
  await expand.click();
  await expect.poll(async () => (await field(page))?.assertions.length).toBe(0);
});

test("a failed expansion page retains its earlier page and retries", async ({ page, world }) => {
  world.count = 250;
  world.hub = true;
  await openProperty(page);
  await readRow(page, 0);
  await reader(page).locator(".world__roles button").click();
  const gate = world.block("rows:200", 500);
  const expand = reader(page).locator(".gm__list button").filter({ hasText: "property" }).first();
  await expand.click();
  await gate.requested;
  await expect.poll(async () => (await field(page))?.assertions.length).toBe(200);
  gate.release();
  await expect(expand).toContainText("retry");
  await expand.click();
  await expect.poll(async () => (await field(page))?.assertions.length).toBe(250);
});

test("removing an expansion's anchor discards its outstanding page", async ({ page, world }) => {
  world.count = 250;
  world.hub = true;
  await openProperty(page);
  await readRow(page, 0);
  await reader(page).locator(".world__roles button").click();
  const gate = world.block("rows:200");
  await reader(page).locator(".gm__list button").filter({ hasText: "property" }).first().click();
  await gate.requested;
  await reader(page).getByRole("button", { name: "Take off the field", exact: true }).click();
  gate.release();
  await expect.poll(() => field(page)).toBeNull();
  await page.getByRole("button", { name: "world", exact: true }).first().click();
  await expect(page.locator(".table__row").first()).not.toHaveAttribute("data-present", "true");
});

/* ------------------------------------------------------------------ *
 * Drag-depth silence: the gesture shows the settled state
 * ------------------------------------------------------------------ *
 * A drop restacks its mark to the front of the depth stack, so the grab
 * carries that depth for the whole gesture: G6 fronts the held mark for
 * the drag and the release redraw must restate identical numbers, or the
 * mark visibly sinks a layer on release. Incident labels likewise track
 * the line live and must not jump once the pointer lets go.
 */

type DragSample = {
  z: number;
  pos: [number, number];
  boxes: Record<string, [number, number] | null>;
};

async function dragSample(page: Page, id: string): Promise<DragSample> {
  return page.evaluate(async ({ id, readerPath }) => {
    const graph = (window as unknown as CanvasWindow).__worldFieldGraph;
    const { paintedLabelBox } = await import(readerPath);
    const boxes: Record<string, [number, number] | null> = {};
    for (const edge of graph.getRelatedEdgesData(id)) {
      const style = (edge.style ?? {}) as Record<string, unknown>;
      if (typeof style.labelText !== "string" || !style.labelText) continue;
      const box = paintedLabelBox(graph, String(edge.id)) as {
        minX: number; minY: number; maxX: number; maxY: number;
      } | null;
      boxes[String(edge.id)] = box
        ? [(box.minX + box.maxX) / 2, (box.minY + box.maxY) / 2]
        : null;
    }
    const at = graph.getElementPosition(id);
    return {
      z: Number(graph.getNodeData(id).style?.zIndex),
      pos: [Number(at?.[0]), Number(at?.[1])] as [number, number],
      boxes,
    };
  }, { id, readerPath: "/src/world/visibility.ts" });
}

async function settleFrames(page: Page, count = 3) {
  await page.evaluate((count) => new Promise<void>((done) => {
    const step = () => {
      count -= 1;
      if (count <= 0) done();
      else requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }), count);
}

async function emitField(page: Page, type: string, id: string, extra: Record<string, unknown> = {}) {
  await page.evaluate(({ type, id, extra }) => {
    const graph = (window as unknown as CanvasWindow).__worldFieldGraph;
    graph.emit(type, { target: { id }, ...extra });
  }, { type, id, extra });
}

/** How many of this mark's strokes are standing bent, read off the renderer. */
async function fannedStrokes(page: Page, id: string): Promise<number> {
  return page.evaluate((id) => {
    const graph = (window as unknown as CanvasWindow).__worldFieldGraph;
    const elements = (graph as unknown as {
      context: { element: { getElement: (edgeId: string) => {
        hasFan?: (fan: null) => boolean;
      } | undefined } };
    }).context.element;
    let open = 0;
    for (const edge of graph.getRelatedEdgesData(id)) {
      const rendered = elements.getElement(String(edge.id));
      if (rendered && typeof rendered.hasFan === "function" && !rendered.hasFan(null)) {
        open += 1;
      }
    }
    return open;
  }, id);
}

async function labeledIncidentCount(page: Page, id: string): Promise<number> {
  return page.evaluate((id) => {
    const graph = (window as unknown as CanvasWindow).__worldFieldGraph;
    return graph.getRelatedEdgesData(id).filter((edge) => {
      const style = (edge.style ?? {}) as Record<string, unknown>;
      return typeof style.labelText === "string" && style.labelText.length > 0;
    }).length;
  }, id);
}

async function gotoWithSpread(page: Page, spread: boolean) {
  await page.goto("/");
  if (spread) return;
  // The menu persists per world, so seed it off and reload rather than
  // fighting the hover-gated toggle. Seeded from what the app itself wrote,
  // so no defaults are guessed here.
  await expect.poll(() => page.evaluate(
    () => localStorage.getItem("worldir.show:review"),
  )).not.toBeNull();
  await page.evaluate(() => {
    const raw = localStorage.getItem("worldir.show:review")!;
    localStorage.setItem("worldir.show:review", JSON.stringify({
      ...JSON.parse(raw), spreadOnSelect: false,
    }));
  });
  await page.reload();
}

async function openPropertyTable(page: Page) {
  await page.locator(".table__row").filter({ has: page.locator('[title="property"]') }).click();
  await expect(rows(page).first()).toBeVisible();
}

/** The drop's draw has landed once the store agrees with the renderer. */
async function awaitDropDraw(page: Page, id: string) {
  await expect.poll(() => page.evaluate((id) => {
    const graph = (window as unknown as CanvasWindow).__worldFieldGraph;
    const node = graph.getNodeData(id);
    const at = graph.getElementPosition(id);
    return Math.abs(Number(node.style?.x) - Number(at?.[0])) < 1 &&
      Math.abs(Number(node.style?.y) - Number(at?.[1])) < 1;
  }, id)).toBe(true);
}

function expectBoxesSettled(before: DragSample, after: DragSample) {
  let compared = 0;
  for (const [id, pre] of Object.entries(before.boxes)) {
    const post = after.boxes[id];
    if (!pre || !post) continue;
    compared += 1;
    expect(
      Math.hypot(post[0] - pre[0], post[1] - pre[1]),
      `label ${id} moved after release`,
    ).toBeLessThanOrEqual(0.5);
  }
  expect(compared, "no incident label was readable in both samples").toBeGreaterThan(0);
}

test("a dragged mark keeps its settled depth from grab through release", async ({ page, world }) => {
  world.count = 3;
  world.binary = true;
  await page.goto("/");
  await openPropertyTable(page);
  await readRow(page, 0);
  await readRow(page, 1);
  await readRow(page, 2);
  await selectReferent(page, "entity:0");
  await expect(reader(page).locator("h2")).toHaveText("Entity 0");
  await expect.poll(() => labeledIncidentCount(page, "entity:0")).toBeGreaterThan(0);
  const rest = await dragSample(page, "entity:0");
  await emitField(page, "node:pointerdown", "entity:0");
  await settleFrames(page);
  await emitField(page, "node:dragstart", "entity:0");
  await settleFrames(page);
  const grabbed = await dragSample(page, "entity:0");
  const zoom = await page.evaluate(
    () => (window as unknown as CanvasWindow).__worldFieldGraph.getZoom(),
  );
  await emitField(page, "node:drag", "entity:0", { dx: 120 * zoom, dy: 60 * zoom });
  await settleFrames(page);
  const mid = await dragSample(page, "entity:0");
  expect(
    Math.hypot(mid.pos[0] - rest.pos[0], mid.pos[1] - rest.pos[1]),
    "the drag did not move its mark",
  ).toBeGreaterThan(50);
  await emitField(page, "node:dragend", "entity:0");
  await awaitDropDraw(page, "entity:0");
  await page.waitForTimeout(500);
  const settled = await dragSample(page, "entity:0");
  // The drop restacked, so flatness below is earned rather than vacuous.
  expect(settled.z).toBeGreaterThan(rest.z);
  expect(grabbed.z).toBe(settled.z);
  expect(mid.z).toBe(settled.z);
  expectBoxesSettled(mid, settled);
});

test("a press that goes nowhere keeps its rest depth", async ({ page, world }) => {
  world.count = 3;
  world.binary = true;
  await page.goto("/");
  await openPropertyTable(page);
  await readRow(page, 0);
  await readRow(page, 1);
  await readRow(page, 2);
  await selectReferent(page, "entity:0");
  await expect(reader(page).locator("h2")).toHaveText("Entity 0");
  await expect.poll(() => labeledIncidentCount(page, "entity:0")).toBeGreaterThan(0);
  const rest = await dragSample(page, "entity:0");
  await emitField(page, "node:pointerdown", "entity:0");
  await emitField(page, "node:dragstart", "entity:0");
  await settleFrames(page);
  await emitField(page, "node:dragend", "entity:0");
  await settleFrames(page, 5);
  const settled = await dragSample(page, "entity:0");
  expect(settled.pos).toEqual(rest.pos);
  expect(settled.z).toBe(rest.z);
});

async function buildHubField(page: Page) {
  await readRow(page, 0);
  await reader(page).locator(".world__roles button").first().click();
  await expect(reader(page).locator("h2")).toHaveText("Entity 0");
  const expand = reader(page).locator(".gm__list button").filter({ hasText: "property" }).first();
  await expand.click();
  await expect.poll(async () => {
    const current = await field(page);
    return (current?.assertions.length ?? 0) + (current?.bonds.length ?? 0);
  }).toBe(12);
  await selectReferent(page, "entity:0");
  await expect.poll(() => page.evaluate(() => {
    const graph = (window as unknown as CanvasWindow).__worldFieldGraph;
    return graph.getRelatedEdgesData("entity:0").length;
  })).toBeGreaterThanOrEqual(12);
}

/**
 * Pile two names onto one station so the fan has a collision to solve.
 * Placement spreads bonds too evenly to collide on their own, so one mark
 * is dragged to its sibling's doorstep first, as seen from their hub.
 */
async function crowdBonds(
  page: Page,
  hub = "entity:0",
  move = "entity:1",
  beside = "entity:2",
) {
  // Placement draws land behind the reads that placed them.
  await expect.poll(() => page.evaluate(({ hub, move, beside }) => {
    const graph = (window as unknown as CanvasWindow).__worldFieldGraph;
    return [hub, move, beside].every((id) => {
      try {
        const at = graph.getElementPosition(id);
        return !!at && Number.isFinite(Number(at[0])) && Number.isFinite(Number(at[1]));
      } catch {
        return false;
      }
    });
  }, { hub, move, beside })).toBe(true);
  const job = await page.evaluate(({ hub, move, beside }) => {
    const graph = (window as unknown as CanvasWindow).__worldFieldGraph;
    const at = (id: string) => graph.getElementPosition(id);
    const hubAt = at(hub);
    const besideAt = at(beside);
    const fromAt = at(move);
    const dx = Number(besideAt[0]) - Number(hubAt[0]);
    const dy = Number(besideAt[1]) - Number(hubAt[1]);
    const len = Math.hypot(dx, dy) || 1;
    return {
      dx: (Number(besideAt[0]) - Number(fromAt[0]) + (-dy / len) * 8) * graph.getZoom(),
      dy: (Number(besideAt[1]) - Number(fromAt[1]) + (dx / len) * 8) * graph.getZoom(),
    };
  }, { hub, move, beside });
  await emitField(page, "node:pointerdown", move);
  await emitField(page, "node:dragstart", move);
  await emitField(page, "node:drag", move, { dx: job.dx, dy: job.dy });
  await settleFrames(page);
  await emitField(page, "node:dragend", move);
  await awaitDropDraw(page, move);
}

async function dragHub(page: Page) {
  const rest = await dragSample(page, "entity:0");
  await emitField(page, "node:pointerdown", "entity:0");
  await settleFrames(page);
  await emitField(page, "node:dragstart", "entity:0");
  await settleFrames(page);
  const grabbed = await dragSample(page, "entity:0");
  const zoom = await page.evaluate(
    () => (window as unknown as CanvasWindow).__worldFieldGraph.getZoom(),
  );
  await emitField(page, "node:drag", "entity:0", { dx: 120 * zoom, dy: 60 * zoom });
  await settleFrames(page);
  const mid = await dragSample(page, "entity:0");
  expect(
    Math.hypot(mid.pos[0] - rest.pos[0], mid.pos[1] - rest.pos[1]),
    "the drag did not move its mark",
  ).toBeGreaterThan(50);
  return { rest, grabbed, mid };
}

test("a dense-field drag release moves no label with the fan off", async ({ page, world }) => {
  world.count = 12;
  world.hub = true;
  world.binary = true;
  await gotoWithSpread(page, false);
  await openPropertyTable(page);
  await buildHubField(page);
  await expect.poll(() => fannedStrokes(page, "entity:0")).toBe(0);
  await expect.poll(() => labeledIncidentCount(page, "entity:0")).toBeGreaterThan(0);
  const { rest, grabbed, mid } = await dragHub(page);
  await emitField(page, "node:dragend", "entity:0");
  await awaitDropDraw(page, "entity:0");
  await page.waitForTimeout(500);
  const settled = await dragSample(page, "entity:0");
  expect(settled.z).toBeGreaterThan(rest.z);
  expect(grabbed.z).toBe(settled.z);
  expect(mid.z).toBe(settled.z);
  expectBoxesSettled(mid, settled);
});

test("a dense-field drag keeps its settled depth with the fan on", async ({ page, world }) => {
  world.count = 12;
  world.hub = true;
  world.binary = true;
  await gotoWithSpread(page, true);
  await openPropertyTable(page);
  await buildHubField(page);
  await crowdBonds(page);
  // The fan is genuinely open: this is the dense reopen case, not chords.
  await expect.poll(() => fannedStrokes(page, "entity:0")).toBeGreaterThan(0);
  const { rest, grabbed, mid } = await dragHub(page);
  // The owner's press put the fan down for the gesture.
  expect(await fannedStrokes(page, "entity:0")).toBe(0);
  await emitField(page, "node:dragend", "entity:0");
  await awaitDropDraw(page, "entity:0");
  const track: { at: string; sample: DragSample }[] = [];
  for (const [at, wait] of [["rel30", 30], ["rel60", 30], ["rel120", 60], ["rel250", 130], ["rel500", 250]] as const) {
    await page.waitForTimeout(wait);
    track.push({ at, sample: await dragSample(page, "entity:0") });
  }
  const settled = track[track.length - 1]!.sample;
  expect(settled.z).toBeGreaterThan(rest.z);
  expect(grabbed.z).toBe(settled.z);
  expect(mid.z).toBe(settled.z);
  for (const { at, sample } of track) {
    expect(sample.z, `depth moved at ${at}`).toBe(settled.z);
  }
  // And the drop's draw opened it fresh once the strokes had settled.
  expect(await fannedStrokes(page, "entity:0")).toBeGreaterThan(0);
});

/**
 * Every painted depth on the field, marks and edge labels alike.
 *
 * Read off the data the lane stamped, after the drop's draw has landed it —
 * so this is what the renderer sorts, not a prediction of it.
 */
async function sampleDepths(page: Page): Promise<{
  marks: Record<string, number>;
  labels: Record<string, number>;
}> {
  return page.evaluate(() => {
    const graph = (window as unknown as CanvasWindow).__worldFieldGraph;
    const marks: Record<string, number> = {};
    for (const node of graph.getNodeData()) {
      marks[String(node.id)] = Number(node.style?.zIndex ?? -1);
    }
    const labels: Record<string, number> = {};
    for (const edge of graph.getEdgeData()) {
      const style = (edge.style ?? {}) as Record<string, unknown>;
      if (typeof style.labelText !== "string" || !style.labelText) continue;
      labels[String(edge.id)] = Number(style.zIndex ?? -1);
    }
    return { marks, labels };
  });
}

test("a drop renumbers only the dropped mark and its own labels", async ({ page, world }) => {
  world.count = 12;
  world.hub = true;
  world.binary = true;
  await gotoWithSpread(page, false);
  await openPropertyTable(page);
  await buildHubField(page);
  await crowdBonds(page);
  const before = await sampleDepths(page);
  await crowdBonds(page, "entity:0", "entity:3", "entity:4");
  // The drop's draw has landed once the dropped mark fronts the field.
  await expect.poll(() => page.evaluate(() => {
    const graph = (window as unknown as CanvasWindow).__worldFieldGraph;
    const nodes = graph.getNodeData();
    const z = Number(nodes.find((node) => String(node.id) === "entity:3")?.style?.zIndex);
    return nodes.every(
      (node) => String(node.id) === "entity:3" || Number(node.style?.zIndex ?? 0) < z,
    );
  })).toBe(true);
  const after = await sampleDepths(page);
  // Same field, so the comparison is meaningful: nothing arrived or left.
  expect(new Set(Object.keys(after.marks))).toEqual(new Set(Object.keys(before.marks)));
  expect(new Set(Object.keys(after.labels))).toEqual(new Set(Object.keys(before.labels)));
  // Only the dropped mark moved.
  expect(
    Object.keys(after.marks).filter((id) => after.marks[id] !== before.marks[id]),
  ).toEqual(["entity:3"]);
  // And only the labels standing on it: their base rose with their endpoint.
  const incident = await page.evaluate(() => {
    const graph = (window as unknown as CanvasWindow).__worldFieldGraph;
    return graph.getRelatedEdgesData("entity:3")
      .filter((edge) => {
        const style = (edge.style ?? {}) as Record<string, unknown>;
        return typeof style.labelText === "string" && style.labelText.length > 0;
      })
      .map((edge) => String(edge.id))
      .sort();
  });
  expect(incident.length, "no labeled edge stands on the dropped mark").toBeGreaterThan(0);
  expect(
    Object.keys(after.labels)
      .filter((id) => after.labels[id] !== before.labels[id])
      .sort(),
  ).toEqual(incident);
});

test("depth assignment appends bounded tops and migrates legacy sequences", async ({ page, world }) => {
  world.count = 1;
  await page.goto("/");
  const result = await page.evaluate(async () => {
    const { emptySet, restack, paintDepths } = await import("/src/world/workingSet.ts");
    let set = emptySet();
    const ids = ["a", "b", "c", "d"];
    let renumbers = 0;
    let prev = new Map<string, number>();
    for (let drop = 0; drop < 120; drop += 1) {
      const id = ids[drop % ids.length]!;
      set = restack(set, id);
      const cur = paintDepths(set.depth);
      let changed = 0;
      for (const [key, z] of cur) {
        if (prev.get(key) !== z) changed += 1;
      }
      if (changed > 1) renumbers += 1;
      for (const z of cur.values()) {
        if (!(z > 1 && z < 2)) return { ok: false as const, why: `unbounded ${z} at drop ${drop}` };
      }
      const top = [...cur.entries()].sort((a, b) => a[1] - b[1]).pop()!;
      if (top[0] !== id) return { ok: false as const, why: `top ${top[0]} is not dropped ${id} at ${drop}` };
      prev = cur;
    }
    // Re-dropping the topmost mark is a no-op, not a new top.
    const held = paintDepths(set.depth);
    const replay = paintDepths(restack(set, "d").depth);
    if ([...held.entries()].some(([key, z]) => replay.get(key) !== z)) {
      return { ok: false as const, why: "re-dropping the top moved the stack" };
    }
    // Legacy sequences — bare drop counts from before paint lived here —
    // come back as the same order, inside the layer.
    const legacy = emptySet();
    legacy.depth.set("x", 1);
    legacy.depth.set("y", 2);
    legacy.depth.set("z", 3);
    const migrated = paintDepths(legacy.depth);
    const ordered = [...migrated.entries()].sort((a, b) => a[1] - b[1]).map(([key]) => key);
    return {
      ok: true as const,
      renumbers,
      migratedOrder: ordered.join(","),
      migratedBounded: [...migrated.values()].every((z) => z > 1 && z < 2),
    };
  });
  expect(result).toMatchObject({ ok: true });
  if (!result.ok) return;
  expect(result.renumbers).toBeLessThanOrEqual(2);
  expect(result.migratedOrder).toBe("x,y,z");
  expect(result.migratedBounded).toBe(true);
});

test("a neighbour's press puts the fan down and a stranger's leaves it up", async ({ page, world }) => {
  world.count = 6;
  world.binary = true;
  await page.goto("/");
  await openPropertyTable(page);
  for (let index = 0; index < 6; index += 1) {
    await readRow(page, index);
  }
  // Pile entity:0 onto entity:2's station as seen from entity:1, before
  // anything is selected and there is a fan to disturb.
  await crowdBonds(page, "entity:1", "entity:0", "entity:2");
  await selectReferent(page, "entity:1");
  await expect(reader(page).locator("h2")).toHaveText("Entity 1");
  await expect.poll(() => fannedStrokes(page, "entity:1")).toBeGreaterThan(0);
  const release = () => page.evaluate(() => window.dispatchEvent(new Event("pointerup")));
  // A neighbour holds one end of the fan's strokes: down for the gesture.
  await emitField(page, "node:pointerdown", "entity:0");
  await settleFrames(page);
  expect(await fannedStrokes(page, "entity:1")).toBe(0);
  await release();
  await expect.poll(() => fannedStrokes(page, "entity:1")).toBeGreaterThan(0);
  // A stranger touches none of them: the fan stands through the press.
  await emitField(page, "node:pointerdown", "entity:4");
  await settleFrames(page);
  expect(await fannedStrokes(page, "entity:1")).toBeGreaterThan(0);
  await release();
  expect(await fannedStrokes(page, "entity:1")).toBeGreaterThan(0);
});

test("spoke roles fan open when their stations pile", async ({ page, world }) => {
  world.count = 12;
  world.hub = true;
  await page.goto("/");
  await openPropertyTable(page);
  await buildHubField(page);
  await expect.poll(() => labeledIncidentCount(page, "entity:0")).toBeGreaterThan(0);
  // Natural placement piles two roles onto one station as seen from the hub.
  // The solver must see the pile: its strokes bend rather than standing
  // straight through each other.
  await expect.poll(() => fannedStrokes(page, "entity:0")).toBeGreaterThanOrEqual(2);
  await settleFrames(page);
  // And every painted role plate clears every other.
  const overlap = await page.evaluate(async () => {
    const graph = (window as unknown as CanvasWindow).__worldFieldGraph;
    const { paintedLabelBox } = await import("/src/world/visibility.ts");
    const boxes = [];
    for (const edge of graph.getRelatedEdgesData("entity:0")) {
      const style = (edge.style ?? {}) as Record<string, unknown>;
      if (typeof style.labelText !== "string" || !style.labelText) continue;
      boxes.push(paintedLabelBox(graph, String(edge.id)) as {
        minX: number; minY: number; maxX: number; maxY: number;
      } | null);
    }
    let area = 0;
    for (let i = 0; i < boxes.length; i += 1) {
      for (let j = i + 1; j < boxes.length; j += 1) {
        const a = boxes[i]!;
        const b = boxes[j]!;
        if (!a || !b) continue;
        area +=
          Math.max(0, Math.min(a.maxX, b.maxX) - Math.max(a.minX, b.minX)) *
          Math.max(0, Math.min(a.maxY, b.maxY) - Math.max(a.minY, b.minY));
      }
    }
    return { area, labels: boxes.length };
  });
  expect(overlap.labels).toBe(12);
  expect(overlap.area).toBe(0);
});

test("facts link back to their assertions and back walks the trail", async ({ page, world }) => {
  world.count = 12;
  world.binary = true;
  await page.goto("/");
  await openPropertyTable(page);
  await readRow(page, 0);
  // The first arrival pushes nothing: there is nowhere back to go.
  await expect(reader(page).locator(".panel__back")).toHaveCount(0);
  await reader(page).locator(".world__roles button").first().click();
  await expect(reader(page).locator("h2")).toHaveText("Entity 0");
  await expect(reader(page).locator(".panel__back")).toHaveCount(1);
  // The fact's assertion was never placed; the back-link reads it anyway.
  await reader(page).locator(".world-reader__facts button").first().click();
  await expect(reader(page).locator("h2")).toHaveText("property");
  await expect(reader(page)).toContainText("value-7");
  // Nothing on the field to take off, so no offer to.
  await expect(reader(page).getByText("Take off the field")).toHaveCount(0);
  // And back walks down the trail it came up, one arrival at a time.
  await reader(page).locator(".panel__back").click();
  await expect(reader(page).locator("h2")).toHaveText("Entity 0");
  await expect(reader(page).locator(".panel__back")).toHaveCount(1);
  await reader(page).locator(".panel__back").click();
  await expect(reader(page)).toContainText("value-0");
  await expect(reader(page).locator(".panel__back")).toHaveCount(0);
});

/**
 * Per-edge tab state, for the fan/tab drift extinction proof.
 *
 * The drift defect was a notch sitting off its plate. It cannot manifest
 * anymore: lone plates sit centred on their strokes (`chipLabelNudge` is 0,
 * spokes and single bonds stack nothing), so the stroke-crosses-plate rule
 * parks their tabs — and stacked plates are parked by the named-pair-sibling
 * rule. The fan only moves the share along the path, never the offsets, so
 * a parked tab stays parked through collapse and reopen. These checks pin
 * that: every labeled edge must report its tab hidden by design, and any
 * edge that ever draws one fails loudly with its id, reopening the bridge
 * question deliberately rather than by accident.
 */
type TabBridge = {
  edge: string;
  bridged: boolean | null;
  fanned: boolean;
  why: string;
};

async function tabBridges(page: Page, id: string): Promise<TabBridge[]> {
  return page.evaluate(async ({ id, readerPath }) => {
    const graph = (window as unknown as CanvasWindow).__worldFieldGraph;
    const { paintedLabelBox } = await import(readerPath);
    const elements = (graph as unknown as {
      context: { element: { getElement: (edgeId: string) => any } };
    }).context.element;
    const out: TabBridge[] = [];
    for (const edge of graph.getRelatedEdgesData(id)) {
      const style = (edge.style ?? {}) as Record<string, unknown>;
      if (typeof style.labelText !== "string" || !style.labelText) continue;
      const eid = String(edge.id);
      const rendered = elements.getElement(eid);
      const fanned =
        typeof rendered?.hasFan === "function" ? !rendered.hasFan(null) : false;
      const knockout = rendered?.getShape?.("knockout")?.getBounds?.();
      const plate = paintedLabelBox(graph, eid) as {
        minX: number; minY: number; maxX: number; maxY: number;
      } | null;
      if (!knockout || !plate) {
        out.push({ edge: eid, bridged: null, fanned, why: "shapes unreadable" });
        continue;
      }
      if (
        !(knockout.maxX - knockout.minX > 0.5) ||
        !(knockout.maxY - knockout.minY > 0.5)
      ) {
        out.push({ edge: eid, bridged: null, fanned, why: "tab hidden by design" });
        continue;
      }
      const overlapX =
        Math.min(knockout.maxX, plate.maxX) - Math.max(knockout.minX, plate.minX);
      const overlapY =
        Math.min(knockout.maxY, plate.maxY) - Math.max(knockout.minY, plate.minY);
      const bridged = overlapX > 0.5 && overlapY > 0.5;
      out.push({
        edge: eid,
        bridged,
        fanned,
        why: bridged
          ? "ok"
          : `knockout [${knockout.minX.toFixed(1)},${knockout.minY.toFixed(1)} ${knockout.maxX.toFixed(1)},${knockout.maxY.toFixed(1)}] plate [${plate.minX.toFixed(1)},${plate.minY.toFixed(1)} ${plate.maxX.toFixed(1)},${plate.maxY.toFixed(1)}]`,
      });
    }
    return out;
  }, { id, readerPath: "/src/world/visibility.ts" });
}

function expectTabsParked(rows: TabBridge[], { fanned }: { fanned: boolean }) {
  expect(rows.length, "no labeled edge to read a tab off").toBeGreaterThan(0);
  for (const row of rows) {
    expect(row.why, `tab state changed on ${row.edge}`).toBe("tab hidden by design");
  }
  if (fanned) {
    expect(
      rows.filter((row) => row.fanned).length,
      "no parked tab stands on a bent stroke",
    ).toBeGreaterThan(0);
  }
}

/** Frames of tab checks across an animation: none may draw, on any frame. */
async function tabsVisibleDuring(page: Page, id: string, ms: number) {
  return page.evaluate(async ({ id, ms }) => {
    const graph = (window as unknown as CanvasWindow).__worldFieldGraph;
    const elements = (graph as unknown as {
      context: { element: { getElement: (edgeId: string) => any } };
    }).context.element;
    const visible: { frame: number; edge: string }[] = [];
    let frames = 0;
    let examined = 0;
    const started = performance.now();
    await new Promise<void>((done) => {
      const tick = () => {
        frames += 1;
        for (const edge of graph.getRelatedEdgesData(id)) {
          const style = (edge.style ?? {}) as Record<string, unknown>;
          if (typeof style.labelText !== "string" || !style.labelText) continue;
          const eid = String(edge.id);
          const knockout = elements
            .getElement(eid)
            ?.getShape?.("knockout")
            ?.getBounds?.();
          if (!knockout) continue;
          examined += 1;
          if (
            knockout.maxX - knockout.minX > 0.5 &&
            knockout.maxY - knockout.minY > 0.5
          ) {
            visible.push({ frame: frames, edge: eid });
          }
        }
        if (performance.now() - started < ms) requestAnimationFrame(tick);
        else done();
      };
      requestAnimationFrame(tick);
    });
    return { frames, examined, visible: visible.slice(0, 8) };
  }, { id, ms });
}

test("label tabs stay parked under an active fan", async ({ page, world }) => {
  world.count = 12;
  world.hub = true;
  world.binary = true;
  await page.goto("/");
  await openPropertyTable(page);
  await buildHubField(page);
  await crowdBonds(page);
  await crowdBonds(page, "entity:0", "entity:3", "entity:4");
  await expect.poll(() => fannedStrokes(page, "entity:0")).toBeGreaterThan(0);
  await expect.poll(() => labeledIncidentCount(page, "entity:0")).toBeGreaterThan(0);
  expectTabsParked(await tabBridges(page, "entity:0"), { fanned: true });
});

test("label tabs stay parked through collapse and reopen", async ({ page, world }) => {
  await page.emulateMedia({ reducedMotion: "no-preference" });
  world.count = 12;
  world.hub = true;
  world.binary = true;
  await page.goto("/");
  await openPropertyTable(page);
  await buildHubField(page);
  await crowdBonds(page);
  await crowdBonds(page, "entity:0", "entity:3", "entity:4");
  await expect.poll(() => fannedStrokes(page, "entity:0")).toBeGreaterThan(0);
  // Collapse: the press puts the fan down over ~95ms of easing.
  await emitField(page, "node:pointerdown", "entity:0");
  const collapse = await tabsVisibleDuring(page, "entity:0", 600);
  expect(collapse.frames, "no frames sampled").toBeGreaterThan(5);
  expect(collapse.examined, "no tab readable mid-collapse").toBeGreaterThan(0);
  expect(collapse.visible).toEqual([]);
  await expect.poll(() => fannedStrokes(page, "entity:0")).toBe(0);
  // Reopen: release re-solves fresh over ~140ms of easing.
  await page.evaluate(() => window.dispatchEvent(new Event("pointerup")));
  const reopen = await tabsVisibleDuring(page, "entity:0", 800);
  expect(reopen.frames, "no frames sampled").toBeGreaterThan(5);
  expect(reopen.examined, "no tab readable mid-reopen").toBeGreaterThan(0);
  expect(reopen.visible).toEqual([]);
  await expect.poll(() => fannedStrokes(page, "entity:0")).toBeGreaterThan(0);
});

test("spoke tabs stay parked under selection", async ({ page, world }) => {
  world.count = 12;
  world.hub = true;
  await page.goto("/");
  await openPropertyTable(page);
  await buildHubField(page);
  await expect.poll(() => labeledIncidentCount(page, "entity:0")).toBeGreaterThan(0);
  expectTabsParked(await tabBridges(page, "entity:0"), { fanned: false });
});

/**
 * Stranded transient poses converge to the settled frame.
 *
 * A lifecycle run cancelled mid-arrival can leave births frozen in the model
 * — a disc at opacity 0 and mid-flight size — while every authored frame
 * says the end state, so restyle never patches them: it diffs authored
 * against authored, and both agree. The guard diffs the model against the
 * settled frame instead and patches what disagrees. Same guard both lanes
 * share; the schema lane grew it first.
 */
async function strandMark(page: Page, nodeId: string, edgeId: string) {
  await page.evaluate(({ nodeId, edgeId }) => {
    const graph = (window as unknown as CanvasWindow).__worldFieldGraph;
    const node = graph.getNodeData(nodeId);
    const edge = graph.getEdgeData(edgeId);
    graph.updateNodeData([
      { id: nodeId, style: { ...(node.style as object), opacity: 0, size: 3.6 } },
    ]);
    graph.updateEdgeData([{ id: edgeId, style: { ...(edge.style as object), opacity: 0 } }]);
  }, { nodeId, edgeId });
}

test("stranded poses converge to the settled frame", async ({ page, world }) => {
  world.count = 3;
  world.binary = true;
  await page.goto("/");
  await openPropertyTable(page);
  await readRow(page, 0);
  await readRow(page, 1);
  await readRow(page, 2);
  await selectReferent(page, "entity:0");
  await expect(reader(page).locator("h2")).toHaveText("Entity 0");
  await expect.poll(() => labeledIncidentCount(page, "entity:0")).toBeGreaterThan(0);
  const verdict = await page.evaluate(async () => {
    const graph = (window as unknown as CanvasWindow).__worldFieldGraph;
    const { convergeStrandedToFrame } = await import("/src/world/canvasMotion.ts");
    const node = graph.getNodeData("entity:0");
    const edge = graph.getEdgeData("bond:assertion:0");
    const frame = {
      nodes: [{ id: "entity:0", style: { ...(node.style as object) } }],
      edges: [{ id: "bond:assertion:0", style: { ...(edge.style as object) } }],
    };
    const problems: string[] = [];
    // Clean converges nothing.
    if (convergeStrandedToFrame(graph, frame) !== false) {
      problems.push("clean frame converged");
    }
    // Unknown ids are skipped, not failed.
    if (
      convergeStrandedToFrame(graph, {
        nodes: [{ id: "nope", style: { opacity: 0 } }],
        edges: [{ id: "nope", style: { opacity: 0 } }],
      }) !== false
    ) {
      problems.push("missing ids converged");
    }
    // Stranded poses patch to the frame and report it.
    graph.updateNodeData([
      { id: "entity:0", style: { ...frame.nodes[0]!.style, opacity: 0, size: 3.6 } },
    ]);
    graph.updateEdgeData([
      { id: "bond:assertion:0", style: { ...frame.edges[0]!.style, opacity: 0 } },
    ]);
    if (convergeStrandedToFrame(graph, frame) !== true) {
      problems.push("stranded frame did not converge");
    }
    const healedNode = graph.getNodeData("entity:0").style as Record<string, unknown>;
    const healedEdge = graph.getEdgeData("bond:assertion:0").style as Record<string, unknown>;
    const wantSize = (node.style as Record<string, unknown>).size;
    if (healedNode.opacity !== 1 || JSON.stringify(healedNode.size) !== JSON.stringify(wantSize)) {
      problems.push(`node not healed: ${JSON.stringify({ opacity: healedNode.opacity, size: healedNode.size })}`);
    }
    if (healedEdge.opacity !== 1) {
      problems.push(`edge not healed: ${JSON.stringify({ opacity: healedEdge.opacity })}`);
    }
    if (convergeStrandedToFrame(graph, frame) !== false) {
      problems.push("healed frame converged again");
    }
    return problems;
  });
  expect(verdict).toEqual([]);
});

test("a restyle heals poses a cancelled arrival stranded", async ({ page, world }) => {
  world.count = 3;
  world.binary = true;
  await page.goto("/");
  await openPropertyTable(page);
  await readRow(page, 0);
  await readRow(page, 1);
  await readRow(page, 2);
  await selectReferent(page, "entity:0");
  await expect(reader(page).locator("h2")).toHaveText("Entity 0");
  await expect.poll(() => labeledIncidentCount(page, "entity:0")).toBeGreaterThan(0);
  await strandMark(page, "entity:1", "bond:assertion:1");
  // A selection changes naming, never topology or positions, so this draw
  // takes the restyle lane — the lane that diffs authored against authored
  // and would otherwise leave the stranded poses frozen.
  await selectReferent(page, "entity:2");
  await expect(reader(page).locator("h2")).toHaveText("Entity 2");
  await expect.poll(() => page.evaluate(() => {
    const graph = (window as unknown as CanvasWindow).__worldFieldGraph;
    const node = graph.getNodeData("entity:1").style as Record<string, unknown>;
    const edge = graph.getEdgeData("bond:assertion:1").style as Record<string, unknown>;
    return node.opacity === 1 && edge.opacity === 1;
  })).toBe(true);
});

test("the fan yields to a hold exactly under its scope", async ({ page, world }) => {
  // Evaluated in the page: `spread.ts` shares its module graph with the
  // renderer's marks, which the Node runner cannot import.
  world.count = 1;
  await page.goto("/");
  const verdict = await page.evaluate(async () => {
    const { spreadYieldsToHold } = await import("/src/world/spread.ts");
    const edges = [
      { source: "hub", target: "a" },
      { source: "b", target: "hub" },
      { source: "hub", target: "hub" },
      { source: "x", target: "y" },
      { source: 7, target: "hub" },
    ];
    const scopes = ["none", "owner", "neighbourhood", "any"] as const;
    const yields = (scope: (typeof scopes)[number], pressed: string) =>
      spreadYieldsToHold(scope, "hub", pressed, edges);
    const problems: string[] = [];
    const check = (scope: (typeof scopes)[number], pressed: string, want: boolean) => {
      if (yields(scope, pressed) !== want) {
        problems.push(`${scope} + ${pressed}: want ${want}`);
      }
    };
    for (const scope of scopes) {
      check(scope, "hub", scope !== "none");
      check(scope, "a", scope === "neighbourhood" || scope === "any");
      check(scope, "b", scope === "neighbourhood" || scope === "any");
      check(scope, "stranger", scope === "any");
      check(scope, "x", scope === "any");
      check(scope, "7", scope === "any");
      if (spreadYieldsToHold(scope, null, "hub", edges)) {
        problems.push(`${scope} + null owner yields`);
      }
    }
    return problems;
  });
  expect(verdict).toEqual([]);
});
