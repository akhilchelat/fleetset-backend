from sqlalchemy import (Column, Float, Integer, DateTime, ForeignKey)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel


class VehicleTelemetry(BaseModel):
    __tablename__ = "vehicle_telemetry"

    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed = Column(Float, default=0)
    fuel_level = Column(Float)
    engine_temperature = Column(Float)
    battery_voltage = Column(Float)
    odometer = Column(Integer)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    vehicle = relationship("Vehicle", back_populates="telemetry")