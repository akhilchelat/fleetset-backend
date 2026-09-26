from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class NotificationType:
    DOCUMENT_EXPIRY = "document_expiry"
    MAINTENANCE_DUE = "maintenance_due"
    DRIVER_LICENSE_EXPIRY = "driver_license_expiry"
    VEHICLE = "vehicle"
    DRIVER = "driver"
    TRIP = "trip"
    FUEL = "fuel"
    USER = "user"
    SYSTEM = "system"


class NotificationPriority:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Notification(BaseModel):
    __tablename__ = "notifications"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False,)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False,)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False,)
    notification_type = Column(String(50), default=NotificationType.SYSTEM, nullable=False,)
    priority = Column(String(20), default=NotificationPriority.MEDIUM, nullable=False,)
    title = Column(String(255), nullable=False,)
    message = Column(String, nullable=False,)
    reference_table = Column(String(100))
    reference_id = Column(UUID(as_uuid=True))
    is_read = Column(Boolean, default=False, nullable=False,)
    read_at = Column(DateTime(timezone=True))

    company = relationship("Company", back_populates="notifications",)
    branch = relationship("Branch", back_populates="notifications",)
    user = relationship("User", back_populates="notifications",)