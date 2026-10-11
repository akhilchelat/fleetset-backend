from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.trip import TripStatus


class TripCreate(BaseModel):
    vehicle_id: UUID
    driver_id: UUID

    origin: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    destination: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    cargo_description: str | None = Field(
        default=None,
        max_length=500,
    )

    remarks: str | None = Field(
        default=None,
        max_length=1000,
    )


class TripUpdate(BaseModel):
    origin: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    destination: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    cargo_description: str | None = Field(
        default=None,
        max_length=500,
    )

    remarks: str | None = Field(
        default=None,
        max_length=1000,
    )


class TripResponse(BaseModel):
    id: UUID

    company_id: UUID
    branch_id: UUID

    vehicle_id: UUID
    driver_id: UUID
    created_by: UUID

    origin: str
    destination: str

    cargo_description: str | None
    remarks: str | None

    status: TripStatus

    actual_start: datetime | None
    actual_end: datetime | None

    is_active: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class TripListResponse(BaseModel):
    id: UUID

    company_id: UUID
    branch_id: UUID

    vehicle_id: UUID
    driver_id: UUID
    created_by: UUID

    origin: str
    destination: str

    cargo_description: str | None
    remarks: str | None

    status: TripStatus

    actual_start: datetime | None
    actual_end: datetime | None

    is_active: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )