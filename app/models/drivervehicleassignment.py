from sqlalchemy import Column, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel


class DriverVehicleAssignment(BaseModel):
    __tablename__ = "driver_vehicle_assignments"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False,)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False,)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=False,)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False,)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False,)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False,)
    unassigned_at = Column(DateTime(timezone=True),)
    is_active = Column(Boolean, default=True, nullable=False,)
    
    company = relationship("Company", back_populates="driver_vehicle_assignments",)
    branch = relationship("Branch", back_populates="driver_vehicle_assignments",)
    driver = relationship("Driver", back_populates="assignments",)
    vehicle = relationship("Vehicle", back_populates="assignments",)
    assigned_by_user = relationship("User", back_populates="driver_vehicle_assignments",)