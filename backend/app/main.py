from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, models_ml, products, scenarios
from app.config import settings
from app.db.session import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI-Powered Price Simulator", version=settings.app_version)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/v1")
app.include_router(products.router, prefix="/v1")
app.include_router(scenarios.router, prefix="/v1")
app.include_router(models_ml.router, prefix="/v1")
