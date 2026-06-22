from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, func
from app.core.database import Base

class Certification(Base):
    __tablename__ = "certifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    certificate_number = Column(String(100), unique=True, nullable=False)
    pdf_url = Column(Text)
    issue_date = Column(TIMESTAMP, server_default=func.now())
    expiry_date = Column(TIMESTAMP)
    status = Column(String(50), default="active")
    created_at = Column(TIMESTAMP, server_default=func.now())