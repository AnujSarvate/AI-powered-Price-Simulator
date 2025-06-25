#!/usr/bin/env python3
"""
Create a Git commit with custom author/committer dates and attach JSON metadata.

Metadata is stored in:
  - git note on the commit (refs/notes/commits)
  - append-only ledger at metadata/commits.jsonl

Research / tooling for this repository — see docs/GIT_COMMIT_METADATA.md.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TOOL_VERSION = "0.1.0"
LEDGER_PATH = Path("metadata/commits.jsonl")
SCHEMA_VERSION = 1


def repo_root() -> Path:
    out = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
    ).strip()
    return Path(out)


def run_git(
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=merged,
        text=True,
        capture_output=True,
        check=False,
    )


def parse_extra_json(paths: list[str], root: Path) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for p in paths:
        path = (root / p).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"extras file not found: {p}")
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError(f"extras file must contain a JSON object: {p}")
        merged.update(data)
    return merged


def build_metadata(
    *,
    author_date: str,
    committer_date: str,
    intent: str | None,
    extras_files: list[str],
    root: Path,
) -> dict[str, Any]:
    extras = parse_extra_json(extras_files, root) if extras_files else {}
    return {
        "schema_version": SCHEMA_VERSION,
        "intent": intent,
        "author_date_requested": author_date,
        "committer_date_requested": committer_date,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "tool": "commit_with_metadata.py",
        "tool_version": TOOL_VERSION,
        "extras": extras,
    }


def stage_and_commit(
    root: Path,
    *,
    paths: list[str],
    message: str,
    author_date: str,
    committer_date: str,
    allow_empty: bool,
) -> str:
    if paths:
        r = run_git(["add", "--", *paths], cwd=root)
        if r.returncode != 0:
            raise RuntimeError(r.stderr or r.stdout)

    cmd = ["commit", "-m", message]
    if allow_empty:
        cmd.insert(1, "--allow-empty")

    env = {
        "GIT_AUTHOR_DATE": author_date,
        "GIT_COMMITTER_DATE": committer_date,
    }
    r = run_git(cmd, env=env, cwd=root)
    if r.returncode != 0:
        raise RuntimeError(r.stderr or r.stdout)

    sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
    ).strip()
