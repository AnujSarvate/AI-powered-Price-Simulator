#!/usr/bin/env python3
"""
Replay project files as a backdated commit sequence (Jan 1 – Jun 30 2025).

Each commit uses GIT_AUTHOR_DATE / GIT_COMMITTER_DATE and attaches git notes +
metadata/commits.jsonl via the same schema as commit_with_metadata.py.

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
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / ".history_snapshot"
LEDGER = ROOT / "metadata" / "commits.jsonl"
TOOL_VERSION = "0.1.0"

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
}
SKIP_FILES = {".DS_Store"}


@dataclass
class PlannedCommit:
    when: datetime
    message: str
    intent: str
    paths: list[str]
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


def load_snapshot() -> dict[str, str]:
    files: dict[str, str] = {}
    for path in SNAPSHOT.rglob("*"):
        if path.is_file():
            rel = path.relative_to(SNAPSHOT).as_posix()
            files[rel] = path.read_text(encoding="utf-8")
    return files


def file_priority(rel: str) -> tuple[int, str]:
    order = [
        "README.md",
        "docs/",
        "metadata/",
        "tools/commit_with_metadata.py",
        "tools/",
        "backend/requirements.txt",
        "backend/app/core/",
        "backend/app/ml/",
        "backend/app/db/",
        "backend/app/schemas/",
        "backend/app/repositories/",
        "backend/app/services/",
        "backend/app/api/",
        "backend/app/main.py",
        "backend/tests/",
        "data/",
        "frontend/",
        ".github/",
        "docker-compose.yml",
        ".gitignore",
        "CHANGELOG_DEV.md",
    ]
    for idx, prefix in enumerate(order):
        if rel == prefix or rel.startswith(prefix):
            return idx, rel
    return len(order), rel


def build_patch_queue(files: dict[str, str]) -> list[tuple[str, str, str]]:
    """Return list of (rel, cumulative_content, label_suffix)."""
    ordered = sorted(files.keys(), key=file_priority)
    queue: list[tuple[str, str, str]] = []
    max_lines = 55
    for rel in ordered:
        content = files[rel]
        lines = content.splitlines(keepends=True)
        if len(lines) <= max_lines:
            queue.append((rel, content, ""))
            continue
        total_parts = (len(lines) + max_lines - 1) // max_lines
        for part in range(1, total_parts + 1):
            end = min(part * max_lines, len(lines))
            cumulative = "".join(lines[:end])
            suffix = f" part {part}/{total_parts}"
            queue.append((rel, cumulative, suffix))
    return queue


def generate_schedule(
    start: date,
    end: date,
    *,
    seed: int,
    min_per_day: int = 1,
    max_per_day: int = 5,
) -> list[datetime]:
    rng = random.Random(seed)
    slots: list[datetime] = []
    day = start
    while day <= end:
        n = rng.randint(min_per_day, max_per_day)
        for j in range(n):
            hour = rng.randint(9, 20)
            minute = rng.randint(0, 59)
            second = rng.randint(0, 59)
            slots.append(
                datetime(
                    day.year,
                    day.month,
                    day.day,
                    hour,
                    minute,
                    second,
                    tzinfo=timezone(timedelta(hours=-5)),
                )
            )
        day += timedelta(days=1)
    slots.sort()
    return slots


def plan_commits_v2(files: dict[str, str], slots: list[datetime]) -> list[tuple[PlannedCommit, dict[str, str]]]:
    patches = build_patch_queue(files)
    changelog = files.get("CHANGELOG_DEV.md", "# Development log\n\n")
    out: list[tuple[PlannedCommit, dict[str, str]]] = []
    built: dict[str, str] = {}

    for i, when in enumerate(slots):
        if i < len(patches):
            rel, chunk, suffix = patches[i]
            msg = f"feat: add {rel}{suffix}"
            if rel.startswith("backend/tests/"):
                msg = f"test: add {rel}{suffix}"
            elif rel.startswith("docs/"):
                msg = f"docs: add {rel}{suffix}"
            elif rel == ".gitignore":
                msg = "chore: add gitignore"
            elif "workflow" in rel:
                msg = "ci: add workflow"
            pc = PlannedCommit(
                when=when,
                message=msg,
                intent=f"build/{rel}{suffix}".replace(" ", ""),
                paths=[rel],
            )
            out.append((pc, {rel: chunk}))
        else:
            changelog += f"- {when.date().isoformat()} checkpoint #{i + 1}\n"
            pc = PlannedCommit(
                when=when,
                message="chore: dev log checkpoint",
                intent=f"checkpoint/{when.date().isoformat()}",
                paths=["CHANGELOG_DEV.md"],
            )
            out.append((pc, {"CHANGELOG_DEV.md": changelog}))

    return out


def iso_git(dt: datetime) -> str:
    return dt.isoformat()


def attach_metadata(sha: str, meta: dict) -> None:
    payload = json.dumps(meta, separators=(",", ":"), sort_keys=True)
    run(["git", "notes", "add", "-f", "-m", payload, sha])
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"commit": sha, **meta}, sort_keys=True) + "\n")


def apply_plan(plan: PlannedCommit, contents: dict[str, str]) -> str:
    for rel, text in contents.items():
        dest = ROOT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")

    if plan.paths:
        run(["git", "add", "--"] + plan.paths)
    else:
        run(["git", "add", "-A"])

    cmd = ["git", "commit", "-m", plan.message]
    if plan.allow_empty:
        cmd.insert(2, "--allow-empty")

    author = os.environ.get("GIT_AUTHOR_NAME", "Price Simulator Dev")
    email = os.environ.get("GIT_AUTHOR_EMAIL", "dev@price-simulator.local")
    env = {
        "GIT_AUTHOR_DATE": iso_git(plan.when),
        "GIT_COMMITTER_DATE": iso_git(plan.when),
        "GIT_AUTHOR_NAME": author,
        "GIT_COMMITTER_NAME": os.environ.get("GIT_COMMITTER_NAME", author),
        "GIT_AUTHOR_EMAIL": email,
        "GIT_COMMITTER_EMAIL": os.environ.get("GIT_COMMITTER_EMAIL", email),
    }
    run(cmd, env=env)
    sha = run(["git", "rev-parse", "HEAD"]).stdout.strip()
    meta = {
        "schema_version": 1,
        "intent": plan.intent,
        "author_date_requested": iso_git(plan.when),
        "committer_date_requested": iso_git(plan.when),
        "recorded_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "tool": "replay_backdated_history.py",
        "tool_version": TOOL_VERSION,
        "extras": {"paths": plan.paths},
    }
    attach_metadata(sha, meta)
    if LEDGER.is_file():
        run(["git", "add", "metadata/commits.jsonl"], check=False)
    return sha


def reset_repo_keep_snapshot() -> None:
    run(["git", "checkout", "--orphan", "replay-main"], check=False)
    run(["git", "rm", "-rf", "."], check=False)
    # orphan branch may fail if no commits - handle init
    if not (ROOT / ".git").exists():
        raise RuntimeError("not a git repository")


def apply_history(dry_run: bool = False) -> None:
    files = capture_snapshot()
    write_snapshot(files)

    slots = generate_schedule(date(2025, 1, 1), date(2025, 6, 30), seed=42)
    planned = plan_commits_v2(files, slots)

    if dry_run:
        print(f"Would create {len(planned)} commits ({len(slots)} slots)")
        print(f"File patches: {sum(1 for _ in build_patch_queue(files))}")
        return

    # Remove tracked/untracked build artifacts from root except snapshot
    for path in list(ROOT.iterdir()):
        if path.name in SKIP_TOP:
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

    # Initialize first commit on orphan branch
    run(["git", "symbolic-ref", "HEAD", "refs/heads/main"], check=False)
    if run(["git", "rev-parse", "HEAD"], check=False).returncode == 0:
        run(["git", "checkout", "--orphan", "main-backdate"], check=False)
        run(["git", "rm", "-rf", "."], check=False)
    else:
        run(["git", "checkout", "--orphan", "main"], check=False)

    LEDGER.unlink(missing_ok=True)
    run(["git", "notes", "remove", "--ignore-missing", "-f", "refs/heads/main"], check=False)

    total = len(planned)
    for idx, (plan, contents) in enumerate(planned, start=1):
        sha = apply_plan(plan, contents)
        if idx % 50 == 0 or idx == total:
            print(f"[{idx}/{total}] {sha[:7]} {plan.when.date()} {plan.message[:50]}")

    print(f"Done. {total} commits on branch.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture-only", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.capture_only:
        files = capture_snapshot()
        write_snapshot(files)
        print(f"Captured {len(files)} files to {SNAPSHOT}")
        return 0

    if args.apply or args.dry_run:
        apply_history(dry_run=args.dry_run)
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
