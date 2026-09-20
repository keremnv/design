"""Read-only access to the sealed World sqlite."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

WORLD_ID = "v0"
WORLD_REVISION = 242
WORLD_HASH = "dc2e7e45c1327fc997691b4fa4071c5fd44edb6aed2b57e2d1e4e4c70a471eb8"
SQLITE_SHA256 = "b2053bcf7c9e02a39b64a77065ff952c4357e494b024292c08eb9a6ff9481a4c"


def default_sqlite_path() -> Path:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "world" / "world.sqlite",
        Path.cwd() / "world" / "world.sqlite",
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError("world/world.sqlite not found relative to application or cwd")


def connect(sqlite_path: Path | None = None) -> sqlite3.Connection:
    path = Path(sqlite_path) if sqlite_path else default_sqlite_path()
    uri = path.resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    return conn


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def world_binding(conn: sqlite3.Connection, sqlite_path: Path | None = None) -> dict:
    path = Path(sqlite_path) if sqlite_path else default_sqlite_path()
    meta = conn.execute("SELECT world_id, revision FROM _world_meta WHERE singleton = 1").fetchone()
    digest = sha256_file(path)
    return {
        "world_id": meta["world_id"] if meta else None,
        "revision": meta["revision"] if meta else None,
        "expected_world_hash": WORLD_HASH,
        "sqlite_path": str(path.resolve()),
        "sqlite_sha256": digest,
        "sqlite_sha256_matches_binding": digest == SQLITE_SHA256,
    }
