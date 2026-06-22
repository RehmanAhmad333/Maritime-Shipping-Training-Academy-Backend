from sqlalchemy import Column, Integer, ForeignKey, Numeric, String, TIMESTAMP, func
from app.core.database import Base

class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    enrollment_date = Column(TIMESTAMP, server_default=func.now())
    progress = Column(Numeric(5,2), default=0.00)  # 0-100
    status = Column(String(50), default="active")  # active, completed, dropped
    completion_date = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())