from sqlalchemy import Column, Integer, ForeignKey, Numeric, String, Date, TIMESTAMP, func
from app.core.database import Base

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    booking_date = Column(TIMESTAMP, server_default=func.now())
    trip_date = Column(Date, nullable=False)
    number_of_people = Column(Integer, default=1)
    total_price = Column(Numeric(10,2))
    status = Column(String(50), default="pending")  # pending, confirmed, cancelled
    payment_status = Column(String(50), default="unpaid")
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())