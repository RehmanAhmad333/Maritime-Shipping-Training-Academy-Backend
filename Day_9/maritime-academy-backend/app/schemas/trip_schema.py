from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

# ---------- Trip Schemas ----------
class TripBase(BaseModel):
    location_name: str
    country: str
    start_date: date
    duration_days: int
    max_slots: int
    price: float
    description: Optional[str] = None
    image_url: Optional[str] = None
    rating: Optional[float] = 0.0
    is_featured: Optional[bool] = False
    status: Optional[str] = "active"

class TripCreate(TripBase):
    pass

class TripUpdate(BaseModel):
    location_name: Optional[str] = None
    country: Optional[str] = None
    start_date: Optional[date] = None
    duration_days: Optional[int] = None
    max_slots: Optional[int] = None
    price: Optional[float] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    rating: Optional[float] = None
    is_featured: Optional[bool] = None
    status: Optional[str] = None

class TripResponse(TripBase):
    id: int
    booked_slots: int
    available_slots: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- Trip Booking Schemas ----------
class TripBookingRequest(BaseModel):
    number_of_people: Optional[int] = 1

    class Config:
        from_attributes = True

class TripBookingResponse(BaseModel):
    message: str
    booking_id: int
    trip_id: int
    total_price: float
    number_of_people: int
    booking_date: datetime


# ---------- Paginated Trip Response ----------
class TripListResponse(BaseModel):
    total: int
    page: int
    pages: int
    trips: List[TripResponse]
 