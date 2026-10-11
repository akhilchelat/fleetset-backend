from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class DriverVehicleAssignmentCreate(BaseModel):
    driver_id: UUID
    vehicle_id: UUID


class DriverVehicleAssignmentTransfer(BaseModel):
    driver_id: UUID
    new_vehicle_id: UUID


class DriverVehicleAssignmentResponse(BaseModel):
    id: UUID
    company_id: UUID
    branch_id: UUID
    driver_id: UUID
    vehicle_id: UUID
    assigned_by: UUID
    assigned_at: datetime
    unassigned_at: datetime | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class DriverVehicleAssignmentListResponse(BaseModel):
    success: bool
    message: str | None = None
    assignments: list[DriverVehicleAssignmentResponse] = Field(
        default_factory=list
    )