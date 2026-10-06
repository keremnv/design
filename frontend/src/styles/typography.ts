/**
 * App typography tokens — the single source for both surfaces.
 *
 * CSS:  font-family: var(--font-sans) | var(--font-mono)
 *  JS/G6: FONT_SANS_FAMILY | FONT_MONO_FAMILY
 *
 * The CSS vars are restated from these tokens at boot (see
 * `applyTypographyToDocument`); base.css only holds first-paint defaults.
 * Nothing else in the app names a face.
 *
 * Usage rule: Jost for controls, prose, names, statuses, and numeric counts
 * (use tabular-nums when numbers need alignment). Mono for code, raw technical
 * identifiers/paths, and diagrams whose characters must align. Small size or
 * secondary emphasis alone is never a reason to switch families.
 *
 * Mono is a trial against Jost. Flip `FONT_MONO` to another loaded id and
 * rebuild; there is no runtime picker yet. Loaded faces: dm, plex, space, azeret, spline.
 */
export const FONT_SANS_FAMILY =
  'Jost, "Helvetica Neue", Helvetica, sans-serif';

const FONT_MONO_STACK = "ui-monospace, Menlo, Consolas, monospace";

export const FONT_MONO_TRIALS = {
  dm: {
    name: "DM Mono",
    note: "Geometric, same construction as Jost. Quiet at small sizes.",
    scale: 1,
  },
  plex: {
    name: "IBM Plex Mono",
    note: "Humanist, a little softer than Jost.",
    scale: 1,
  },
  space: {
    name: "Space Mono",
    note: "Also geometric, more ink and character. Louder in a tag.",
    scale: 1,
  },
  azeret: {
    name: "Azeret Mono",
    note: "Low-contrast grotesque mono, generous spacing. Airy at small sizes.",
    scale: 0.9,
  },
  spline: {
    name: "Spline Sans Mono",
    note: "Geometric-grotesque mono, open apertures. Calm at small sizes.",
    scale: 0.9,
  },
} as const;

export type FontMonoId = keyof typeof FONT_MONO_TRIALS;

/** The mono in use. Change this to try another loaded face. */
export const FONT_MONO: FontMonoId = "spline";

export function fontMonoFamily(id: FontMonoId = FONT_MONO): string {
  return `"${FONT_MONO_TRIALS[id].name}", ${FONT_MONO_STACK}`;
}

export const FONT_MONO_FAMILY = fontMonoFamily(FONT_MONO);

/**
 * Apparent-size compensation for the active trial. Faces with generous
 * metrics (Azeret) render larger than their nominal size next to Jost; the
 * scale restores parity. Every mono size — canvas paint, canvas measure,
 * and DOM rules via `--font-mono-scale` — multiplies by this, so measure
 * and paint can never drift apart.
 */
export const FONT_MONO_SCALE = FONT_MONO_TRIALS[FONT_MONO].scale;

/** Default G6 node label face — keep in sync with FONT_SANS_FAMILY. */
export const FONT_NODE_LABEL_FAMILY = FONT_SANS_FAMILY;

/**
 * Restate the CSS face vars from the tokens, once, at boot.
 *
 * The canvas reads the tokens directly; the DOM reads the vars. Without this
 * a mono trial would move the canvas and leave every panel behind, because
 * base.css can only hold one stack. Called from main before first render.
 */
export function applyTypographyToDocument(): void {
  const root = document.documentElement;
  root.style.setProperty("--font-sans", FONT_SANS_FAMILY);
  root.style.setProperty("--font-mono", FONT_MONO_FAMILY);
  root.style.setProperty("--font-mono-scale", String(FONT_MONO_SCALE));
}
