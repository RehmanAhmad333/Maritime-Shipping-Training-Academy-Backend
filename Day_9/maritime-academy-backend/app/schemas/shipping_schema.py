from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ShippingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    service_type: str
    price: float
    duration_days: int
    features: Optional[List[str]] = None
    image_url: Optional[str] = None

class ShippingResponse(ShippingCreate):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ShippingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    service_type: Optional[str] = None
    price: Optional[float] = None
    duration_days: Optional[int] = None
    features: Optional[List[str]] = None
    image_url: Optional[str] = None