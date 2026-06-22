from sqlalchemy import Column, Integer, String, BigInteger, TIMESTAMP, func
from app.core.database import Base

class PlatformStat(Base):
    __tablename__ = "platform_stats"

    id = Column(Integer, primary_key=True)
    stat_key = Column(String(100), unique=True, nullable=False)
    stat_value = Column(BigInteger, nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())