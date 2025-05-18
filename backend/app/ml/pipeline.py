"""Train and evaluate demand regression models."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.ml.synthetic import generate_synthetic_sales

FEATURE_COLUMNS = [
    "log_price",
    "week_of_year",
    "promo_active",
    "competitor_price_ratio",
    "category_beverage",
    "category_merch",
    "category_snack",
]


@dataclass
class TrainResult:
    model_id: str
    metrics: dict[str, float]
    artifact_path: str


def _baseline_mae(y_test: pd.Series) -> float:
    pred = [float(y_test.mean())] * len(y_test)
    return float(mean_absolute_error(y_test, pred))


def train_demand_model(
    df: pd.DataFrame | None = None,
    *,
    artifacts_dir: Path,
    test_size: float = 0.2,
    random_state: int = 42,
) -> TrainResult:
