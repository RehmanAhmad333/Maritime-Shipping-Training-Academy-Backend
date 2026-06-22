from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP, func
from app.core.database import Base

class ProgressTracking(Base):
    __tablename__ = "progress_tracking"

    id = Column(Integer, primary_key=True, index=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False)
    module_name = Column(String(255), nullable=False)
    completed = Column(Boolean, default=False)
    completion_date = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())