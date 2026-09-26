from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.driver_schema import (
    DriverCreate,
    DriverUpdate,
    DriverResponse,
    DriverListResponse,
    DriverBulkAction,
    DriverBulkActionResponse,
)

from app.services.driver_service import (
    create_driver,
    get_all_drivers,
    find_driver_by_id,
    find_driver_by_license_number,
    find_active_driver_by_id,
    find_driver_by_license_number_admin,
    get_all_drivers_admin,
    update_driver,
    activate_driver,
    deactivate_driver,
    bulk_activate_drivers,
    bulk_deactivate_drivers,
)


router = APIRouter(
    prefix="/drivers",
    tags=["Drivers"]
)


# =========================================================
# ADMIN ROUTES
# =========================================================

# 1. Admin - Get driver by license number
@router.get(
    "/admin/license/{license_number}",
    response_model=DriverResponse,
    status_code=status.HTTP_200_OK
)
def get_driver_by_license_number_admin_route(
    license_number: str,
    db: Session = Depends(get_db)
):
    result = find_driver_by_license_number_admin(
        db=db,
        license_number=license_number
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


# 2. Admin - Get all drivers
@router.get(
    "/admin/all",
    response_model=list[DriverListResponse],
    status_code=status.HTTP_200_OK
)
def get_all_drivers_admin_route(
    db: Session = Depends(get_db)
):
    result = get_all_drivers_admin(
        db=db
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


# 3. Admin - Bulk activate drivers
@router.patch(
    "/admin/bulk/activate",
    response_model=DriverBulkActionResponse,
    status_code=status.HTTP_200_OK
)
def bulk_activate_drivers_route(
    driver_data: DriverBulkAction,
    db: Session = Depends(get_db)
):
    result = bulk_activate_drivers(
        db=db,
        driver_ids=driver_data.driver_ids
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


# 4. Admin - Bulk deactivate drivers
@router.patch(
    "/admin/bulk/deactivate",
    response_model=DriverBulkActionResponse,
    status_code=status.HTTP_200_OK
)
def bulk_deactivate_drivers_route(
    driver_data: DriverBulkAction,
    db: Session = Depends(get_db)
):
    result = bulk_deactivate_drivers(
        db=db,
        driver_ids=driver_data.driver_ids
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


# 5. Admin - Activate driver
@router.patch(
    "/admin/{driver_id}/activate",
    response_model=DriverResponse,
    status_code=status.HTTP_200_OK
)
def activate_driver_route(
    driver_id: UUID,
    db: Session = Depends(get_db)
):
    result = activate_driver(
        db=db,
        driver_id=driver_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


# 6. Admin - Deactivate driver
@router.patch(
    "/admin/{driver_id}/deactivate",
    response_model=DriverResponse,
    status_code=status.HTTP_200_OK
)
def deactivate_driver_route(
    driver_id: UUID,
    db: Session = Depends(get_db)
):
    result = deactivate_driver(
        db=db,
        driver_id=driver_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


# 7. Admin - Get active driver by ID
@router.get(
    "/admin/{driver_id}",
    response_model=DriverResponse,
    status_code=status.HTTP_200_OK
)
def get_active_driver_by_id_route(
    driver_id: UUID,
    db: Session = Depends(get_db)
):
    result = find_active_driver_by_id(
        db=db,
        driver_id=driver_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


# =========================================================
# COMPANY-SCOPED ROUTES
# =========================================================

# 8. Create driver
@router.post(
    "/{company_id}",
    response_model=DriverResponse,
    status_code=status.HTTP_201_CREATED
)
def create_driver_route(
    company_id: UUID,
    driver: DriverCreate,
    db: Session = Depends(get_db)
):
    result = create_driver(
        db=db,
        company_id=company_id,
        first_name=driver.first_name,
        last_name=driver.last_name,
        phone=driver.phone,
        address=driver.address,
        license_number=driver.license_number,
        license_expiry=driver.license_expiry,
        experience_years=driver.experience_years,
        emergency_contact=driver.emergency_contact
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


# 9. Get all drivers for company
@router.get(
    "/{company_id}",
    response_model=list[DriverListResponse],
    status_code=status.HTTP_200_OK
)
def get_all_drivers_route(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    result = get_all_drivers(
        db=db,
        company_id=company_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


# 10. Get driver by ID
@router.get(
    "/{company_id}/{driver_id}",
    response_model=DriverResponse,
    status_code=status.HTTP_200_OK
)
def get_driver_by_id_route(
    company_id: UUID,
    driver_id: UUID,
    db: Session = Depends(get_db)
):
    result = find_driver_by_id(
        db=db,
        company_id=company_id,
        driver_id=driver_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


# 11. Get driver by license number
@router.get(
    "/{company_id}/license/{license_number}",
    response_model=DriverResponse,
    status_code=status.HTTP_200_OK
)
def get_driver_by_license_number_route(
    company_id: UUID,
    license_number: str,
    db: Session = Depends(get_db)
):
    result = find_driver_by_license_number(
        db=db,
        company_id=company_id,
        license_number=license_number
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


# 12. Update driver
@router.put(
    "/{company_id}/{driver_id}",
    response_model=DriverResponse,
    status_code=status.HTTP_200_OK
)
def update_driver_route(
    company_id: UUID,
    driver_id: UUID,
    driver: DriverUpdate,
    db: Session = Depends(get_db)
):
    result = update_driver(
    db=db,
    company_id=company_id,
    driver_id=driver_id,
    first_name=driver.first_name,
    last_name=driver.last_name,
    phone=driver.phone,
    address=driver.address,
    license_number=driver.license_number,
    license_expiry=driver.license_expiry,
    experience_years=driver.experience_years,
    emergency_contact=driver.emergency_contact,
    driver_status=driver.status
)

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]