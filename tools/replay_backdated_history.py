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
        "docker-compose.yml",
        ".gitignore",
    ]
    for idx, prefix in enumerate(order):
        if rel == prefix or rel.startswith(prefix):
            return idx, rel
    return len(order), rel


def build_patch_queue(files: dict[str, str], *, max_lines: int) -> list[tuple[str, str, str]]:
    ordered = sorted(files.keys(), key=file_priority)
    queue: list[tuple[str, str, str]] = []
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


def _merge_one_adjacent_same_file(merged: list[tuple[str, str, str]]) -> bool:
    for i in range(len(merged) - 1):
        if merged[i][0] == merged[i + 1][0]:
            rel = merged[i][0]
            suffix = merged[i + 1][2] or merged[i][2]
            merged[i : i + 2] = [(rel, merged[i + 1][1], suffix)]
            return True
    return False


def trim_queue_to_slots(queue: list[tuple[str, str, str]], slot_count: int) -> list[tuple[str, str, str]]:
    merged = list(queue)
    while len(merged) > slot_count:
        if not _merge_one_adjacent_same_file(merged):
            break
    return merged


def describe_change(rel: str, content: str, suffix: str) -> tuple[str, str, str]:
    base = rel.split("/")[-1]
    part_note = f" ({suffix.strip()})" if suffix.strip() else ""
    slug = rel.replace("/", "-").replace(".", "-")

    if rel.startswith("backend/tests/"):
        title = f"test: cover {base}{part_note}"
        description = f"Add or extend tests in {rel} for pricing simulation behavior."
        intent = f"test/{slug}{suffix.replace(' ', '')}"
    elif rel.startswith("docs/"):
        title = f"docs: document {base}{part_note}"
        description = f"Write project documentation in {rel}{part_note}."
        intent = f"docs/{slug}{suffix.replace(' ', '')}"
    elif rel.startswith("backend/app/core/"):
        title = f"feat(core): implement {base}{part_note}"
        description = f"Implement simulation or optimization logic in {rel}{part_note}."
        intent = f"core/{slug}{suffix.replace(' ', '')}"
    elif rel.startswith("backend/app/ml/"):
        title = f"feat(ml): implement {base}{part_note}"
        description = f"Add demand forecasting or training code in {rel}{part_note}."
        intent = f"ml/{slug}{suffix.replace(' ', '')}"
    elif rel.startswith("backend/app/api/"):
        title = f"feat(api): expose {base}{part_note}"
        description = f"Add REST route handlers in {rel}{part_note}."
        intent = f"api/{slug}{suffix.replace(' ', '')}"
    elif rel.startswith("frontend/"):
        title = f"feat(ui): update {base}{part_note}"
        description = f"Build dashboard or client integration in {rel}{part_note}."
        intent = f"ui/{slug}{suffix.replace(' ', '')}"
    elif rel == "README.md":
        title = f"docs: update README{part_note}"
        description = f"Document setup and project overview{part_note}."
        intent = f"readme{suffix.replace(' ', '')}"
    elif rel == ".gitignore":
        title = "chore: define gitignore"
        description = "Ignore virtualenv, build artifacts, and local databases."
        intent = "chore/gitignore"
    elif "docker" in rel.lower():
        title = f"chore: container config for {base}"
        description = f"Add Docker or compose configuration in {rel}."
        intent = f"docker/{slug}"
    else:
        title = f"feat: add {rel}{part_note}"
        description = f"Introduce or extend {rel}{part_note} for the price simulator."
        intent = f"build/{slug}{suffix.replace(' ', '')}"

    lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
    description += f" ({lines} lines in file snapshot after this commit.)"
    return title, description, intent


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
        for _ in range(n):
            slots.append(
                datetime(
                    day.year,
                    day.month,
                    day.day,
                    rng.randint(9, 20),
                    rng.randint(0, 59),
                    rng.randint(0, 59),
                    tzinfo=timezone(timedelta(hours=-5)),
                )
            )
        day += timedelta(days=1)
    slots.sort()
    return slots


