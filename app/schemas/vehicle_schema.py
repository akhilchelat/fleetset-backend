from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VehicleCreate(BaseModel):
    branch_id: UUID

    registration_number: str = Field(
        ...,
        min_length=1,
        max_length=50
    )

    manufacturer: str | None = Field(
        default=None,
        max_length=100
    )

    model: str | None = Field(
        default=None,
        max_length=100
    )

    vehicle_type: str | None = Field(
        default=None,
        max_length=50
    )

    year: int | None = Field(
        default=None,
        ge=1900,
        le=2100
    )

    purchase_date: date | None = None

    current_odometer: int | None = Field(
        default=0,
        ge=0
    )


class VehicleUpdate(BaseModel):
    registration_number: str | None = Field(
        default=None,
        min_length=1,
        max_length=50
    )

    manufacturer: str | None = Field(
        default=None,
        max_length=100
    )

    model: str | None = Field(
        default=None,
        max_length=100
    )

    vehicle_type: str | None = Field(
        default=None,
        max_length=50
    )

    year: int | None = Field(
        default=None,
        ge=1900,
        le=2100
    )

    purchase_date: date | None = None

    status: str | None = Field(
        default=None,
        max_length=50
    )

    current_odometer: int | None = Field(
        default=None,
        ge=0,
    )


class VehicleResponse(BaseModel):
    id: UUID
    company_id: UUID
    branch_id: UUID

    registration_number: str

    manufacturer: str | None
    model: str | None
    vehicle_type: str | None

    year: int | None
    purchase_date: date | None

    current_odometer: int

    status: str
    is_active: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class VehicleListResponse(BaseModel):
    id: UUID
    company_id: UUID
    branch_id: UUID

    registration_number: str

    manufacturer: str | None
    model: str | None
    vehicle_type: str | None

    year: int | None
    purchase_date: date | None

    current_odometer: int

    status: str
    is_active: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class VehicleBulkAction(BaseModel):
    vehicle_ids: list[UUID] = Field(
        ...,
        min_length=1
    )


class VehicleBulkActionItem(BaseModel):
    id: UUID
    registration_number: str


class VehicleBulkActionResponse(BaseModel):
    activated_vehicles: list[VehicleBulkActionItem] = Field(
        default_factory=list
    )

    already_active_vehicles: list[VehicleBulkActionItem] = Field(
        default_factory=list
    )

    deactivated_vehicles: list[VehicleBulkActionItem] = Field(
        default_factory=list
    )

    already_inactive_vehicles: list[VehicleBulkActionItem] = Field(
        default_factory=list
    )