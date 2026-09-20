from __future__ import annotations

from ontology_author.evidence.markdown import MarkdownSource
from ontology_author.world.core.source import SourceObservation


def test_markdown_byte_ranges_are_literal_and_reconstructible(tmp_path):
    path = tmp_path / "docs" / "note.md"
    path.parent.mkdir()
    text = "# Title\n\nHello world.\n\nSee [spec](./spec.md).\n"
    path.write_text(text, encoding="utf-8", newline="")
    source = MarkdownSource.from_path(path, workspace=tmp_path)

    assert source.handle == "docs/note.md"
    assert source.revision.startswith("sha256:")
    assert source.reconstruct(source.document()) == text
    paragraphs = source.paragraphs()
    assert len(paragraphs) == 2
    assert source.reconstruct(paragraphs[0]) == "Hello world.\n"
    heading = source.headings()[0]
    assert source.reconstruct(heading).startswith("# Title")
    section = source.section("Title")
    assert section is not None
    assert section.start == heading.start
    span = source.span_containing("Hello world.")
    assert source.reconstruct(span) == "Hello world."
    observation = source.observe(paragraphs[0])
    assert observation.provider == "markdown"
    assert observation.native_handle == "docs/note.md"
    assert observation.source_revision == source.revision
    assert observation.native_location == paragraphs[0].native_location
    assert source.reconstruct(observation) == "Hello world.\n"
    links = source.links()
    assert len(links) == 1
    assert links[0].destination_text == "./spec.md"
    assert source.reconstruct(links[0].text) == "spec"


def test_markdown_driver_does_not_mint_identities(tmp_path):
    path = tmp_path / "page.md"
    path.write_text(
        "## Purchase Action\n\nThe purchase action displays the total.\n",
        encoding="utf-8",
        newline="",
    )
    source = MarkdownSource(path, handle="page.md")
    kinds = {block.kind for block in source.blocks()}
    assert {"heading", "paragraph", "section"} <= kinds
    assert not hasattr(source, "add_referent")
    observation = source.observe(source.paragraphs()[0])
    assert isinstance(observation, SourceObservation)
    assert "Purchase Action" not in observation.native_handle
