from sqlalchemy import Column, String, Integer, Boolean, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class DriverStatus:
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    SUSPENDED = "suspended"


class Driver(BaseModel):
    __tablename__ = "drivers"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    license_number = Column(String(100), unique=True, nullable=False)
    license_expiry = Column(Date)
    experience_years = Column(Integer)
    emergency_contact = Column(String(20))
    status = Column(String(50), default=DriverStatus.ACTIVE, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="driver")
    company = relationship("Company")
    branch = relationship("Branch")
    trips = relationship("Trip", back_populates="driver")
    assignments = relationship("DriverVehicleAssignment", back_populates="driver")
    fuel_logs = relationship("FuelLog", back_populates="driver")