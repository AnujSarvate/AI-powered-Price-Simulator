from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    sku: str
    name: str
