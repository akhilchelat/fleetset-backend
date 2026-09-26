
from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FuelLogCreate(BaseModel):
    vehicle_id: UUID
    driver_id: UUID | None = None
    recorded_by: UUID
    fuel_date: date
    fuel_cost: Decimal = Field(..., gt=0, decimal_places=2)

    @field_validator("fuel_cost")
    @classmethod
    def validate_fuel_cost(cls, value: Decimal):
        if value <= Decimal("0"):
            raise ValueError("Fuel cost must be greater than zero")
        return value


class FuelLogUpdate(BaseModel):
    fuel_date: date | None = None
    fuel_cost: Decimal | None = Field(
        default=None,
        gt=0,
        decimal_places=2
    )

    @field_validator("fuel_cost")
    @classmethod
    def validate_fuel_cost(cls, value: Decimal | None):
        if value is not None and value <= Decimal("0"):
            raise ValueError("Fuel cost must be greater than zero")
        return value


class FuelLogResponse(BaseModel):
    id: UUID
    company_id: UUID
    vehicle_id: UUID
    driver_id: UUID | None = None
    recorded_by: UUID
    fuel_date: date
    fuel_cost: Decimal
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class FuelExpenseResponse(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    total_cost: Decimal


class DailyFuelExpenseResponse(BaseModel):
    expense_date: date
    total_cost: Decimal

