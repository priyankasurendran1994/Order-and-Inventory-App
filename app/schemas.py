from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)

class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class OrderItemCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)

class OrderItem(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(..., min_length=1)

class Order(BaseModel):
    id: int
    idempotency_key: str
    total_amount: float
    created_at: datetime
    items: List[OrderItem]
    
    class Config:
        from_attributes = True

class PaginatedOrders(BaseModel):
    orders: List[Order]
    next_cursor: Optional[str] = None
    has_more: bool