from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, func
from app.core.database import Base

class Translation(Base):
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True)
    key = Column(String(100), nullable=False)
    language = Column(String(10), nullable=False)  # en, it, tr
    translation = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())