# Backdated commits and attached metadata (research notes)

This document describes **what Git allows**, **how GitHub interprets dates**, and **patterns for binding structured metadata to each commit**—for experiments in this repository, not as guidance to misrepresent work history elsewhere.

---

## 1. Two timestamps on every commit

Each commit object stores four fields:

| Field | Meaning |
|-------|---------|
| `author` | Who wrote the change |
| `author date` | When the change was originally written |
| `committer` | Who created the commit object (often same as author) |
| `committer date` | When the commit object was created |

**Backdating** means setting `author date` and/or `committer date` to a chosen instant before `git commit` runs.

Environment variables (ISO 8601 or Unix epoch):

```bash
export GIT_AUTHOR_DATE="2025-03-15T14:30:00-05:00"
export GIT_COMMITTER_DATE="2025-03-15T14:30:00-05:00"
git commit -m "example"
```

Or inline:

```bash
GIT_AUTHOR_DATE="2025-03-15T14:30:00" GIT_COMMITTER_DATE="2025-03-15T14:30:00" git commit -m "example"
```

**Feasibility:** Yes—Git accepts arbitrary valid dates. No cryptographic tie to wall-clock time unless you use **signed commits** (signature time is separate) or external audit logs.

---

## 2. What GitHub (and others) use

- **Contribution graph** generally uses the **author date** on commits that reach the default branch, with email/account linking rules.
- **Commit UI** shows author and committer; they can differ (rebase, cherry-pick, `am`end).
- **Metadata in `git notes`** is stored in Git but **not shown** on the default GitHub commit page; notes can be pushed and fetched by collaborators who know to look.
- Reviewers can run `git log --format=fuller`, compare notes, check reflog (local), and inspect patch coherence.

For a research project, record **both** intended backdate and **actual** creation time in metadata (see §4).

---

## 3. Where to attach metadata

| Mechanism | Pros | Cons |
|-----------|------|------|
| **Commit message trailers** (`Key: value` after blank line) | Travels with commit; visible on GitHub | Unstructured unless you standardize; noisy |
| **`git notes`** | Structured JSON; doesn’t change commit hash of parent tree | Extra ref to push; easy to miss on hosting UI |
| **Signed commit + signed tag** | Integrity | Doesn’t prove backdate is “true” |
| **External ledger** (JSONL file in repo, updated each commit) | Easy to query; auditable | Ledger commit itself has a real timestamp unless also backdated |
| **Rebase / filter-repo rewrite** | Bulk date changes | Rewrites SHAs; destructive on shared branches |

**Recommended for this repo:** combine **trailers** (human-readable summary) + **`git notes`** (full JSON) + **append-only ledger** (`metadata/commits.jsonl`) for tooling.

---

## 4. Metadata schema (v2 — per commit)

Each replayed commit adds **`metadata/records/NNNN.json`** where `NNNN` is the 1-based sequence. The JSON **`title`** and **`description`** match the Git commit subject and body. The commit message also includes trailers:

- `Metadata-Intent`
- `Metadata-Sequence`
- `Metadata-Record`

Git notes duplicate the same JSON plus the final `commit` SHA.

## 5. Metadata schema (v1, legacy)

Each logical commit should carry:

```json
{
  "schema_version": 1,
  "intent": "simulation_kernel_baseline",
  "author_date_requested": "2025-03-15T14:30:00-05:00",
  "committer_date_requested": "2025-03-15T14:30:00-05:00",
  "recorded_at_utc": "2026-09-22T22:31:00Z",
  "tool": "commit_with_metadata.py",
  "tool_version": "0.1.0",
  "extras": {}
}
```

`recorded_at_utc` is wall-clock when the tool ran—useful for research on backdating vs. creation time.

---

## 5. Tooling in this repository

```bash
python tools/commit_with_metadata.py \
  --author-date "2025-03-15T14:30:00-05:00" \
  --message "feat(sim): add constant-elasticity demand" \
  --intent simulation_kernel_baseline \
  -- metadata/extra.json \
  -- path/to/file.py
```

The script:

1. Stages listed paths (or `--allow-empty`).
2. Commits with `GIT_AUTHOR_DATE` / `GIT_COMMITTER_DATE`.
3. Adds a **note** on the new commit SHA with full JSON metadata.
4. Appends one line to `metadata/commits.jsonl`.

Read metadata back:

```bash
python tools/commit_with_metadata.py show HEAD
python tools/commit_with_metadata.py show <sha>
```

Push notes to origin (when remote exists):

```bash
git push origin refs/notes/commits
```

---

## 6. Bulk / scheduled backdating (experiments)

For **research batches** (e.g. simulating a timeline), prefer:

1. Generate a **manifest CSV** (`planned_date`, `message`, `intent`, `files`).
2. Apply commits **one manifest row at a time** with the tool (keeps metadata consistent).
3. Never rewrite `main` after push without documenting SHA migration.

Avoid empty noise commits; each row should map to a real file change when possible so history stays analyzable.

---

## 7. Limits and ethics (project framing)

| Question | Answer |
|----------|--------|
| Can dates be backdated? | Yes, locally and when pushed. |
| Can metadata be attached per commit? | Yes (notes, trailers, ledger). |
| Does metadata prove the backdate is historically accurate? | No—only your ledger + signatures + external systems can support audit stories. |
| Good research questions | Note push ergonomics; graph vs. author date; detecting incoherent backdated series; reproducible manifests. |

---

## 8. References

- `git commit` environment variables: Git documentation (`GIT_AUTHOR_DATE`, `GIT_COMMITTER_DATE`).
- `git notes add`, `git notes show`, `refs/notes/commits`.
- Conventional Commit trailers and `git interpret-trailers`.
