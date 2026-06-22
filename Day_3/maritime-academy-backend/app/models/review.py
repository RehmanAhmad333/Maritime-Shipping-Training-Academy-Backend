from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, TIMESTAMP, func
from app.core.database import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    is_featured = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())