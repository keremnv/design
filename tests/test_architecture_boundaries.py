"""Executable architectural dependency boundary.

Rule (docs/ARCHITECTURE.md):

    APPLICATION may depend on ONTOLOGY read/construction surfaces.
    ONTOLOGY may depend on EVIDENCE adapters and the WORLD KERNEL.
    WORLD KERNEL must not depend on application/domain packages.

This test scans imports with the standard library only. It enforces the
forbidden reverse edges, not package-name equality with the conceptual
architecture: documented application-composition edges elsewhere (for
example ``semantic_binding`` using ``governance.model_adjudicator``) are
not rejected here.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
WORLD_ROOT = REPOSITORY_ROOT / "ontology_author" / "world"
WORLD_CORE_ROOT = WORLD_ROOT / "core"
EVIDENCE_ROOT = REPOSITORY_ROOT / "ontology_author" / "evidence"
PROGRAM_ROOT = REPOSITORY_ROOT / "ontology_author" / "program_spine"

# Application/domain regions the World layer must never import. ``profiles``
# is a top-level application package; the rest live under ``ontology_author``.
FORBIDDEN_WORLD_IMPORTS = (
    "ontology_author.authority",
    "ontology_author.semantic_binding",
    "ontology_author.governance",
    "ontology_author.program_spine",
    "ontology_author.software_governance",
    "ontology_author.config_routes",
    "ontology_author.construction_boundary",
    "profiles",
)

# The kernel stores generic shapes; it must not reach up into ontology
# construction, read surfaces, or serving code.
FORBIDDEN_CORE_IMPORTS = (
    "ontology_author.world.runtime",
    "ontology_author.world.explorer",
    "ontology_author.world.server",
    "ontology_author.world.cli",
    "ontology_author.world.workspaces",
)


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                package = path.relative_to(REPOSITORY_ROOT).parts[:-1]
                package = package[:len(package) - node.level + 1]
                module = ".".join((*package, *((module,) if module else ())))
            if module:
                modules.add(module)
                modules.update(f"{module}.{alias.name}" for alias in node.names)
    return modules


def _violations(root: Path, forbidden: tuple[str, ...]) -> list[str]:
    found: list[str] = []
    for path in sorted(root.rglob("*.py")):
        for module in sorted(_imported_modules(path)):
            if module in forbidden or module.startswith(
                tuple(f"{prefix}." for prefix in forbidden)
            ):
                found.append(f"{path.relative_to(REPOSITORY_ROOT)} imports {module}")
    return found


def test_world_layer_does_not_import_application_packages():
    assert _violations(WORLD_ROOT, FORBIDDEN_WORLD_IMPORTS) == []


def test_world_kernel_does_not_import_upper_layers():
    assert _violations(WORLD_CORE_ROOT, FORBIDDEN_CORE_IMPORTS) == []


def test_evidence_adapters_do_not_import_application_rules():
    # Evidence observes and reconstructs sources; standing lives elsewhere.
    # (Reading sealed World state is allowed; assigning standing is not.)
    assert _violations(EVIDENCE_ROOT, FORBIDDEN_WORLD_IMPORTS) == []


def test_program_spine_does_not_depend_on_semantic_construction():
    forbidden = tuple(item for item in FORBIDDEN_WORLD_IMPORTS if item != "ontology_author.program_spine")
    assert _violations(PROGRAM_ROOT, forbidden) == []
