from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, func
from app.core.database import Base

class CourseCurriculum(Base):
    __tablename__ = "course_curriculum"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    day_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    point_1 = Column(Text)
    point_2 = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())