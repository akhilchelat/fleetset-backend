from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ReportRequest(BaseModel):
    start_date: date
    end_date: date

class ReportEmailRequest(BaseModel):
    start_date: date
    end_date: date
    recipient_email: str | None = None    


class ReportSummary(BaseModel):
    total_vehicles: int
    active_vehicles: int
    inactive_vehicles: int
    total_drivers: int
    total_trips: int

    total_fuel_expense: Decimal
    total_maintenance_expense: Decimal
    total_expense: Decimal


class ReportResponse(BaseModel):
    success: bool
    message: str

    company_id: UUID
    report_type: str

    start_date: date
    end_date: date

    file_name: str | None = None

class ReportEmailRequest(BaseModel):
    start_date: date
    end_date: date
    recipient_email: EmailStr | None = None    