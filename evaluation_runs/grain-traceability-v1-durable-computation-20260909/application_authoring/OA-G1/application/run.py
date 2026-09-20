#!/usr/bin/env python3
"""Callable entrypoint for sealed-World grain-trace computations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.compute import COMPUTATIONS, run_computation  # noqa: E402
from lib.db import connect, default_sqlite_path  # noqa: E402


def load_catalog() -> dict:
    return json.loads((ROOT / "catalog.json").read_text())


def parse_params(pairs: list[str], params_json: str | None) -> dict[str, str]:
    params: dict[str, str] = {}
    if params_json:
        loaded = json.loads(params_json)
        if not isinstance(loaded, dict):
            raise ValueError("--params-json must be an object")
        params.update({str(k): "" if v is None else str(v) for k, v in loaded.items()})
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"expected NAME=VALUE, got {pair!r}")
        name, value = pair.split("=", 1)
        params[name] = value
    return params


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a parameterized grain-trace computation against the sealed World."
    )
    parser.add_argument("computation_id", nargs="?", help="Computation id from the catalog")
    parser.add_argument("--list", action="store_true", help="List computations and exit")
    parser.add_argument("--param", action="append", default=[], help="NAME=VALUE (repeatable)")
    parser.add_argument("--params-json", help="JSON object of parameters")
    parser.add_argument("--world", help="Path to world.sqlite (defaults to bound World)")
    parser.add_argument("--pretty", action="store_true", help="Indent JSON output")
    args = parser.parse_args(argv)

    catalog = load_catalog()
    if args.list or not args.computation_id:
        json.dump(catalog, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    try:
        params = parse_params(args.param, args.params_json)
    except (ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.computation_id not in COMPUTATIONS:
        print(f"unknown computation: {args.computation_id}", file=sys.stderr)
        return 2

    world_path = Path(args.world) if args.world else default_sqlite_path()
    conn = connect(world_path)
    try:
        result = run_computation(conn, args.computation_id, params)
    except (KeyError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    finally:
        conn.close()

    json.dump(result, sys.stdout, indent=2 if args.pretty else None, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
