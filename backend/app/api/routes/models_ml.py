from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.ml.pipeline import FEATURE_COLUMNS, predict_units, train_demand_model
from app.ml.synthetic import generate_synthetic_sales

router = APIRouter(prefix="/models", tags=["models"])


