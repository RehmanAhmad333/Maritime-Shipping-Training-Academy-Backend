from sqlalchemy import Column, Integer, String, Text, Numeric, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base

class ShippingService(Base):
    __tablename__ = "shipping_services"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    service_type = Column(String(50))  # ship_handling, cargo_management, fleet_tracking
    price = Column(Numeric(10,2))
    duration_days = Column(Integer)
    features = Column(JSONB)  # list of features
    image_url = Column(String)
    status = Column(String(50), default="active")
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())