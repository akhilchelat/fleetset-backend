from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.user_schema import (
    UserBulkAction,
    UserBulkActionResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)

from app.security.authentication import hash_password
from app.security.authorization import (
    get_current_user,
    require_roles,
)

from app.services.user_service import (
    activate_user,
    bulk_activate_users,
    bulk_deactivate_users,
    create_user,
    deactivate_user,
    find_user_by_email,
    find_user_by_id,
    get_all_active_users,
    get_all_users_admin,
    update_user,
)

from app.models.user import User


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user_route(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "GLOBAL_ADMIN",
            "SUPER_ADMIN",
            "BRANCH_ADMIN",
        )
    ),
):
    hashed_password = hash_password(
        user.password
    )

    result = create_user(
        db=db,
        current_user=current_user,
        company_id=user.company_id,
        branch_id=user.branch_id,
        role_id=user.role_id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone=user.phone,
        password_hash=hashed_password,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/all",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
)
def get_all_active_users_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = get_all_active_users(
        db=db,
        current_user=current_user,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/admin/all",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
)
def get_all_users_admin_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("GLOBAL_ADMIN")
    ),
):
    result = get_all_users_admin(
        db=db,
        current_user=current_user,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/email/{email}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def get_user_by_email_route(
    email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "GLOBAL_ADMIN",
            "SUPER_ADMIN",
            "BRANCH_ADMIN",
        )
    ),
):
    result = find_user_by_email(
        db=db,
        current_user=current_user,
        email=email,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def get_user_by_id_route(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = find_user_by_id(
        db=db,
        current_user=current_user,
        user_id=user_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def update_user_route(
    user_id: UUID,
    user: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = update_user(
        db=db,
        current_user=current_user,
        user_id=user_id,
        company_id=user.company_id,
        branch_id=user.branch_id,
        role_id=user.role_id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone=user.phone,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.patch(
    "/{user_id}/activate",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def activate_user_route(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "GLOBAL_ADMIN",
            "SUPER_ADMIN",
            "BRANCH_ADMIN",
        )
    ),
):
    result = activate_user(
        db=db,
        current_user=current_user,
        user_id=user_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.patch(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def deactivate_user_route(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "GLOBAL_ADMIN",
            "SUPER_ADMIN",
            "BRANCH_ADMIN",
        )
    ),
):
    result = deactivate_user(
        db=db,
        current_user=current_user,
        user_id=user_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.patch(
    "/bulk/activate",
    response_model=UserBulkActionResponse,
    status_code=status.HTTP_200_OK,
)
def bulk_activate_users_route(
    request: UserBulkAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "GLOBAL_ADMIN",
            "SUPER_ADMIN",
            "BRANCH_ADMIN",
        )
    ),
):
    result = bulk_activate_users(
        db=db,
        current_user=current_user,
        user_ids=request.user_ids,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.patch(
    "/bulk/deactivate",
    response_model=UserBulkActionResponse,
    status_code=status.HTTP_200_OK,
)
def bulk_deactivate_users_route(
    request: UserBulkAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "GLOBAL_ADMIN",
            "SUPER_ADMIN",
            "BRANCH_ADMIN",
        )
    ),
):
    result = bulk_deactivate_users(
        db=db,
        current_user=current_user,
        user_ids=request.user_ids,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]