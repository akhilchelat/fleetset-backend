from sqlalchemy import Column, Numeric, Date, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class FuelLog(BaseModel):
    __tablename__ = "fuel_logs"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False,)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False,)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False,)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=True,)
    recorded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False,)
    fuel_date = Column(Date, nullable=False)
    fuel_cost = Column(Numeric(12, 2), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False,)

    company = relationship("Company", back_populates="fuel_logs",)
    branch = relationship("Branch", back_populates="fuel_logs",)
    vehicle = relationship("Vehicle", back_populates="fuel_logs",)
    driver = relationship("Driver", back_populates="fuel_logs",)
    recorded_by_user = relationship("User", back_populates="fuel_logs",)