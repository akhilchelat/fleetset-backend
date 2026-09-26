from app.models.user import User
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from app.reusable_functions.company_reusable import (get_company_by_id_query)
from app.reusable_functions.user_reusable import (get_user_by_email_query,
                                                  get_user_by_id_query,
                                                  get_all_users_query,
                                                  get_all_users_admin_query,
                                                  get_user_by_id_admin_query,
                                                  get_users_by_ids_query)
from app.reusable_functions.role_reusable import (get_role_by_id_query)


def create_user(
    db: Session,
    company_id: UUID,
    role_id: UUID,
    first_name: str,
    last_name: str | None,
    email: str,
    phone: str | None,
    password_hash: str
):

    company = get_company_by_id_query(
        db,
        company_id
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found",
            "data": None
        }

    role = get_role_by_id_query(
        db,
        role_id
    )

    if not role:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "ROLE_NOT_FOUND",
            "message": "Role not found",
            "data": None
        }

    user = get_user_by_email_query(
        db,
        email
    )

    if user:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "USER_ALREADY_EXISTS",
            "message": "User already exists",
            "data": None
        }

    new_user = User(
        company_id=company.id,
        role_id=role.id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        password_hash=password_hash
    )

    db.add(new_user)

    try:
        db.commit()
        db.refresh(new_user)

        return {
            "success": True,
            "status_code": status.HTTP_201_CREATED,
            "code": "USER_CREATED",
            "message": "User created successfully",
            "data": new_user
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "USER_ALREADY_EXISTS",
            "message": "User already exists",
            "data": None
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None
        }


def find_user_by_id(
    db: Session,
    user_id: UUID
):

    user = get_user_by_id_query(
        db,
        user_id
    )

    if not user:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "USER_NOT_FOUND",
            "message": "User not found",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "USER_FOUND",
        "message": "User found successfully",
        "data": user
    }


def find_user_by_email(
    db: Session,
    email: str
):

    user = get_user_by_email_query(
        db,
        email
    )

    if not user:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "USER_NOT_FOUND",
            "message": "User not found",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "USER_FOUND",
        "message": "User found successfully",
        "data": user
    }


def get_all_active_users(
    db: Session
):

    users = get_all_users_query(
        db
    )

    if not users:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_USERS_FOUND",
            "message": "No users found",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "USERS_FOUND",
        "message": "Users retrieved successfully",
        "data": users
    }


def get_all_users_admin(
    db: Session
):

    users = get_all_users_admin_query(
        db
    )

    if not users:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_USERS_FOUND",
            "message": "No users found",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "USERS_FOUND",
        "message": "Users retrieved successfully",
        "data": users
    }


def update_user(
    db: Session,
    user_id: UUID,
    company_id: UUID | None = None,
    role_id: UUID | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    phone: str | None = None
):

    user = get_user_by_id_query(
        db,
        user_id
    )

    if not user:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "USER_NOT_FOUND",
            "message": "User not found",
            "data": None
        }

    if company_id is not None:

        company = get_company_by_id_query(
            db,
            company_id
        )

        if not company:
            return {
                "success": False,
                "status_code": status.HTTP_404_NOT_FOUND,
                "code": "COMPANY_NOT_FOUND",
                "message": "Company not found",
                "data": None
            }

        user.company_id = company.id

    if role_id is not None:

        role = get_role_by_id_query(
            db,
            role_id
        )

        if not role:
            return {
                "success": False,
                "status_code": status.HTTP_404_NOT_FOUND,
                "code": "ROLE_NOT_FOUND",
                "message": "Role not found",
                "data": None
            }

        user.role_id = role.id

    if email is not None:

        existing_user = get_user_by_email_query(
            db,
            email
        )

        if existing_user and existing_user.id != user.id:
            return {
                "success": False,
                "status_code": status.HTTP_409_CONFLICT,
                "code": "EMAIL_ALREADY_EXISTS",
                "message": "Email already exists",
                "data": None
            }

        user.email = email

    if first_name is not None:
        user.first_name = first_name

    if last_name is not None:
        user.last_name = last_name

    if phone is not None:
        user.phone = phone

    try:
        db.commit()
        db.refresh(user)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "USER_UPDATED",
            "message": "User updated successfully",
            "data": user
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None
        }
    

def activate_user(
    db: Session,
    user_id: UUID
):

    user = get_user_by_id_admin_query(
        db,
        user_id
    )

    if not user:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "USER_NOT_FOUND",
            "message": "User not found",
            "data": None
        }

    if user.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "USER_ALREADY_ACTIVE",
            "message": "User already active",
            "data": None
        }

    user.is_active = True

    try:
        db.commit()
        db.refresh(user)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "USER_ACTIVATED",
            "message": "User activated successfully",
            "data": user
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None
        }
    

def bulk_activate_users(
    db: Session,
    user_ids: list[UUID]
):

    users = get_users_by_ids_query(
        db,
        user_ids
    )

    if not users:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_USERS_FOUND",
            "message": "No users found",
            "data": None
        }

    already_active_users = []
    activated_users = []

    for user in users:

        if user.is_active:

            already_active_users.append(
                {
                    "name": f"{user.first_name} {user.last_name or ''}".strip()
                }
            )

            continue

        user.is_active = True

        activated_users.append(
            {
                "name": f"{user.first_name} {user.last_name or ''}".strip()
            }
        )

    try:
        db.commit()

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "BULK_USER_ACTIVATION_COMPLETED",
            "message": "Bulk activation completed",
            "data": {
                "activated_users": activated_users,
                "already_active_users": already_active_users
            }
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None
        }
    

def deactivate_user(
    db: Session,
    user_id: UUID
):

    user = get_user_by_id_admin_query(
        db,
        user_id
    )

    if not user:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "USER_NOT_FOUND",
            "message": "User not found",
            "data": None
        }

    if not user.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "USER_ALREADY_INACTIVE",
            "message": "User already inactive",
            "data": None
        }

    user.is_active = False

    try:
        db.commit()
        db.refresh(user)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "USER_DEACTIVATED",
            "message": "User deactivated successfully",
            "data": user
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None
        }
        

def bulk_deactivate_users(
    db: Session,
    user_ids: list[UUID]
):

    users = get_users_by_ids_query(
        db,
        user_ids
    )

    if not users:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_USERS_FOUND",
            "message": "No users found",
            "data": None
        }

    already_inactive_users = []
    deactivated_users = []

    for user in users:

        if not user.is_active:

            already_inactive_users.append(
                {
                    "name": f"{user.first_name} {user.last_name or ''}".strip()
                }
            )

            continue

        user.is_active = False

        deactivated_users.append(
            {
                "name": f"{user.first_name} {user.last_name or ''}".strip()
            }
        )

    try:
        db.commit()

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "BULK_USER_DEACTIVATION_COMPLETED",
            "message": "Bulk deactivation completed",
            "data": {
                "deactivated_users": deactivated_users,
                "already_inactive_users": already_inactive_users
            }
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None
        }