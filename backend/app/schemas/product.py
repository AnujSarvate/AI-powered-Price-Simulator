from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    sku: str
    name: str
    unit_cost: float = Field(ge=0)
    list_price: float = Field(gt=0)
    category: str = "general"
    elasticity: float = Field(gt=0)
    q0: float = Field(gt=0, default=100.0)

