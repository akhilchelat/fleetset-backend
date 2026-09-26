from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

from uuid import UUID
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class DriverCreate(BaseModel):
    first_name: str
    last_name: str | None = None
    phone: str
    address: str | None = None
    license_number: str
    license_expiry: date | None = None
    experience_years: int | None = None
    emergency_contact: str | None = None


class DriverUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    address: str | None = None
    license_number: str | None = None
    license_expiry: date | None = None
    experience_years: int | None = None
    emergency_contact: str | None = None
    status: str | None = None


class DriverResponse(BaseModel):
    id: UUID
    company_id: UUID
    first_name: str
    last_name: str | None
    phone: str
    address: str | None
    license_number: str
    license_expiry: date | None
    experience_years: int | None
    emergency_contact: str | None
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DriverListResponse(BaseModel):
    id: UUID
    company_id: UUID
    first_name: str
    last_name: str | None
    phone: str
    license_number: str
    license_expiry: date | None
    status: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class DriverBulkAction(BaseModel):
    driver_ids: list[UUID]


class DriverBulkActionItem(BaseModel):
    id: UUID
    name: str


class DriverBulkActionResponse(BaseModel):
    activated_drivers: list[DriverBulkActionItem] = []
    already_active_drivers: list[DriverBulkActionItem] = []
    deactivated_drivers: list[DriverBulkActionItem] = []
    already_inactive_drivers: list[DriverBulkActionItem] = []