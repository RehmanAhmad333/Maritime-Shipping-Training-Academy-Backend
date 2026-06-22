from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CertificationResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    certificate_number: str
    pdf_url: Optional[str]
    issue_date: datetime
    expiry_date: Optional[datetime]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True