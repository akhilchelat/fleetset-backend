from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.models.user import User

from app.schemas.driver_schema import (
    DriverCreate,
    DriverUpdate,
    DriverResponse,
    DriverListResponse,
    DriverBulkAction,
    DriverBulkActionResponse,
)

from app.security.authentication import hash_password
from app.security.authorization import (
    get_current_user,
    require_roles,
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
    tags=["Drivers"],
)


# ============================================================
# GLOBAL ADMIN ROUTES
# ============================================================


@router.get(
    "/admin/license/{license_number}",
    response_model=DriverResponse,
    dependencies=[Depends(require_roles("GLOBAL_ADMIN"))],
)
def get_driver_by_license_admin(
    license_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = find_driver_by_license_number_admin(
        db=db,
        current_user=current_user,
        license_number=license_number,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result,
        )

    return result["data"]


@router.get(
    "/admin/all",
    response_model=list[DriverListResponse],
    dependencies=[Depends(require_roles("GLOBAL_ADMIN"))],
)
def get_all_drivers_admin_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = get_all_drivers_admin(
        db=db,
        current_user=current_user,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result,
        )

    return result["data"]


@router.get(
    "/admin/{driver_id}",
    response_model=DriverResponse,
    dependencies=[Depends(require_roles("GLOBAL_ADMIN"))],
)
def get_active_driver_admin(
    driver_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = find_active_driver_by_id(
        db=db,
        current_user=current_user,
        driver_id=driver_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result,
        )

    return result["data"]


@router.patch(
    "/admin/{driver_id}/activate",
    response_model=DriverResponse,
    dependencies=[Depends(require_roles("GLOBAL_ADMIN"))],
)
def activate_driver_admin(
    driver_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = activate_driver(
        db=db,
        current_user=current_user,
        driver_id=driver_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result,
        )

    return result["data"]


@router.patch(
    "/admin/{driver_id}/deactivate",
    response_model=DriverResponse,
    dependencies=[Depends(require_roles("GLOBAL_ADMIN"))],
)
def deactivate_driver_admin(
    driver_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = deactivate_driver(
        db=db,
        current_user=current_user,
        driver_id=driver_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result,
        )

    return result["data"]


@router.patch(
    "/admin/bulk/activate",
    response_model=DriverBulkActionResponse,
    dependencies=[Depends(require_roles("GLOBAL_ADMIN"))],
)
def bulk_activate_drivers_admin(
    payload: DriverBulkAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = bulk_activate_drivers(
        db=db,
        current_user=current_user,
        driver_ids=payload.driver_ids,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result,
        )

    return result["data"]


@router.patch(
    "/admin/bulk/deactivate",
    response_model=DriverBulkActionResponse,
    dependencies=[Depends(require_roles("GLOBAL_ADMIN"))],
)
def bulk_deactivate_drivers_admin(
    payload: DriverBulkAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = bulk_deactivate_drivers(
        db=db,
        current_user=current_user,
        driver_ids=payload.driver_ids,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result,
        )

    return result["data"]


# ============================================================
# COMPANY / BRANCH ROUTES
# ============================================================


@router.post(
    "/{company_id}",
    response_model=DriverResponse,
)
def create_driver_route(
    company_id: UUID,
    driver: DriverCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    hashed_password = hash_password(
        driver.password
    )

    result = create_driver(
        db=db,
        current_user=current_user,
        company_id=company_id,
        branch_id=driver.branch_id,
        first_name=driver.first_name,
        last_name=driver.last_name,
        email=driver.email,
        phone=driver.phone,
        password_hash=hashed_password,
        license_number=driver.license_number,
        license_expiry=driver.license_expiry,
        experience_years=driver.experience_years,
        emergency_contact=driver.emergency_contact,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result,
        )

    return result["data"]


@router.get(
    "/{company_id}",
    response_model=list[DriverListResponse],
)
def get_all_drivers_route(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = get_all_drivers(
        db=db,
        current_user=current_user,
        company_id=company_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result,
        )

    return result["data"]


@router.get(
    "/{company_id}/license/{license_number}",
    response_model=DriverResponse,
)
def get_driver_by_license_route(
    company_id: UUID,
    license_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = find_driver_by_license_number(
        db=db,
        current_user=current_user,
        company_id=company_id,
        license_number=license_number,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result,
        )

    return result["data"]


@router.get(
    "/{company_id}/{driver_id}",
    response_model=DriverResponse,
)
def get_driver_by_id_route(
    company_id: UUID,
    driver_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = find_driver_by_id(
        db=db,
        current_user=current_user,
        company_id=company_id,
        driver_id=driver_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result,
        )

    return result["data"]


@router.put(
    "/{company_id}/{driver_id}",
    response_model=DriverResponse,
)
def update_driver_route(
    company_id: UUID,
    driver_id: UUID,
    driver: DriverUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = update_driver(
        db=db,
        current_user=current_user,
        company_id=company_id,
        driver_id=driver_id,
        first_name=driver.first_name,
        last_name=driver.last_name,
        email=driver.email,
        phone=driver.phone,
        license_number=driver.license_number,
        license_expiry=driver.license_expiry,
        experience_years=driver.experience_years,
        emergency_contact=driver.emergency_contact,
        driver_status=driver.status,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result,
        )

    return result["data"]