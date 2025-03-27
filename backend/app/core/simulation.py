"""Weekly pricing simulation engine."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Literal

from app.core.demand import DemandParams, demand_qty


@dataclass
