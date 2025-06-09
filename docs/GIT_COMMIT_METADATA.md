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

