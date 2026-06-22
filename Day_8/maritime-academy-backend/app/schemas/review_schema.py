from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReviewResponse(BaseModel):
    id: int
    user_id: Optional[int]
    trip_id: Optional[int]
    reviewer_name: str
    rating: int
    comment: Optional[str]
    is_featured: bool
    created_at: datetime

    class Config:
        from_attributes = True