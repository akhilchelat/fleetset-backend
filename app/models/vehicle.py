from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    Date,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class VehicleStatus:
    ACTIVE = "active"
    IN_MAINTENANCE = "in_maintenance"
    OUT_OF_SERVICE = "out_of_service"


class Vehicle(BaseModel):
    __tablename__ = "vehicles"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False,)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False,)
    registration_number = Column(String(50), unique=True, nullable=False,)
    manufacturer = Column(String(100))
    model = Column(String(100))
    vehicle_type = Column(String(50))
    year = Column(Integer)
    purchase_date = Column(Date)
    current_odometer = Column(Integer, default=0)
    status = Column(String(50), default=VehicleStatus.ACTIVE, nullable=False,)
    is_active = Column(Boolean, default=True, nullable=False)

    company = relationship("Company", back_populates="vehicles",)
    branch = relationship("Branch", back_populates="vehicles",)
    trips = relationship("Trip", back_populates="vehicle",)
    assignments = relationship("DriverVehicleAssignment", back_populates="vehicle",)
    fuel_logs = relationship("FuelLog", back_populates="vehicle",)
    maintenance_records = relationship("MaintenanceRecord", back_populates="vehicle",)
    documents = relationship("VehicleDocument", back_populates="vehicle",)
    telemetry = relationship("VehicleTelemetry", back_populates="vehicle",)