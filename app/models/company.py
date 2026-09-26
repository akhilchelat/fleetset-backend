from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Company(BaseModel):
    __tablename__ = "companies"

    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20))
    address = Column(String)
    gst_number = Column(String(50), unique=True)
    is_active = Column(Boolean, default=True, nullable=False)

    branches = relationship("Branch", back_populates="company", cascade="all, delete-orphan")
    users = relationship("User", back_populates="company")
    vehicles = relationship("Vehicle", back_populates="company")
    trips = relationship("Trip", back_populates="company")
    driver_vehicle_assignments = relationship("DriverVehicleAssignment", back_populates="company")
    vehicle_documents = relationship("VehicleDocument", back_populates="company")
    fuel_logs = relationship("FuelLog", back_populates="company")
    maintenance_records = relationship("MaintenanceRecord", back_populates="company")
    notifications = relationship("Notification", back_populates="company")