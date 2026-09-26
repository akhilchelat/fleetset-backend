from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True,)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True,)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False,)
    first_name = Column(String(100), nullable=False,)
    last_name = Column(String(100))
    email = Column(String(255), unique=True, nullable=False,)
    phone = Column(String(20))
    password_hash = Column(String, nullable=False,)
    is_active = Column(Boolean, default=True, nullable=False,)
    
    company = relationship("Company", back_populates="users",)
    branch = relationship("Branch", back_populates="users",)
    role = relationship("Role", back_populates="users",)
    driver = relationship("Driver", back_populates="user", uselist=False,)
    notifications = relationship("Notification", back_populates="user",)
    driver_vehicle_assignments = relationship("DriverVehicleAssignment", back_populates="assigned_by_user",)
    trips = relationship("Trip", back_populates="created_by_user",)
    fuel_logs = relationship("FuelLog", back_populates="recorded_by_user",)
    maintenance_records = relationship("MaintenanceRecord", back_populates="recorded_by_user",)
    vehicle_documents = relationship("VehicleDocument", back_populates="uploaded_by_user",)