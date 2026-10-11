from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class TripStatus(str, Enum):
    CREATED = "CREATED"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Trip(BaseModel):
    __tablename__ = "trips"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False,)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False,)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False,)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=False,)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False,)
    origin = Column(String(255), nullable=False,)
    destination = Column(String(255), nullable=False,)
    cargo_description = Column(String)
    status = Column(SQLEnum(TripStatus, name="trip_status"), default=TripStatus.CREATED,nullable=False,)
    actual_start = Column(DateTime(timezone=True),)
    actual_end = Column(DateTime(timezone=True),)
    remarks = Column(String)
    is_active = Column(Boolean, default=True, nullable=False,)
    
    company = relationship("Company", back_populates="trips",)
    branch = relationship("Branch", back_populates="trips",)
    vehicle = relationship("Vehicle", back_populates="trips",)
    driver = relationship("Driver", back_populates="trips",)
    created_by_user = relationship("User", back_populates="trips",)
   