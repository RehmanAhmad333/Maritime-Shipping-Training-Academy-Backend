from sqlalchemy import Column, Integer, Boolean, String, ForeignKey, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base

class EmailAlert(Base):
    __tablename__ = "email_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filters_json = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    frequency = Column(String(20), default="weekly")  # daily, weekly
    last_sent_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())