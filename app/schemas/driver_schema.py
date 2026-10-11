from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class DriverCreate(BaseModel):
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    last_name: str | None = Field(
        default=None,
        max_length=100,
    )

    email: EmailStr

    phone: str = Field(
        ...,
        min_length=1,
        max_length=20,
    )

    password: str = Field(
        ...,
        min_length=8,
    )

    branch_id: UUID

    license_number: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    license_expiry: date | None = None

    experience_years: int | None = Field(
        default=None,
        ge=0,
    )

    emergency_contact: str | None = Field(
        default=None,
        max_length=20,
    )


class DriverUpdate(BaseModel):
    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    last_name: str | None = Field(
        default=None,
        max_length=100,
    )

    email: EmailStr | None = None

    phone: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
    )

    license_number: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    license_expiry: date | None = None

    experience_years: int | None = Field(
        default=None,
        ge=0,
    )

    emergency_contact: str | None = Field(
        default=None,
        max_length=20,
    )

    status: str | None = None


class DriverResponse(BaseModel):
    id: UUID
    company_id: UUID
    branch_id: UUID

    first_name: str
    last_name: str | None

    email: EmailStr
    phone: str | None

    license_number: str
    license_expiry: date | None
    experience_years: int | None
    emergency_contact: str | None

    status: str
    is_active: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class DriverListResponse(BaseModel):
    id: UUID
    company_id: UUID
    branch_id: UUID

    first_name: str
    last_name: str | None

    email: EmailStr
    phone: str | None

    license_number: str
    license_expiry: date | None
    status: str
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class DriverBulkAction(BaseModel):
    driver_ids: list[UUID] = Field(
        ...,
        min_length=1,
    )


class DriverBulkActionItem(BaseModel):
    id: UUID
    name: str


class DriverBulkActionResponse(BaseModel):
    activated_drivers: list[DriverBulkActionItem] = []
    already_active_drivers: list[DriverBulkActionItem] = []

    deactivated_drivers: list[DriverBulkActionItem] = []
    already_inactive_drivers: list[DriverBulkActionItem] = []