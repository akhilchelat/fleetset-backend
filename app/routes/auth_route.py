
import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth_schema import (
    TokenResponse,
    CurrentUserResponse,
)
from app.schemas.password_schema import (
    ForgotPasswordRequest,
    VerifyResetOTPRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
)
from app.security.authorization import get_current_user
from app.security.authentication import (
    SECRET_KEY,
    hash_password,
    verify_password,
)
from app.services.auth_service import login_user
from app.services.email_service import (
    send_password_reset_otp,
)
from app.reusable_functions.user_reusable import (
    get_user_by_email_auth_query,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

logger = logging.getLogger(__name__)

PASSWORD_RESET_SECRET = os.getenv(
    "PASSWORD_RESET_SECRET",
    SECRET_KEY,
)

OTP_EXPIRY_MINUTES = 10
RESET_TOKEN_EXPIRY_MINUTES = 10
MAX_OTP_ATTEMPTS = 5


# ============================================================
# PASSWORD RESET HELPERS
# ============================================================

def _password_fingerprint(password_hash: str) -> str:
    return hashlib.sha256(
        password_hash.encode("utf-8")
    ).hexdigest()


def _otp_hash(otp: str) -> str:
    return hmac.new(
        PASSWORD_RESET_SECRET.encode("utf-8"),
        otp.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _reset_token_hash(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def _invalid_otp_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired code. Request a new code.",
    )


def _invalid_reset_token_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Reset authorization is invalid or expired.",
    )


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    result = login_user(
        db=db,
        email=form_data.username,
        password=form_data.password,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


# ============================================================
# CURRENT USER
# ============================================================

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
        "role_name": (
            current_user.role.name
            if current_user.role
            else ""
        ),
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "is_active": current_user.is_active,
    }


# ============================================================
# FORGOT PASSWORD - SEND EMAIL OTP
# ============================================================

@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
)
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    # Use the same response for known and unknown accounts.
    generic_response = {
        "message": (
            "If an active account matches that email, "
            "a verification code will be sent."
        )
    }

    user = get_user_by_email_auth_query(
        db,
        request.email,
    )

    if not user or not user.is_active:
        return generic_response

    otp = f"{secrets.randbelow(1_000_000):06d}"
    now = datetime.now(timezone.utc)

    try:
        db.execute(
            text("""
                INSERT INTO password_reset_otps (
                    user_id,
                    otp_hash,
                    password_fingerprint,
                    expires_at,
                    attempts,
                    verified_at,
                    reset_token_hash,
                    reset_token_expires_at,
                    consumed_at,
                    created_at
                )
                VALUES (
                    :user_id,
                    :otp_hash,
                    :fingerprint,
                    :expires_at,
                    0,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NOW()
                )
                ON CONFLICT (user_id)
                DO UPDATE SET
                    otp_hash = EXCLUDED.otp_hash,
                    password_fingerprint =
                        EXCLUDED.password_fingerprint,
                    expires_at = EXCLUDED.expires_at,
                    attempts = 0,
                    verified_at = NULL,
                    reset_token_hash = NULL,
                    reset_token_expires_at = NULL,
                    consumed_at = NULL,
                    created_at = NOW()
            """),
            {
                "user_id": user.id,
                "otp_hash": _otp_hash(otp),
                "fingerprint": _password_fingerprint(
                    user.password_hash
                ),
                "expires_at": (
                    now + timedelta(
                        minutes=OTP_EXPIRY_MINUTES
                    )
                ),
            },
        )

        db.commit()

    except Exception:
        db.rollback()
        logger.exception(
            "Unable to create password-reset OTP"
        )
        return generic_response

    # Send the email only after the OTP is committed.
    try:
        result = send_password_reset_otp(
            recipient_email=user.email,
            otp=otp,
        )
    except Exception:
        logger.exception(
            "Password-reset OTP email delivery raised an error"
        )
        result = {"success": False}

    if not result.get("success"):
        # Invalidate the code if the email could not be sent.
        try:
            db.execute(
                text("""
                    DELETE FROM password_reset_otps
                    WHERE user_id = :user_id
                """),
                {"user_id": user.id},
            )
            db.commit()
        except Exception:
            db.rollback()
            logger.exception(
                "Unable to invalidate unsent password-reset OTP"
            )

        logger.error(
            "Password-reset OTP email delivery failed"
        )

    return generic_response


