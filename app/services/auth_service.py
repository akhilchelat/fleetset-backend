from datetime import timedelta

from fastapi import status
from sqlalchemy.orm import Session

from app.reusable_functions.user_reusable import (
    get_user_by_email_auth_query,
)

from app.security.authentication import (
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)


def login_user(
    db: Session,
    email: str,
    password: str,
):
    user = get_user_by_email_auth_query(
        db,
        email,
    )

    if not user:
        return {
            "success": False,
            "status_code": status.HTTP_401_UNAUTHORIZED,
            "code": "INVALID_CREDENTIALS",
            "message": "Invalid email or password",
            "data": None,
        }

    if not user.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "USER_INACTIVE",
            "message": "User account is inactive",
            "data": None,
        }

    if not verify_password(
        password,
        user.password_hash,
    ):
        return {
            "success": False,
            "status_code": status.HTTP_401_UNAUTHORIZED,
            "code": "INVALID_CREDENTIALS",
            "message": "Invalid email or password",
            "data": None,
        }

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "company_id": (
                str(user.company_id)
                if user.company_id
                else None
            ),
            "branch_id": (
                str(user.branch_id)
                if user.branch_id
                else None
            ),
            "role_id": str(user.role_id),
        },
        expires_delta=timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "LOGIN_SUCCESSFUL",
        "message": "Login successful",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
        },
    }