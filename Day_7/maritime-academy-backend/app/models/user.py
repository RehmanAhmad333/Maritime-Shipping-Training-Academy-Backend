from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20))
    role = Column(String(50), default="student")  # student, admin, trainer
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())