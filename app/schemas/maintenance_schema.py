from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


MaintenanceTypeValue = Literal[
    "engine_oil",
    "oil_filter",
    "air_filter",
    "fuel_filter",
    "brake_service",
    "tyre_change",
    "wheel_alignment",
    "wheel_balancing",
    "battery_replacement",
    "clutch_replacement",
    "gearbox_service",
    "engine_repair",
    "coolant_service",
    "suspension_service",
    "electrical_repair",
    "ac_service",
    "general_service",
    "inspection",
    "other",
]


class MaintenanceCreate(BaseModel):

    vehicle_id: UUID

    recorded_by: UUID

    maintenance_type: MaintenanceTypeValue = "general_service"

    description: str | None = Field(
        default=None,
        max_length=1000
    )

    garage_name: str | None = Field(
        default=None,
        max_length=150
    )

    invoice_number: str | None = Field(
        default=None,
        max_length=100
    )

    cost: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        max_digits=12
    )

    service_date: date

    next_service_date: date | None = None

    odometer_reading: int | None = Field(
        default=None,
        ge=0
    )

    remarks: str | None = Field(
        default=None,
        max_length=1000
    )


class MaintenanceUpdate(BaseModel):

    maintenance_type: MaintenanceTypeValue | None = None

    description: str | None = Field(
        default=None,
        max_length=1000
    )

    garage_name: str | None = Field(
        default=None,
        max_length=150
    )

    invoice_number: str | None = Field(
        default=None,
        max_length=100
    )

    cost: Decimal | None = Field(
        default=None,
        gt=0,
        decimal_places=2,
        max_digits=12
    )

    service_date: date | None = None

    next_service_date: date | None = None

    odometer_reading: int | None = Field(
        default=None,
        ge=0
    )

    remarks: str | None = Field(
        default=None,
        max_length=1000
    )


class MaintenanceResponse(BaseModel):

    id: UUID

    company_id: UUID
    vehicle_id: UUID
    recorded_by: UUID

    maintenance_type: MaintenanceTypeValue

    description: str | None

    garage_name: str | None

    invoice_number: str | None

    cost: Decimal

    service_date: date

    next_service_date: date | None

    odometer_reading: int | None

    remarks: str | None

    is_active: bool

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class MaintenanceCostResponse(BaseModel):

    total_cost: Decimal



class MaintenanceDateRangeCostResponse(BaseModel):

    start_date: date

    end_date: date

    total_cost: Decimal


class MaintenanceDailyCostResponse(BaseModel):

    date: date

    total_cost: Decimal



class MaintenanceVehicleCostResponse(BaseModel):

    vehicle_id: UUID

    start_date: date

    end_date: date

    total_cost: Decimal