# ============================================================
# VERIFY OTP - ISSUE SHORT-LIVED RESET AUTHORIZATION
# ============================================================

@router.post(
    "/verify-reset-otp",
    status_code=status.HTTP_200_OK,
)
def verify_reset_otp(
    request: VerifyResetOTPRequest,
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)

    try:
        row = db.execute(
            text("""
                SELECT
                    pr.*,
                    u.is_active
                FROM password_reset_otps AS pr
                JOIN users AS u
                    ON u.id = pr.user_id
                WHERE LOWER(u.email) = LOWER(:email)
                FOR UPDATE OF pr
            """),
            {"email": request.email},
        ).mappings().first()

        if (
            not row
            or not row["is_active"]
            or row["consumed_at"] is not None
            or row["verified_at"] is not None
            or row["expires_at"] <= now
            or row["attempts"] >= MAX_OTP_ATTEMPTS
        ):
            db.rollback()
            raise _invalid_otp_error()

        if not hmac.compare_digest(
            row["otp_hash"],
            _otp_hash(request.otp),
        ):
            # Commit the failed attempt before returning an error.
            # Otherwise a rollback would undo the attempt counter.
            db.execute(
                text("""
                    UPDATE password_reset_otps
                    SET attempts = attempts + 1
                    WHERE id = :id
                """),
                {"id": row["id"]},
            )
            db.commit()
            raise _invalid_otp_error()

        reset_token = secrets.token_urlsafe(32)

        db.execute(
            text("""
                UPDATE password_reset_otps
                SET verified_at = :now,
                    reset_token_hash = :token_hash,
                    reset_token_expires_at = :token_expires
                WHERE id = :id
            """),
            {
                "now": now,
                "token_hash": _reset_token_hash(
                    reset_token
                ),
                "token_expires": (
                    now + timedelta(
                        minutes=RESET_TOKEN_EXPIRY_MINUTES
                    )
                ),
                "id": row["id"],
            },
        )

        db.commit()

        return {
            "message": "Email verified successfully.",
            "reset_token": reset_token,
        }

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception(
            "Password-reset OTP verification failed"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to verify the code right now.",
        )


# ============================================================
# RESET PASSWORD - REQUIRES VERIFIED RESET AUTHORIZATION
# ============================================================

@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
)
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)

    try:
        row = db.execute(
            text("""
                SELECT
                    pr.*,
                    u.password_hash,
                    u.is_active
                FROM password_reset_otps AS pr
                JOIN users AS u
                    ON u.id = pr.user_id
                WHERE pr.reset_token_hash = :token_hash
                FOR UPDATE OF pr
            """),
            {
                "token_hash": _reset_token_hash(
                    request.token
                ),
            },
        ).mappings().first()

        if (
            not row
            or not row["is_active"]
            or row["consumed_at"] is not None
            or row["verified_at"] is None
            or row["reset_token_expires_at"] is None
            or row["reset_token_expires_at"] <= now
            or not hmac.compare_digest(
                row["password_fingerprint"],
                _password_fingerprint(
                    row["password_hash"]
                ),
            )
        ):
            db.rollback()
            raise _invalid_reset_token_error()

        if verify_password(
            request.new_password,
            row["password_hash"],
        ):
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Choose a password different from "
                    "your current password."
                ),
            )

        db.execute(
            text("""
                UPDATE users
                SET password_hash = :password_hash,
                    updated_at = NOW()
                WHERE id = :user_id
            """),
            {
                "password_hash": hash_password(
                    request.new_password
                ),
                "user_id": row["user_id"],
            },
        )

        # Consume the authorization so it cannot be reused.
        db.execute(
            text("""
                UPDATE password_reset_otps
                SET consumed_at = :now,
                    reset_token_hash = NULL,
                    reset_token_expires_at = NULL,
                    otp_hash = ''
                WHERE id = :id
            """),
            {
                "now": now,
                "id": row["id"],
            },
        )

        db.commit()

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("Password reset failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to reset the password right now.",
        )

    return {
        "message": (
            "Password reset successfully. Please sign in."
        )
    }


# ============================================================
# CHANGE PASSWORD - EXISTING AUTHENTICATED FLOW
# ============================================================

@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
)
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
            detail=(
                "Choose a password different from "
                "your current password."
            ),
        )

    current_user.password_hash = hash_password(
        request.new_password
    )
    db.commit()

    return {
        "message": "Password changed successfully."
    }
