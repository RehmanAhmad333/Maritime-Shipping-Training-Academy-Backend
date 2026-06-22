from datetime import datetime
from pydantic import BaseModel

class MyBookingResponse(BaseModel):
    id: int
    trip_id: int
    user_id: int
    number_of_people: int
    total_price: float
    status: str
    payment_status: str
    created_at: datetime
    updated_at: datetime

    # Highlight: This line allows Pydantic to read SQLAlchemy objects
    model_config = {
        "from_attributes": True
    }
class BookingResponse(BaseModel):
    id: int
    user_id: int
    trip_id: int
    booking_date: datetime
    trip_date: datetime
    number_of_people: int
    total_price: float
    status: str
    payment_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

