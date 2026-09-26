from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.role_schema import (
    RoleResponse,
    RoleListResponse,
    RoleBulkAction,
    RoleBulkActionResponse,
)

from app.services.role_service import (
    find_role_by_id,
    find_role_by_id_admin,
    find_role_by_name,
    get_all_roles,
    get_all_roles_admin,
    activate_role,
    deactivate_role,
    bulk_activate_roles,
    bulk_deactivate_roles,
)


router = APIRouter(
    prefix="/roles",
    tags=["Roles"]
)


# =========================================================
# ADMIN ROUTES
# =========================================================


# 1. Admin - Get all roles
@router.get(
    "/admin/all",
    response_model=list[RoleListResponse],
    status_code=status.HTTP_200_OK
)
def get_all_roles_admin_route(
    db: Session = Depends(get_db)
):
    result = get_all_roles_admin(
        db=db
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


# 2. Admin - Bulk activate roles
@router.patch(
    "/admin/bulk/activate",
    response_model=RoleBulkActionResponse,
    status_code=status.HTTP_200_OK
)
def bulk_activate_roles_route(
    role_data: RoleBulkAction,
    db: Session = Depends(get_db)
):
    result = bulk_activate_roles(
        db=db,
        role_ids=role_data.role_ids
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


# 3. Admin - Bulk deactivate roles
@router.patch(
    "/admin/bulk/deactivate",
    response_model=RoleBulkActionResponse,
    status_code=status.HTTP_200_OK
)
def bulk_deactivate_roles_route(
    role_data: RoleBulkAction,
    db: Session = Depends(get_db)
):
    result = bulk_deactivate_roles(
        db=db,
        role_ids=role_data.role_ids
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


# 4. Admin - Activate role
@router.patch(
    "/admin/{role_id}/activate",
    response_model=RoleResponse,
    status_code=status.HTTP_200_OK
)
def activate_role_route(
    role_id: UUID,
    db: Session = Depends(get_db)
):
    result = activate_role(
        db=db,
        role_id=role_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


# 5. Admin - Deactivate role
@router.patch(
    "/admin/{role_id}/deactivate",
    response_model=RoleResponse,
    status_code=status.HTTP_200_OK
)
def deactivate_role_route(
    role_id: UUID,
    db: Session = Depends(get_db)
):
    result = deactivate_role(
        db=db,
        role_id=role_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


# 6. Admin - Get role by ID
@router.get(
    "/admin/{role_id}",
    response_model=RoleResponse,
    status_code=status.HTTP_200_OK
)
def get_role_by_id_admin_route(
    role_id: UUID,
    db: Session = Depends(get_db)
):
    result = find_role_by_id_admin(
        db=db,
        role_id=role_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


# =========================================================
# APPLICATION ROUTES
# =========================================================


# 7. Get all active roles
@router.get(
    "",
    response_model=list[RoleListResponse],
    status_code=status.HTTP_200_OK
)
def get_all_roles_route(
    db: Session = Depends(get_db)
):
    result = get_all_roles(
        db=db
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


# 8. Get role by name
@router.get(
    "/name/{role_name}",
    response_model=RoleResponse,
    status_code=status.HTTP_200_OK
)
def get_role_by_name_route(
    role_name: str,
    db: Session = Depends(get_db)
):
    result = find_role_by_name(
        db=db,
        role_name=role_name
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


# 9. Get active role by ID
@router.get(
    "/{role_id}",
    response_model=RoleResponse,
    status_code=status.HTTP_200_OK
)
def get_role_by_id_route(
    role_id: UUID,
    db: Session = Depends(get_db)
):
    result = find_role_by_id(
        db=db,
        role_id=role_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]