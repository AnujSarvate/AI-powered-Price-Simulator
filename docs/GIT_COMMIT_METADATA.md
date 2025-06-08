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
