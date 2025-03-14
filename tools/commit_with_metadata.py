#!/usr/bin/env python3
"""
Create a Git commit with custom author/committer dates and attach JSON metadata.

Metadata is stored in:
  - git note on the commit (refs/notes/commits)
  - append-only ledger at metadata/commits.jsonl

Research / tooling for this repository — see docs/GIT_COMMIT_METADATA.md.
"""

from __future__ import annotations
