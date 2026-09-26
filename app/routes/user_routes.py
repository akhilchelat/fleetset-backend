from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.user_schema import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserBulkAction,
    UserBulkActionResponse,
)

from app.services.user_service import (
    create_user,
    find_user_by_id,
    find_user_by_email,
    get_all_active_users,
    get_all_users_admin,
    update_user,
    activate_user,
    bulk_activate_users,
    deactivate_user,
    bulk_deactivate_users,
)

from app.security.authentication import hash_password


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
):
    hashed_password = hash_password(user.password)

    result = create_user(
        db=db,
        company_id=user.company_id,
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
):
    result = get_all_active_users(db=db)

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
):
    result = get_all_users_admin(db=db)

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
):
    result = find_user_by_email(
        db=db,
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
):
    result = find_user_by_id(
        db=db,
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
):
    result = update_user(
        db=db,
        user_id=user_id,
        company_id=user.company_id,
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
):
    result = activate_user(
        db=db,
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
):
    result = deactivate_user(
        db=db,
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
):
    result = bulk_activate_users(
        db=db,
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
):
    result = bulk_deactivate_users(
        db=db,
        user_ids=request.user_ids,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]

