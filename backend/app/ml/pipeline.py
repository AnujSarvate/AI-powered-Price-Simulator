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
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    data = df if df is not None else generate_synthetic_sales()

    missing = [c for c in FEATURE_COLUMNS + ["units_sold"] if c not in data.columns]
    if missing:
        raise ValueError(f"missing columns: {missing}")

    x = data[FEATURE_COLUMNS]
    y = data["units_sold"]
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=test_size, random_state=random_state
    )

    pipe = Pipeline(
        steps=[
            ("model", RandomForestRegressor(n_estimators=120, random_state=random_state)),
        ]
    )
    pipe.fit(x_train, y_train)
    preds = pipe.predict(x_test)

    metrics = {
        "mae": float(mean_absolute_error(y_test, preds)),
        "r2": float(r2_score(y_test, preds)),
        "baseline_mae": _baseline_mae(y_test),
    }

    model_id = str(uuid4())
    artifact = artifacts_dir / f"{model_id}.joblib"
    meta = artifacts_dir / f"{model_id}.json"
    joblib.dump(pipe, artifact)
    meta.write_text(json.dumps({"features": FEATURE_COLUMNS, "metrics": metrics}, indent=2))

    return TrainResult(model_id=model_id, metrics=metrics, artifact_path=str(artifact))


def predict_units(model_path: Path, rows: list[dict]) -> list[float]:
    pipe = joblib.load(model_path)
    df = pd.DataFrame(rows)
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"missing feature column: {col}")
