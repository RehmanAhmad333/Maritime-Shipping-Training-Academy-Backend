from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EnrollmentCreate(BaseModel):
    course_id: int

class EnrollmentResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    enrollment_date: datetime
    progress: float
    status: str
    completion_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True