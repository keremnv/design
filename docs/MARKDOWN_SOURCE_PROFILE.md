# Markdown source profile

This document defines Markdown v0 as a source driver: reconstructible
addressability over ordinary Markdown files. It is subordinate to
[`AUTHORITY_CONSTRUCTION_CONTRACT.md`](AUTHORITY_CONSTRUCTION_CONTRACT.md).

Markdown is construction machinery for evidence addressing. It is not a
semantic ontology, not a persistent Markdown IR, and not part of the
universal authority-construction contract.

The driver answers:

```text
What can I address?
```

It does not answer:

```text
What does this paragraph mean?
```

Principle:

```text
Parse eagerly, select deterministically, interpret lazily.
```

v0 implementation: `ontology_author.evidence.markdown.MarkdownSource`.

## Profile identity

## Profile identity

```text
provider: markdown
driver: markdown-source/v0
profile: markdown-authority-v0
```

The driver MAY be a CommonMark-compatible parse, a deterministic project
script, or an agent-authored reusable parser. Durable coordinates MUST follow
this profile.

## Source identity and revision

A Markdown source in an authorized universe is identified by:

```text
native handle     workspace-relative POSIX path, or a declared equivalent
source revision   SHA-256 of the exact UTF-8 file bytes
```

Optional observational metadata MAY record a Git commit, blob OID, or
workspace mtime. Those MUST NOT replace the content digest. Reconstructing
the same bytes MUST yield the same revision.

Standing (`AUTHORITATIVE`, `AVAILABLE`, `ANALYSIS_SUPPORT`) is declared by
the authorized source universe. The Markdown driver does not assign standing.

## Coordinate system

Selected evidence MUST be reconstructible as a `SourceObservation`:

```text
provider:         markdown
native_handle:    docs/checkout.md
source_revision:  sha256:<hex>
native_location:  bytes:<start>:<end>
payload:          optional structural locator JSON, not a substitute coordinate
```

`bytes:start:end` is a half-open UTF-8 byte range into the immutable file
bytes identified by `source_revision`. This matches the program-spine
preference for reconstructible ranges without copying source bodies into
semantic tuples. The v0 writer also copies structural locators into
`AssertionGrounding.extra`, because `SourceObservation.as_pointer()` does not
persist `payload`.

A structural locator MAY appear in `payload` as a convenience, for example:

```text
block_kind        document | heading | section | paragraph | list_item | fenced | link_span | quote
heading_path      ATX heading text sequence from the document root
block_index       deterministic depth-first index of block-level nodes
span_kind         emphasis | link_text | link_destination | inline_code | none
```

Structural locators are not identities. They MUST NOT become World referents.
If heading text is edited, the byte range is the reconstruction source of
truth; a stale heading path is a known loss, not a silent retarget.

## Addressable native structure

The v0 driver MUST be able to address at least:

```text
document            entire file bytes
heading             ATX heading line, including markers
section             bytes from a heading through the last byte before the
                    next heading of equal or higher rank, or EOF
paragraph           contiguous block-level paragraph
list_item           a single list item’s bytes
fenced_block        a fenced code/info block, including fences
span                an inline range inside a paragraph or heading
explicit_link       link text span and destination span
```

Setext headings, thematic breaks, block quotes, and HTML blocks MAY be
addressed as blocks when the parser recognizes them. Unrecognized bytes
remain addressable as a residual document range so addressability coverage
can be honest.

Literal source fidelity means: given handle, revision, and `bytes:start:end`,
the exact original characters are recoverable from the immutable file. Do not
normalize quotes, whitespace, or heading text in the persisted coordinate.

## What this driver MUST NOT do

- Create persistent semantic identities for documents, headings, sections,
  paragraphs, noun phrases, or quoted labels.
- Treat a heading as equivalent to a concept named by that heading.
- Interpret admonitions, tables of contents, or task lists as World claims.
- Persist a full Markdown AST in the World.
- Follow or dereference a link destination as authority unless the destination
  is itself in the declared source universe.
- Assign `AUTHORITATIVE` standing.

Explicit Markdown links are source-native *addressable relationships* available
to construction. They are not automatically World claims. If construction
persists a link-derived claim, the support class is typically `SOURCE_NATIVE`
or `SOURCE_EXPLICIT`, and both the link text and destination spans remain
evidence.

## Source-native identity

Markdown v0 produces **no** source-native referents.

Future structured sources may. This profile must not be generalized into a
rule that every addressable node is an identity.

## Metadata

Basic metadata the driver MAY expose to construction without persisting it as
semantics:

```text
path and digest
byte length
heading outline as locator hints
explicit link destinations (relative path, URL, or fragment)
info strings on fenced blocks
YAML front matter as a byte region, uninterpreted
```

Front matter is evidence. Keys in front matter are not automatically semantic
referents or World facts.

## Selection vs parse

The parser MAY produce a complete addressability map during construction. The
World MUST persist only:

- authorized source membership and revision;
- `SourceObservation`s that actually ground claims or unresolved records;
- receipt summaries of examined regions and known losses.

An optional ephemeral or sidecar addressability map is allowed as construction
machinery. It is not a kernel IR.

## Completeness basis

Source addressability coverage for this profile is complete when:

```text
every AUTHORITATIVE (and, if declared, AVAILABLE) Markdown source in the
universe has a content digest, and every byte of each such file is covered
by the document range or by a partition into recognized blocks plus a
disclosed residual
```

That completeness is mechanical addressability. It is not construction
coverage and not attachment coverage.

Known v0 losses, which a receipt SHOULD list when they affect reconstruction
or selection:

```text
CRLF vs LF stored as raw bytes; coordinates are byte-based
undecodable non-UTF-8 files (not admitted; not silently repaired)
raw HTML not interpreted
reference-style link definitions may be addressable as blocks while
    resolved destinations require a declared resolver
GFM tables, footnotes, and extensions unless a construction profile
    claims them
included or generated Markdown not in the declared universe
```

## Construction use

A constructor MAY use the driver to:

- list headings and paragraphs;
- recover exact quotes;
- follow in-universe relative links;
- compare a stored range to current bytes when a later source-authority
  maintenance step exists (not part of program-side attachment maintenance).

A constructor MUST still select claims lazily. Presence of a paragraph in the
addressability map does not require a World assertion.

Unresolved Markdown phrases remain `SourceObservation`s on
`authority_unresolved` records, still without becoming referents.
