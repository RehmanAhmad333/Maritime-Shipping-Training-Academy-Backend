from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, func
from app.core.database import Base

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    avatar_url = Column(String)
    bio = Column(Text)
    specialization = Column(String(255))  # for trainers
    address = Column(String)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())