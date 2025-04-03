from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    sku: str
    name: str
    unit_cost: float = Field(ge=0)
    list_price: float = Field(gt=0)
    category: str = "general"
    elasticity: float = Field(gt=0)
    q0: float = Field(gt=0, default=100.0)


class ProductRead(ProductCreate):
    product_id: str

    model_config = {"from_attributes": True}


class ProductUpdate(BaseModel):
    name: str | None = None
    unit_cost: float | None = Field(default=None, ge=0)
    list_price: float | None = Field(default=None, gt=0)
    category: str | None = None
    elasticity: float | None = Field(default=None, gt=0)
    q0: float | None = Field(default=None, gt=0)
