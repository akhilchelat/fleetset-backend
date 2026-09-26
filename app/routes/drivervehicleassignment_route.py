from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.drivervehicleassignment_schema import (
    DriverVehicleAssignmentCreate,
    DriverVehicleAssignmentTransfer,
    DriverVehicleAssignmentResponse,
    DriverVehicleAssignmentListResponse,
)
from app.services.drivervehicleassignment_service import (
    assign_driver_to_vehicle_service,
    unassign_driver_from_vehicle_service,
    transfer_driver_to_vehicle_service,
    get_assignment_service,
    get_company_assignments_service,
)

router = APIRouter(
    prefix="/driver-vehicle-assignments",
    tags=["Driver Vehicle Assignments"]
)



@router.post(
    "/{company_id}",
    response_model=DriverVehicleAssignmentResponse,
    status_code=status.HTTP_201_CREATED
)
def assign_driver_to_vehicle_route(
    company_id: UUID,
    assignment: DriverVehicleAssignmentCreate,
    assigned_by: UUID,
    db: Session = Depends(get_db)
):
    result = assign_driver_to_vehicle_service(
        db=db,
        company_id=company_id,
        driver_id=assignment.driver_id,
        vehicle_id=assignment.vehicle_id,
        assigned_by=assigned_by
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )

    return result["assignment"]



@router.post(
    "/{company_id}/transfer",
    response_model=DriverVehicleAssignmentResponse,
    status_code=status.HTTP_200_OK
)
def transfer_driver_to_vehicle_route(
    company_id: UUID,
    assignment: DriverVehicleAssignmentTransfer,
    assigned_by: UUID,
    db: Session = Depends(get_db)
):
    result = transfer_driver_to_vehicle_service(
        db=db,
        company_id=company_id,
        driver_id=assignment.driver_id,
        new_vehicle_id=assignment.new_vehicle_id,
        assigned_by=assigned_by
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )

    return result["assignment"]



@router.patch(
    "/{company_id}/{assignment_id}/unassign",
    response_model=DriverVehicleAssignmentResponse,
    status_code=status.HTTP_200_OK
)
def unassign_driver_from_vehicle_route(
    company_id: UUID,
    assignment_id: UUID,
    db: Session = Depends(get_db)
):
    result = unassign_driver_from_vehicle_service(
        db=db,
        company_id=company_id,
        assignment_id=assignment_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )

    return result["assignment"]



@router.get(
    "/{company_id}/{assignment_id}",
    response_model=DriverVehicleAssignmentResponse,
    status_code=status.HTTP_200_OK
)
def get_assignment_route(
    company_id: UUID,
    assignment_id: UUID,
    db: Session = Depends(get_db)
):
    result = get_assignment_service(
        db=db,
        company_id=company_id,
        assignment_id=assignment_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["message"]
        )

    return result["assignment"]

@router.get(
    "/{company_id}",
    response_model=DriverVehicleAssignmentListResponse,
    status_code=status.HTTP_200_OK
)
def get_company_assignments_route(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    result = get_company_assignments_service(
        db=db,
        company_id=company_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["message"]
        )

    return result