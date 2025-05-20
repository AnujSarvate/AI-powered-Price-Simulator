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

    for i in range(n_rows):
        category = categories[i % len(categories)]
        price = rng.uniform(5.0, 40.0)
        week = i % 52
        promo = 1 if rng.random() < 0.12 else 0
        competitor_ratio = rng.uniform(0.85, 1.15)
        eps = {"beverage": 1.4, "merch": 1.1, "snack": 1.8}[category]
        base_q = 120.0 if category != "merch" else 45.0
        season = 1.0 + 0.12 * math.sin(2 * math.pi * week / 52)
        promo_lift = 1.22 if promo else 1.0
        noise = rng.uniform(0.92, 1.08)
        units = base_q * (price / 20.0) ** (-eps) * season * promo_lift
        units *= competitor_ratio * noise
        rows.append(
            {
                "log_price": math.log(price),
                "week_of_year": week,
                "promo_active": promo,
                "competitor_price_ratio": competitor_ratio,
                f"category_{categories[0]}": 1 if category == categories[0] else 0,
                f"category_{categories[1]}": 1 if category == categories[1] else 0,
                f"category_{categories[2]}": 1 if category == categories[2] else 0,
                "units_sold": max(0.5, units),
