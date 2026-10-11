from sqlalchemy import Column, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Branch(BaseModel):
    __tablename__ = "branches"

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "name",
            name="uq_branch_company_name",
        ),
    )

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False,)
    name = Column(String(255), nullable=False,)
    email = Column(String(255))
    phone = Column(String(20))
    address = Column(String)
    is_active = Column(Boolean, default=True, nullable=False,)

    company = relationship("Company", back_populates="branches",)
    users = relationship("User", back_populates="branch",)
    vehicles = relationship("Vehicle", back_populates="branch",)
    driver_vehicle_assignments = relationship("DriverVehicleAssignment", back_populates="branch",)
    trips = relationship("Trip", back_populates="branch",)
    fuel_logs = relationship("FuelLog", back_populates="branch",)
    maintenance_records = relationship("MaintenanceRecord", back_populates="branch",)
    vehicle_documents = relationship("VehicleDocument", back_populates="branch",)
    notifications = relationship("Notification", back_populates="branch",)