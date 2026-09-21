"""Publish each reconstruction at a fresh address using the existing Project.

The default Project rebuild replaces its current bundle. This acceptance
workflow deliberately allocates a separate Project root per revision and never
reuses one. It is not a generic history manager or a new core primitive.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ontology_author.world import Project, RunResult


def build(source_root: Path, revision_root: Path, *, construction: Path | None = None) -> RunResult:
    revision_root = Path(revision_root)
    # Exclusive reservation rejects overwrites, including concurrent builders.
    revision_root.mkdir(parents=True, exist_ok=False)
    return Project(revision_root, project_root=source_root).run(
        construction or Path(__file__).with_name("construction.py")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("revision_root", type=Path, help="new, unused publication directory")
    parser.add_argument("--sources", type=Path, default=Path(__file__).with_name("fixture"))
    args = parser.parse_args()
    result = build(args.sources, args.revision_root)
    if not result.succeeded:
        raise SystemExit(f"{result.reason}: {result.errors}")
    print(result.world_dir)


if __name__ == "__main__":
    main()
