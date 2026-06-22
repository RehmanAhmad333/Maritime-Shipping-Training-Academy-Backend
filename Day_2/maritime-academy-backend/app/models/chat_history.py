from sqlalchemy import Column, Integer, Text, ForeignKey, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    reply = Column(Text)
    context_snapshot = Column(JSONB)
    created_at = Column(TIMESTAMP, server_default=func.now())