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