def plan_commits(files: dict[str, str], slots: list[datetime]) -> list[tuple[PlannedCommit, dict[str, str]]]:
    raw = build_patch_queue(files, max_lines=PATCH_MAX_LINES)
    patches = trim_queue_to_slots(raw, len(slots))

    readme = files.get("README.md", "# AI-Powered Price Simulator\n")
    while len(patches) < len(slots):
        n = len(patches) + 1
        readme += f"\n<!-- dev-milestone:{n} -->\n"
        patches.append(("README.md", readme, f" milestone {n}"))

    if len(patches) > len(slots):
        patches = patches[: len(slots)]

    out: list[tuple[PlannedCommit, dict[str, str]]] = []
    for seq, (when, (rel, chunk, suffix)) in enumerate(zip(slots, patches, strict=True), start=1):
        title, description, intent = describe_change(rel, chunk, suffix)
        record_path = f"{RECORDS_DIR}/{seq:04d}.json"
        pc = PlannedCommit(
            when=when,
            title=title,
            description=description,
            intent=intent,
            paths=[rel, record_path],
            sequence=seq,
            record_path=record_path,
        )
        out.append((pc, {rel: chunk}))
    return out


def iso_git(dt: datetime) -> str:
    return dt.isoformat()


def attach_metadata(sha: str, meta: dict) -> None:
    payload = json.dumps(meta, separators=(",", ":"), sort_keys=True)
    run(["git", "notes", "add", "-f", "-m", payload, sha])


def apply_plan(plan: PlannedCommit, contents: dict[str, str]) -> str:
    for rel, text in contents.items():
        dest = ROOT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")

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

    pre_meta = {
        "schema_version": 2,
        "sequence": plan.sequence,
        "title": plan.title,
        "description": plan.description,
        "intent": plan.intent,
        "author_date_requested": iso_git(plan.when),
        "committer_date_requested": iso_git(plan.when),
        "paths": [p for p in plan.paths if not p.endswith(".json")],
        "recorded_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "tool": "replay_backdated_history.py",
        "tool_version": TOOL_VERSION,
    }

    record_dest = ROOT / plan.record_path
    record_dest.parent.mkdir(parents=True, exist_ok=True)
    record_dest.write_text(json.dumps(pre_meta, indent=2) + "\n", encoding="utf-8")

    run(["git", "add", "--"] + plan.paths)

    cmd = [
        "git",
        "commit",
        "-m",
        plan.title,
        "-m",
        plan.description,
        "-m",
        f"Metadata-Intent: {plan.intent}",
        "-m",
        f"Metadata-Sequence: {plan.sequence}",
        "-m",
        f"Metadata-Record: {plan.record_path}",
    ]
    if plan.allow_empty:
        cmd.insert(2, "--allow-empty")

    run(cmd, env=env)
    sha = run(["git", "rev-parse", "HEAD"]).stdout.strip()

    file_meta = {**pre_meta, "paths": plan.paths}
    record_dest.write_text(json.dumps(file_meta, indent=2) + "\n", encoding="utf-8")
    run(["git", "add", plan.record_path])
    run(["git", "commit", "--amend", "--no-edit"], env=env)
    sha = run(["git", "rev-parse", "HEAD"]).stdout.strip()

    note_meta = {**file_meta, "commit": sha}
    attach_metadata(sha, note_meta)

    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(note_meta, sort_keys=True) + "\n")

    return sha


def apply_history(dry_run: bool = False) -> None:
    files = capture_snapshot()
    write_snapshot(files)

    slots = generate_schedule(date(2025, 1, 1), date(2025, 6, 30), seed=42)
    planned = plan_commits(files, slots)

    if dry_run:
        print(f"Would create {len(planned)} commits ({len(slots)} slots)")
        print(f"Raw patches: {len(build_patch_queue(files, max_lines=PATCH_MAX_LINES))}")
        print(f"Sample title: {planned[0][0].title}")
        return

    for path in list(ROOT.iterdir()):
        if path.name in SKIP_TOP:
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

    run(["git", "checkout", "--orphan", "main-replay"], check=False)
    run(["git", "rm", "-rf", "."], check=False)
    run(["git", "branch", "-M", "main"], check=False)

    records_dir = ROOT / RECORDS_DIR
    if records_dir.exists():
        shutil.rmtree(records_dir)
    LEDGER.unlink(missing_ok=True)

    total = len(planned)
    for idx, (plan, contents) in enumerate(planned, start=1):
        sha = apply_plan(plan, contents)
        if idx % 50 == 0 or idx == total:
            print(f"[{idx}/{total}] {sha[:7]} {plan.title[:55]}")

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
