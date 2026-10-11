from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr


class ReportRequest(BaseModel):
    start_date: date
    end_date: date
    branch_id: UUID | None = None


class ReportEmailRequest(BaseModel):
    start_date: date
    end_date: date
    branch_id: UUID | None = None
    recipient_email: EmailStr | None = None


class ReportSummary(BaseModel):
    total_vehicles: int
    active_vehicles: int
    inactive_vehicles: int
    total_drivers: int
    total_trips: int
    total_fuel_expense: Decimal
    total_maintenance_expense: Decimal
    total_expense: Decimal


class ReportPeriod(BaseModel):
    start_date: date
    end_date: date


class ReportResponse(BaseModel):
    success: bool
    message: str
    company_id: UUID
    branch_id: UUID | None = None
    report_type: str
    period: ReportPeriod
    summary: ReportSummary
    file_name: str | None = None