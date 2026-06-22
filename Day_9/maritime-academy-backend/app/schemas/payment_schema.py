from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PaymentCreate(BaseModel):
    booking_id: int

class PaymentResponse(BaseModel):
    id: int
    user_id: int
    booking_id: int
    amount: float
    currency: str
    payment_method: Optional[str]
    stripe_payment_intent_id: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True