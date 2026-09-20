"""Markdown v0 source driver: reconstructible addressability only.

The driver answers what exact source material can be addressed. It does not
interpret meaning, mint World referents, or assign standing.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from ontology_author.world.core.source import SourceObservation

from ontology_author.evidence import EvidenceError

MARKDOWN_PROVIDER = "markdown"
MARKDOWN_DRIVER = "markdown-source/v0"


def parse_byte_location(location: str) -> tuple[int, int]:
    text = str(location or "")
    if not text.startswith("bytes:"):
        raise EvidenceError(f"native location is not a byte range: {location!r}")
    parts = text.split(":")
    if len(parts) != 3:
        raise EvidenceError(f"native location is not a byte range: {location!r}")
    try:
        start, end = int(parts[1]), int(parts[2])
    except ValueError as exc:
        raise EvidenceError(f"native location is not a byte range: {location!r}") from exc
    if start < 0 or end < start:
        raise EvidenceError(f"native location is not a half-open byte range: {location!r}")
    return start, end


_ATX = re.compile(rb"^(#{1,6})[ \t]+(.+?)[ \t#]*\r?$")
_FENCE = re.compile(rb"^(`{3,}|~{3,})")
_LIST = re.compile(rb"^(\s{0,3})([*\-+]|\d{1,9}[.)])[ \t]+")
_QUOTE = re.compile(rb"^>[ \t]?")
_LINK = re.compile(rb"\[(?:\\.|[^\]])+\]\((?:\\.|[^)])*\)")
_BLANK = re.compile(rb"^[ \t]*\r?$")


@dataclass(frozen=True)
class MarkdownRegion:
    """An addressable byte range. Not a World referent."""

    handle: str
    revision: str
    start: int
    end: int
    kind: str
    heading_path: tuple[str, ...] = ()
    block_index: int = -1
    span_kind: str = "none"

    @property
    def native_location(self) -> str:
        return f"bytes:{self.start}:{self.end}"

    def locator(self) -> dict[str, Any]:
        return {
            "block_kind": self.kind,
            "heading_path": list(self.heading_path),
            "block_index": self.block_index,
            "span_kind": self.span_kind,
        }


@dataclass(frozen=True)
class MarkdownLink:
    text: MarkdownRegion
    destination: MarkdownRegion
    destination_text: str


class MarkdownSource:
    """Immutable Markdown file with exact UTF-8 byte addressing."""

    def __init__(self, path: Path | str, *, handle: str, data: bytes | None = None) -> None:
        self.path = Path(path)
        self.handle = str(handle)
        if data is None:
            raw = self.path.read_bytes()
        else:
            raw = data
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise EvidenceError(
                f"Markdown source {self.handle!r} is not UTF-8"
            ) from exc
        self.data = raw
        self.revision = "sha256:" + hashlib.sha256(raw).hexdigest()
        self._blocks = tuple(_parse_blocks(self.handle, self.revision, raw))
        self._links = tuple(_parse_links(self.handle, self.revision, raw, self._blocks))

    @classmethod
    def from_path(cls, path: Path | str, *, workspace: Path | str | None = None) -> "MarkdownSource":
        file_path = Path(path)
        root = Path(workspace) if workspace is not None else file_path.parent
        handle = file_path.resolve().relative_to(root.resolve()).as_posix()
        return cls(file_path, handle=handle)

    def document(self) -> MarkdownRegion:
        return MarkdownRegion(
            handle=self.handle,
            revision=self.revision,
            start=0,
            end=len(self.data),
            kind="document",
            heading_path=(),
            block_index=0,
        )

    def blocks(self, kind: str | None = None) -> tuple[MarkdownRegion, ...]:
        if kind is None:
            return self._blocks
        return tuple(block for block in self._blocks if block.kind == kind)

    def paragraphs(self) -> tuple[MarkdownRegion, ...]:
        return self.blocks("paragraph")

    def headings(self) -> tuple[MarkdownRegion, ...]:
        return self.blocks("heading")

    def sections(self) -> tuple[MarkdownRegion, ...]:
        return self.blocks("section")

    def heading_path(self, *titles: str) -> MarkdownRegion | None:
        wanted = tuple(titles)
        for heading in self.headings():
            if heading.heading_path == wanted:
                return heading
        for section in self.sections():
            if section.heading_path == wanted:
                return section
        return None

    def section(self, *titles: str) -> MarkdownRegion | None:
        wanted = tuple(titles)
        for section in self.sections():
            if section.heading_path == wanted:
                return section
        return None

    def region(
        self,
        start: int,
        end: int,
        *,
        kind: str = "span",
        heading_path: Iterable[str] = (),
        block_index: int = -1,
        span_kind: str = "none",
    ) -> MarkdownRegion:
        if start < 0 or end < start or end > len(self.data):
            raise EvidenceError(
                f"byte range {start}:{end} is outside {self.handle}"
            )
        return MarkdownRegion(
            handle=self.handle,
            revision=self.revision,
            start=start,
            end=end,
            kind=kind,
            heading_path=tuple(heading_path),
            block_index=block_index,
            span_kind=span_kind,
        )

    def span_containing(self, text: str) -> MarkdownRegion:
        needle = text.encode("utf-8")
        start = self.data.find(needle)
        if start < 0:
            raise EvidenceError(f"text not found in {self.handle}: {text!r}")
        if self.data.find(needle, start + 1) >= 0:
            raise EvidenceError(f"text is not unique in {self.handle}: {text!r}")
        enclosing = self._enclosing_block(start, start + len(needle))
        return self.region(
            start,
            start + len(needle),
            kind="span",
            heading_path=enclosing.heading_path if enclosing else (),
            block_index=enclosing.block_index if enclosing else -1,
            span_kind="exact_text",
        )

    def links(self) -> tuple[MarkdownLink, ...]:
        return self._links

    def reconstruct(self, region: MarkdownRegion | SourceObservation) -> str:
        if isinstance(region, SourceObservation):
            self._check_observation(region)
            start, end = parse_byte_location(region.native_location)
        else:
            if region.handle != self.handle or region.revision != self.revision:
                raise EvidenceError("region does not belong to this Markdown source")
            start, end = region.start, region.end
        return self.data[start:end].decode("utf-8")

    def observe(self, region: MarkdownRegion) -> SourceObservation:
        if region.handle != self.handle or region.revision != self.revision:
            raise EvidenceError("region does not belong to this Markdown source")
        return SourceObservation(
            provider=MARKDOWN_PROVIDER,
            native_handle=self.handle,
            source_revision=self.revision,
            native_location=region.native_location,
            payload=json.dumps(region.locator(), sort_keys=True, separators=(",", ":")),
        )

    def known_losses(self) -> tuple[str, ...]:
        losses = [
            "raw HTML is not interpreted",
            "coordinates are UTF-8 byte ranges; CRLF is stored as raw bytes",
        ]
        if b"\r\n" in self.data:
            losses.append("CRLF line endings are preserved as bytes, not normalized")
        return tuple(losses)

    def _check_observation(self, observation: SourceObservation) -> None:
        if observation.provider != MARKDOWN_PROVIDER:
            raise EvidenceError(f"observation provider is not markdown: {observation.provider}")
        if observation.native_handle != self.handle:
            raise EvidenceError("observation handle does not match this source")
        if observation.source_revision != self.revision:
            raise EvidenceError("observation revision does not match this source")

    def _enclosing_block(self, start: int, end: int) -> MarkdownRegion | None:
        candidates = [
            block for block in self._blocks
            if block.kind not in {"document", "section"} and block.start <= start and end <= block.end
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda block: (block.end - block.start, block.start))


def _line_starts(data: bytes) -> list[tuple[int, int, bytes]]:
    lines: list[tuple[int, int, bytes]] = []
    start = 0
    while start <= len(data):
        newline = data.find(b"\n", start)
        if newline < 0:
            lines.append((start, len(data), data[start:]))
            break
        lines.append((start, newline + 1, data[start:newline + 1]))
        start = newline + 1
        if start == len(data):
            lines.append((start, start, b""))
            break
    return lines


def _strip_newline(line: bytes) -> bytes:
    if line.endswith(b"\r\n"):
        return line[:-2]
    if line.endswith(b"\n"):
        return line[:-1]
    return line


def _heading_text(body: bytes) -> str:
    return body.decode("utf-8").strip()


def _parse_blocks(handle: str, revision: str, data: bytes) -> list[MarkdownRegion]:
    lines = _line_starts(data)
    blocks: list[MarkdownRegion] = []
    headings: list[tuple[int, str, int, int]] = []
    heading_stack: list[tuple[int, str]] = []
    index = 1
    i = 0
    in_front_matter = data.startswith(b"---") and (len(data) == 3 or data[3:4] in {b"\n", b"\r"})
    if in_front_matter:
        close = data.find(b"\n---", 3)
        if close >= 0:
            end = close + 4
            if end < len(data) and data[end:end + 1] == b"\n":
                end += 1
            blocks.append(MarkdownRegion(handle, revision, 0, end, "front_matter", (), index))
            index += 1
            while i < len(lines) and lines[i][0] < end:
                i += 1

    while i < len(lines):
        start, end, raw = lines[i]
        body = _strip_newline(raw)
        if start == end == len(data) and not raw:
            break
        if _BLANK.match(body or b""):
            i += 1
            continue
        fence = _FENCE.match(body)
        if fence:
            marker = fence.group(1)[:1] * len(fence.group(1))
            j = i + 1
            close_end = end
            while j < len(lines):
                other_body = _strip_newline(lines[j][2])
                if other_body.startswith(marker) and _FENCE.match(other_body):
                    close_end = lines[j][1]
                    j += 1
                    break
                close_end = lines[j][1]
                j += 1
            path = tuple(title for _, title in heading_stack)
            blocks.append(MarkdownRegion(handle, revision, start, close_end, "fenced", path, index))
            index += 1
            i = j
            continue
        atx = _ATX.match(body)
        if atx:
            level = len(atx.group(1))
            title = _heading_text(atx.group(2))
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, title))
            path = tuple(item[1] for item in heading_stack)
            blocks.append(MarkdownRegion(handle, revision, start, end, "heading", path, index))
            headings.append((level, title, start, index))
            index += 1
            i += 1
            continue
        if _QUOTE.match(body):
            j = i + 1
            block_end = end
            while j < len(lines):
                next_body = _strip_newline(lines[j][2])
                if _BLANK.match(next_body) or _ATX.match(next_body) or _FENCE.match(next_body):
                    break
                if not _QUOTE.match(next_body):
                    break
                block_end = lines[j][1]
                j += 1
            path = tuple(title for _, title in heading_stack)
            blocks.append(MarkdownRegion(handle, revision, start, block_end, "quote", path, index))
            index += 1
            i = j
            continue
        if _LIST.match(body):
            j = i + 1
            block_end = end
            while j < len(lines):
                next_body = _strip_newline(lines[j][2])
                if _BLANK.match(next_body) or _ATX.match(next_body) or _FENCE.match(next_body):
                    break
                if _LIST.match(next_body) and not next_body.startswith(b" "):
                    break
                if _LIST.match(next_body):
                    break
                block_end = lines[j][1]
                j += 1
            path = tuple(title for _, title in heading_stack)
            blocks.append(MarkdownRegion(handle, revision, start, block_end, "list_item", path, index))
            index += 1
            i = j
            continue
        j = i + 1
        block_end = end
        while j < len(lines):
            next_body = _strip_newline(lines[j][2])
            if _BLANK.match(next_body) or _ATX.match(next_body) or _FENCE.match(next_body) or _LIST.match(next_body) or _QUOTE.match(next_body):
                break
            block_end = lines[j][1]
            j += 1
        path = tuple(title for _, title in heading_stack)
        blocks.append(MarkdownRegion(handle, revision, start, block_end, "paragraph", path, index))
        index += 1
        i = j

    for position, (level, title, start, heading_index) in enumerate(headings):
        section_end = len(data)
        for later_level, _title, later_start, _later_index in headings[position + 1:]:
            if later_level <= level:
                section_end = later_start
                break
        path = ()
        for block in blocks:
            if block.kind == "heading" and block.start == start:
                path = block.heading_path
                break
        blocks.append(MarkdownRegion(handle, revision, start, section_end, "section", path, heading_index))
    blocks.sort(key=lambda block: (block.start, 0 if block.kind == "section" else 1, block.block_index))
    return blocks


def _parse_links(
    handle: str,
    revision: str,
    data: bytes,
    blocks: Iterable[MarkdownRegion],
) -> list[MarkdownLink]:
    searchable = [block for block in blocks if block.kind in {"paragraph", "heading", "list_item", "quote"}]
    links: list[MarkdownLink] = []
    for block in searchable:
        for match in _LINK.finditer(data, block.start, block.end):
            inner = match.group(0)
            split = inner.find(b"](")
            if split < 0:
                continue
            text_start = match.start() + 1
            text_end = match.start() + split
            dest_start = match.start() + split + 2
            dest_end = match.end() - 1
            links.append(
                MarkdownLink(
                    text=MarkdownRegion(
                        handle, revision, text_start, text_end, "span",
                        block.heading_path, block.block_index, "link_text",
                    ),
                    destination=MarkdownRegion(
                        handle, revision, dest_start, dest_end, "span",
                        block.heading_path, block.block_index, "link_destination",
                    ),
                    destination_text=data[dest_start:dest_end].decode("utf-8"),
                )
            )
    return links
