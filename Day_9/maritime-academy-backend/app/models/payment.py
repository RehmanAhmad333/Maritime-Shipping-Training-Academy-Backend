from sqlalchemy import Column, Integer, ForeignKey, Numeric, String, TIMESTAMP, func
from app.core.database import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(10,2), nullable=False)
    currency = Column(String(10), default="USD")
    payment_method = Column(String(50))
    stripe_payment_intent_id = Column(String(255))
    status = Column(String(50), default="pending")
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())