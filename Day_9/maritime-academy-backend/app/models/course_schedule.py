from sqlalchemy import Column, Integer, String, Date, ForeignKey, TIMESTAMP, func
from app.core.database import Base

class CourseSchedule(Base):
    __tablename__ = "course_schedules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    time_slot = Column(String(100))
    capacity = Column(Integer, nullable=False)
    booked = Column(Integer, default=0)
    status = Column(String(50), default="available")
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())