from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, TIMESTAMP, ForeignKey, func
from app.core.database import Base

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(50))
    price = Column(Numeric(10,2))
    duration_days = Column(Integer)
    instructor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    max_students = Column(Integer)
    location = Column(String(255))  # New field for course location
    image_url = Column(String)
    status = Column(String(50), default="active")
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())