from sqlalchemy import Column, Integer, String, Numeric, Date, Boolean, Text, TIMESTAMP, func
from app.core.database import Base

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    location_name = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    duration_days = Column(Integer, nullable=False)
    max_slots = Column(Integer, nullable=False)
    booked_slots = Column(Integer, default=0)
    rating = Column(Numeric(2,1), default=0.0)
    is_featured = Column(Boolean, default=False)
    price = Column(Numeric(10,2), nullable=False)
    description = Column(Text)
    image_url = Column(String)
    status = Column(String(50), default="active")
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())