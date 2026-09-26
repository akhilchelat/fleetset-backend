from sqlalchemy import (
    Column,
    String,
    Date,
    Boolean,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class VehicleDocumentType:
    REGISTRATION_CERTIFICATE = "registration_certificate"
    INSURANCE = "insurance"
    FITNESS_CERTIFICATE = "fitness_certificate"
    POLLUTION_CERTIFICATE = "pollution_certificate"
    NATIONAL_PERMIT = "national_permit"
    STATE_PERMIT = "state_permit"
    ROAD_TAX = "road_tax"
    OTHER = "other"


class VehicleDocument(BaseModel):
    __tablename__ = "vehicle_documents"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False,)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False,)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False,)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False,)
    document_type = Column(String(100), default=VehicleDocumentType.OTHER, nullable=False,)
    document_number = Column(String(100), nullable=False,)
    issue_date = Column(Date)
    expiry_date = Column(Date)
    file_url = Column(String)
    remarks = Column(String)
    is_active = Column(Boolean, default=True, nullable=False,)

    company = relationship("Company", back_populates="vehicle_documents",)
    branch = relationship("Branch", back_populates="vehicle_documents",)
    vehicle = relationship("Vehicle", back_populates="documents",)
    uploaded_by_user = relationship("User", back_populates="vehicle_documents",)