from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.ml.pipeline import FEATURE_COLUMNS, predict_units, train_demand_model
from app.ml.synthetic import generate_synthetic_sales

router = APIRouter(prefix="/models", tags=["models"])


class TrainResponse(BaseModel):
    model_id: str
    metrics: dict[str, float]
    artifact_path: str


class PredictRequest(BaseModel):
    rows: list[dict] = Field(default_factory=list)


class PredictResponse(BaseModel):
    predictions: list[float]


@router.post("/train", response_model=TrainResponse)
def train_model(use_synthetic: bool = True) -> TrainResponse:
    df = generate_synthetic_sales() if use_synthetic else None
    result = train_demand_model(df, artifacts_dir=Path(settings.artifacts_dir))
    return TrainResponse(
        model_id=result.model_id,
        metrics=result.metrics,
        artifact_path=result.artifact_path,
    )

