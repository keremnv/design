/**
 * The TABLES dock's subject chrome.
 *
 * World, the legacy Purpose frontier, and governed Obligations are subjects in
 * one panel, not parallel applications. The handle still says Tables; these
 * buttons say which read contract is open. A relation or derivation is a
 * subject you navigated to — named in the bar, not a third tab.
 */

import type { ReactNode } from "react";
import { PanelClose } from "./panelChrome";

export type TableSubject = "world" | "frontier" | "governed" | "other";

export type TableChrome = {
  current: TableSubject;
  hasFrontier: boolean;
  hasGovernedObligations: boolean;
  onWorld: () => void;
  onFrontier: () => void;
  onGoverned: () => void;
  onClose: () => void;
};

export function TableBar({
  chrome,
  title,
  meta,
  children,
}: {
  chrome: TableChrome;
  title?: string;
  meta?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <header className="table__bar">
      <nav className="table__subjects" aria-label="Table subject">
        <button
          type="button"
          aria-pressed={chrome.current === "world"}
          onClick={chrome.onWorld}
        >
          world
        </button>
        {chrome.hasFrontier ? (
          <button
            type="button"
            aria-pressed={chrome.current === "frontier"}
            onClick={chrome.onFrontier}
          >
            {/*
              * This is the compatibility surface for Purpose demand. It is
              * named explicitly so it cannot be confused with the governed
              * Obligation collection beside it.
              */}
            purpose frontier
          </button>
        ) : null}
        {chrome.hasGovernedObligations ? (
          <button
            type="button"
            aria-pressed={chrome.current === "governed"}
            onClick={chrome.onGoverned}
          >
            obligations
          </button>
        ) : null}
      </nav>
      {/*
        * The two of them in one box, and the box takes the free space rather
        * than the text's width. That is what makes the fade honest: the mask
        * eats the last stretch of the *box*, so a name that fits ends well
        * before it and only a name that has run out of room is faded away.
        */}
      {title || meta ? (
        <div className="table__said">
          {title ? <b>{title}</b> : null}
          {meta ? <span className="table__meta">{meta}</span> : null}
        </div>
      ) : null}
      <div className="table__actions">
        {children}
        <PanelClose onClose={chrome.onClose} />
      </div>
    </header>
  );
}

/** Search is local to the table subject, independent of the global finder. */
export function TableSearch({ value, onChange, label }: {
  value: string;
  onChange: (value: string) => void;
  label: string;
}) {
  return <div className="table__search">
    <input type="search" aria-label={label} placeholder={label} value={value}
      onChange={(event) => onChange(event.target.value)}
      onKeyDown={(event) => {
        if (event.key === "Escape" && value) {
          event.stopPropagation();
          onChange("");
        }
      }} />
    {value ? <button type="button" onClick={() => onChange("")}>clear search</button> : null}
  </div>;
}
