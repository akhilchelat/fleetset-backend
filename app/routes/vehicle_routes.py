from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User

from app.schemas.vehicle_schema import (
    VehicleCreate,
    VehicleUpdate,
    VehicleResponse,
    VehicleListResponse,
    VehicleBulkAction,
    VehicleBulkActionResponse,
)

from app.security.authorization import (
    get_current_user,
    require_roles,
)

from app.services.vehicle_service import (
    create_vehicle,
    get_all_active_vehicles,
    get_all_inactive_vehicles,
    find_vehicle_by_id,
    find_vehicle_by_registration_number,
    find_active_vehicle_by_id,
    find_vehicle_by_registration_number_admin,
    get_all_vehicles_admin,
    update_vehicle,
    activate_vehicle,
    deactivate_vehicle,
    bulk_activate_vehicles,
    bulk_deactivate_vehicles,
)


router = APIRouter(
    prefix="/vehicles",
    tags=["Vehicles"]
)


@router.get(
    "/admin/all",
    response_model=list[VehicleListResponse],
    status_code=status.HTTP_200_OK
)
def get_all_vehicles_admin_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("GLOBAL_ADMIN")
    )
):
    result = get_all_vehicles_admin(db)

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


@router.get(
    "/admin/registration/{registration_number}",
    response_model=VehicleResponse,
    status_code=status.HTTP_200_OK
)
def get_vehicle_by_registration_number_admin_route(
    registration_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("GLOBAL_ADMIN")
    )
):
    result = find_vehicle_by_registration_number_admin(
        db,
        registration_number
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


@router.get(
    "/admin/{vehicle_id}",
    response_model=VehicleResponse,
    status_code=status.HTTP_200_OK
)
def get_active_vehicle_by_id_admin_route(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("GLOBAL_ADMIN")
    )
):
    result = find_active_vehicle_by_id(
        db,
        vehicle_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


@router.patch(
    "/{company_id}/bulk/activate",
    response_model=VehicleBulkActionResponse,
    status_code=status.HTTP_200_OK
)
def bulk_activate_vehicle_route(
    company_id: UUID,
    vehicle: VehicleBulkAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "GLOBAL_ADMIN",
            "SUPER_ADMIN",
            "BRANCH_ADMIN"
        )
    )
):
    result = bulk_activate_vehicles(
        db=db,
        current_user=current_user,
        company_id=company_id,
        vehicle_ids=vehicle.vehicle_ids
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


@router.patch(
    "/{company_id}/bulk/deactivate",
    response_model=VehicleBulkActionResponse,
    status_code=status.HTTP_200_OK
)
def bulk_deactivate_vehicle_route(
    company_id: UUID,
    vehicle: VehicleBulkAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "GLOBAL_ADMIN",
            "SUPER_ADMIN",
            "BRANCH_ADMIN"
        )
    )
):
    result = bulk_deactivate_vehicles(
        db=db,
        current_user=current_user,
        company_id=company_id,
        vehicle_ids=vehicle.vehicle_ids
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


@router.get(
    "/{company_id}/all",
    response_model=list[VehicleListResponse],
    status_code=status.HTTP_200_OK
)
def get_all_active_vehicles_route(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = get_all_active_vehicles(
        db,
        current_user,
        company_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


@router.get(
    "/{company_id}/inactive",
    response_model=list[VehicleListResponse],
    status_code=status.HTTP_200_OK
)
def get_all_inactive_vehicles_route(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = get_all_inactive_vehicles(
        db,
        current_user,
        company_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


@router.get(
    "/{company_id}/registration/{registration_number}",
    response_model=VehicleResponse,
    status_code=status.HTTP_200_OK
)
def get_vehicle_by_registration_number_route(
    company_id: UUID,
    registration_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = find_vehicle_by_registration_number(
        db,
        current_user,
        company_id,
        registration_number
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


@router.get(
    "/{company_id}/{vehicle_id}",
    response_model=VehicleResponse,
    status_code=status.HTTP_200_OK
)
def get_vehicle_by_id_route(
    company_id: UUID,
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = find_vehicle_by_id(
        db,
        current_user,
        company_id,
        vehicle_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


@router.post(
    "/{company_id}",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED
)
def create_vehicle_route(
    company_id: UUID,
    vehicle: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "GLOBAL_ADMIN",
            "SUPER_ADMIN",
            "BRANCH_ADMIN"
        )
    )
):
    result = create_vehicle(
        db=db,
        current_user=current_user,
        company_id=company_id,
        branch_id=vehicle.branch_id,
        registration_number=vehicle.registration_number,
        manufacturer=vehicle.manufacturer,
        model=vehicle.model,
        vehicle_type=vehicle.vehicle_type,
        year=vehicle.year,
        purchase_date=vehicle.purchase_date,
        current_odometer=vehicle.current_odometer
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


@router.put(
    "/{company_id}/{vehicle_id}",
    response_model=VehicleResponse,
    status_code=status.HTTP_200_OK
)
def update_vehicle_route(
    company_id: UUID,
    vehicle_id: UUID,
    vehicle: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "GLOBAL_ADMIN",
            "SUPER_ADMIN",
            "BRANCH_ADMIN"
        )
    )
):
    result = update_vehicle(
        db=db,
        current_user=current_user,
        company_id=company_id,
        vehicle_id=vehicle_id,
        registration_number=vehicle.registration_number,
        manufacturer=vehicle.manufacturer,
        model=vehicle.model,
        vehicle_type=vehicle.vehicle_type,
        year=vehicle.year,
        purchase_date=vehicle.purchase_date,
        vehicle_status=vehicle.status,
        current_odometer=vehicle.current_odometer,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


@router.patch(
    "/{company_id}/{vehicle_id}/activate",
    response_model=VehicleResponse,
    status_code=status.HTTP_200_OK
)
def activate_vehicle_route(
    company_id: UUID,
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "GLOBAL_ADMIN",
            "SUPER_ADMIN",
            "BRANCH_ADMIN"
        )
    )
):
    result = activate_vehicle(
        db=db,
        current_user=current_user,
        company_id=company_id,
        vehicle_id=vehicle_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


@router.patch(
    "/{company_id}/{vehicle_id}/deactivate",
    response_model=VehicleResponse,
    status_code=status.HTTP_200_OK
)
def deactivate_vehicle_route(
    company_id: UUID,
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "GLOBAL_ADMIN",
            "SUPER_ADMIN",
            "BRANCH_ADMIN"
        )
    )
):
    result = deactivate_vehicle(
        db=db,
        current_user=current_user,
        company_id=company_id,
        vehicle_id=vehicle_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]