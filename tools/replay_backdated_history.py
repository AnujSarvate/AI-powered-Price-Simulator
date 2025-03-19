#!/usr/bin/env python3
"""
Replay project files as a backdated commit sequence (Jan 1 – Jun 30 2025).

Each commit includes:
  - Subject + body derived from structured metadata (visible on GitHub)
  - metadata/records/NNNN.json describing that exact commit
  - git note on the commit SHA (includes final commit hash)

Usage (from repo root):
  python tools/replay_backdated_history.py --apply
"""

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / ".history_snapshot"
RECORDS_DIR = "metadata/records"
LEDGER = ROOT / "metadata" / "commits.jsonl"
TOOL_VERSION = "0.2.0"
PATCH_MAX_LINES = 6

SKIP_TOP = {".git", ".history_snapshot"}

SKIP_DIRS = {
    ".git",
    ".history_snapshot",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "artifacts",
    "htmlcov",
    ".pytest_cache",
    "metadata/records",
}
SKIP_FILES = {".DS_Store"}
SKIP_CAPTURE_PREFIXES = (
    "metadata/commits.jsonl",
    "metadata/records/",
    "CHANGELOG_DEV.md",
)


@dataclass
class PlannedCommit:
    when: datetime
    title: str
    description: str
    intent: str
    paths: list[str]
    sequence: int
    record_path: str
    allow_empty: bool = False


def run(cmd: list[str], *, env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        env=merged,
        text=True,
        capture_output=True,
    )
    if check and proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "").strip())
    return proc


def capture_snapshot() -> dict[str, str]:
    files: dict[str, str] = {}
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(SKIP_CAPTURE_PREFIXES):
            continue
        parts = set(rel.split("/"))
        if parts & SKIP_DIRS:
            continue
        if path.name in SKIP_FILES:
            continue
        if rel.startswith(".git/"):
            continue
        if rel.endswith((".pyc", ".db", ".joblib")):
            continue
        files[rel] = path.read_text(encoding="utf-8", errors="replace")
    return files


def write_snapshot(files: dict[str, str]) -> None:
    if SNAPSHOT.exists():
        shutil.rmtree(SNAPSHOT)
    for rel, content in files.items():
        dest = SNAPSHOT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")


def file_priority(rel: str) -> tuple[int, str]:
    order = [
        "README.md",
        "docs/",
        "metadata/schema",
        "tools/commit_with_metadata.py",
        "tools/",
        "backend/requirements.txt",
