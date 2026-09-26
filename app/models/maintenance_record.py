from sqlalchemy import (
    Column,
    String,
    Integer,
    Date,
    Numeric,
    ForeignKey,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class MaintenanceType:
    ENGINE_OIL = "engine_oil"
    OIL_FILTER = "oil_filter"
    AIR_FILTER = "air_filter"
    FUEL_FILTER = "fuel_filter"
    BRAKE_SERVICE = "brake_service"
    TYRE_CHANGE = "tyre_change"
    WHEEL_ALIGNMENT = "wheel_alignment"
    WHEEL_BALANCING = "wheel_balancing"
    BATTERY_REPLACEMENT = "battery_replacement"
    CLUTCH_REPLACEMENT = "clutch_replacement"
    GEARBOX_SERVICE = "gearbox_service"
    ENGINE_REPAIR = "engine_repair"
    COOLANT_SERVICE = "coolant_service"
    SUSPENSION_SERVICE = "suspension_service"
    ELECTRICAL_REPAIR = "electrical_repair"
    AC_SERVICE = "ac_service"
    GENERAL_SERVICE = "general_service"
    INSPECTION = "inspection"
    OTHER = "other"


class MaintenanceRecord(BaseModel):
    __tablename__ = "maintenance_records"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False,)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False,)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False,)
    recorded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False,)
    maintenance_type = Column(String(100), default=MaintenanceType.GENERAL_SERVICE, nullable=False,)
    description = Column(String)
    garage_name = Column(String(150))
    invoice_number = Column(String(100))
    cost = Column(Numeric(12, 2), nullable=False,)
    service_date = Column(Date, nullable=False,)
    next_service_date = Column(Date)
    odometer_reading = Column(Integer)
    remarks = Column(String)
    is_active = Column(Boolean, default=True, nullable=False,)

    company = relationship("Company", back_populates="maintenance_records",)
    branch = relationship("Branch", back_populates="maintenance_records",)
    vehicle = relationship("Vehicle", back_populates="maintenance_records",)
    recorded_by_user = relationship("User", back_populates="maintenance_records",)