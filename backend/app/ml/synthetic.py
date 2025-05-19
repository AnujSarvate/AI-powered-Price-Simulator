"""Synthetic sales data for demand model training."""

from __future__ import annotations

import math
import random

import pandas as pd


def generate_synthetic_sales(
    n_rows: int = 2000,
    *,
    seed: int = 7,
) -> pd.DataFrame:
    rng = random.Random(seed)
    rows: list[dict] = []
    categories = ["beverage", "merch", "snack"]
