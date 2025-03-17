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
    return sha


def attach_note(root: Path, sha: str, metadata: dict[str, Any]) -> None:
    payload = json.dumps(metadata, separators=(",", ":"), sort_keys=True)
    r = run_git(["notes", "add", "-f", "-m", payload, sha], cwd=root)
    if r.returncode != 0:
        raise RuntimeError(f"git notes failed: {r.stderr or r.stdout}")


def append_ledger(root: Path, sha: str, metadata: dict[str, Any]) -> None:
    ledger = root / LEDGER_PATH
    ledger.parent.mkdir(parents=True, exist_ok=True)
    row = {"commit": sha, **metadata}
    with ledger.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")


def cmd_commit(args: argparse.Namespace) -> int:
    root = repo_root()
    committer_date = args.committer_date or args.author_date

    if not args.allow_empty and not args.paths:
        print("error: pass file paths or --allow-empty", file=sys.stderr)
        return 2

    metadata = build_metadata(
        author_date=args.author_date,
        committer_date=committer_date,
        intent=args.intent,
        extras_files=args.extras,
        root=root,
    )

    sha = stage_and_commit(
        root,
        paths=args.paths,
        message=args.message,
        author_date=args.author_date,
        committer_date=committer_date,
        allow_empty=args.allow_empty,
    )
    attach_note(root, sha, metadata)
    append_ledger(root, sha, metadata)

    print(sha)
    if args.print_metadata:
        print(json.dumps(metadata, indent=2))
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    root = repo_root()
    rev = args.rev or "HEAD"
    r = run_git(["notes", "show", rev], cwd=root)
    if r.returncode != 0:
        print(r.stderr or r.stdout, file=sys.stderr)
        return 1
    try:
        data = json.loads(r.stdout.strip())
        print(json.dumps(data, indent=2))
    except json.JSONDecodeError:
        print(r.stdout)
    return 0


def cmd_log_ledger(args: argparse.Namespace) -> int:
    root = repo_root()
    ledger = root / LEDGER_PATH
    if not ledger.is_file():
        print("(empty ledger)", file=sys.stderr)
        return 0
    lines = ledger.read_text(encoding="utf-8").strip().splitlines()
    for line in lines[-args.tail :]:
        print(line)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Commit with backdated timestamps and JSON metadata.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_commit = sub.add_parser("commit", help="Stage paths, backdate, commit, attach note + ledger")
    p_commit.add_argument(
        "--author-date",
        required=True,
        help='ISO 8601 timestamp, e.g. "2025-03-15T14:30:00-05:00"',
    )
    p_commit.add_argument(
        "--committer-date",
        help="Defaults to --author-date",
    )
    p_commit.add_argument("--message", "-m", required=True)
    p_commit.add_argument(
        "--intent",
        help="Short label stored in metadata (e.g. phase0_demand_kernel)",
    )
    p_commit.add_argument(
        "--extras",
        action="append",
        default=[],
        help="JSON object file merged into metadata.extras (repeatable)",
    )
    p_commit.add_argument("--allow-empty", action="store_true")
    p_commit.add_argument("--print-metadata", action="store_true")
    p_commit.add_argument("paths", nargs="*")
    p_commit.set_defaults(func=cmd_commit)

    p_show = sub.add_parser("show", help="Print git note JSON for a revision")
    p_show.add_argument("rev", nargs="?", default="HEAD")
    p_show.set_defaults(func=cmd_show)

    p_ledger = sub.add_parser("ledger", help="Tail metadata/commits.jsonl")
    p_ledger.add_argument("--tail", type=int, default=20)
