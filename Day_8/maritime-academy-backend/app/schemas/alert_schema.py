from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EmailAlertCreate(BaseModel):
    filters_json: dict  # {"category": "Maritime", "price_max": 3000, "location": "Italy"}
    frequency: Optional[str] = "weekly"  # daily, weekly

class EmailAlertResponse(BaseModel):
    id: int
    user_id: int
    filters_json: dict
    is_active: bool
    frequency: str
    last_sent_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class AlertResponse(BaseModel):
    message: str
    alert_id: int

class AlertToggleResponse(BaseModel):
    active: bool