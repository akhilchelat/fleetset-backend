from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.auth_service import login_user
from app.schemas.auth_schema import (
    TokenResponse,
    CurrentUserResponse,
)

from app.security.authorization import get_current_user


import hashlib
import hmac
import logging
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import UUID

from jose import JWTError, jwt

from app.models.user import User
from app.schemas.password_schema import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
)
from app.security.authentication import (
    SECRET_KEY,
    ALGORITHM,
    hash_password,
    verify_password,
)
from app.services.email_service import send_password_reset_email
from app.reusable_functions.user_reusable import (
    get_user_by_email_auth_query,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    result = login_user(
        db=db,
        email=form_data.username,
        password=form_data.password
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]



@router.get(
    "/me",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_200_OK,
)
def get_current_user_route(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "company_id": current_user.company_id,
        "branch_id": current_user.branch_id,
        "company_name": (
            current_user.company.name
            if current_user.company
            else None
        ),
        "branch_name": (
            current_user.branch.name
            if current_user.branch
            else None
        ),
        "role_id": current_user.role_id,
        "role_name": current_user.role.name if current_user.role else "",
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "is_active": current_user.is_active,
    }

logger = logging.getLogger(__name__)

PASSWORD_RESET_SECRET = os.getenv(
    "PASSWORD_RESET_SECRET",
    SECRET_KEY,
)

PASSWORD_RESET_URL = os.getenv(
    "PASSWORD_RESET_URL",
    "fleetsetmobile://reset-password",
)


def _password_fingerprint(password_hash: str) -> str:
    return hashlib.sha256(
        password_hash.encode("utf-8")
    ).hexdigest()


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    # Always return the same public response to prevent email enumeration.
    generic_response = {
        "message": (
            "If an active account matches that email, "
            "password-reset instructions will be sent."
        )
    }

    user = get_user_by_email_auth_query(db, request.email)

    if not user or not user.is_active:
        return generic_response

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user.id),
        "purpose": "password_reset",
        "pwdv": _password_fingerprint(user.password_hash),
        "iat": now,
        "exp": now + timedelta(minutes=30),
    }

    token = jwt.encode(
        payload,
        PASSWORD_RESET_SECRET,
        algorithm=ALGORITHM,
    )

    reset_url = (
        f"{PASSWORD_RESET_URL}?{urlencode({'token': token})}"
    )

    result = send_password_reset_email(
        recipient_email=user.email,
        reset_url=reset_url,
    )

    if not result.get("success"):
        logger.error("FleetSet password-reset email delivery failed")

    return generic_response


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    invalid_token = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Reset link is invalid or expired. Request a new link.",
    )

    try:
        payload = jwt.decode(
            request.token,
            PASSWORD_RESET_SECRET,
            algorithms=[ALGORITHM],
        )
    except JWTError:
        raise invalid_token

    if payload.get("purpose") != "password_reset":
        raise invalid_token

    try:
        user_id = UUID(payload.get("sub", ""))
    except (ValueError, TypeError):
        raise invalid_token

    user = db.query(User).filter(User.id == user_id).first()

    if (
        not user
        or not user.is_active
        or not hmac.compare_digest(
            str(payload.get("pwdv", "")),
            _password_fingerprint(user.password_hash),
        )
    ):
        raise invalid_token

    if verify_password(request.new_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Choose a password different from your current password.",
        )

    user.password_hash = hash_password(request.new_password)
    db.commit()

    return {"message": "Password reset successfully. Please sign in."}


@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(
        request.current_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    if verify_password(
        request.new_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Choose a password different from your current password.",
        )

    current_user.password_hash = hash_password(request.new_password)
    db.commit()

    return {"message": "Password changed successfully."}
