from uuid import UUID

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.driver import Driver

from app.reusable_functions.branch_reusable import (
    get_branch_by_company_query,
)

from app.reusable_functions.company_reusable import (
    get_company_by_id_query,
)

from app.reusable_functions.role_reusable import (
    get_role_by_id_query,
)

from app.reusable_functions.user_reusable import (
    get_user_by_email_auth_query,
    get_user_by_id_admin_query,
    get_users_by_branch_query,
    get_users_by_company_query,
    get_users_by_ids_query,
)


GLOBAL_ADMIN = "GLOBAL_ADMIN"
SUPER_ADMIN = "SUPER_ADMIN"
BRANCH_ADMIN = "BRANCH_ADMIN"
DRIVER = "DRIVER"


def _validate_role_scope(
    db: Session,
    role_name: str,
    company_id: UUID | None,
    branch_id: UUID | None,
):
    if role_name == GLOBAL_ADMIN:
        if company_id is not None or branch_id is not None:
            return {
                "success": False,
                "status_code": status.HTTP_400_BAD_REQUEST,
                "code": "INVALID_GLOBAL_ADMIN_SCOPE",
                "message": "GLOBAL_ADMIN cannot belong to a company or branch",
                "data": None,
            }

    elif role_name == SUPER_ADMIN:
        if company_id is None:
            return {
                "success": False,
                "status_code": status.HTTP_400_BAD_REQUEST,
                "code": "COMPANY_REQUIRED",
                "message": "SUPER_ADMIN must belong to a company",
                "data": None,
            }

        if branch_id is not None:
            return {
                "success": False,
                "status_code": status.HTTP_400_BAD_REQUEST,
                "code": "INVALID_SUPER_ADMIN_BRANCH",
                "message": "SUPER_ADMIN cannot belong to a branch",
                "data": None,
            }

        company = get_company_by_id_query(
            db,
            company_id,
        )

        if not company:
            return {
                "success": False,
                "status_code": status.HTTP_404_NOT_FOUND,
                "code": "COMPANY_NOT_FOUND",
                "message": "Company not found",
                "data": None,
            }

    elif role_name in {
        BRANCH_ADMIN,
        DRIVER,
    }:
        if company_id is None:
            return {
                "success": False,
                "status_code": status.HTTP_400_BAD_REQUEST,
                "code": "COMPANY_REQUIRED",
                "message": f"{role_name} must belong to a company",
                "data": None,
            }

        if branch_id is None:
            return {
                "success": False,
                "status_code": status.HTTP_400_BAD_REQUEST,
                "code": "BRANCH_REQUIRED",
                "message": f"{role_name} must belong to a branch",
                "data": None,
            }

        branch = get_branch_by_company_query(
            db,
            branch_id,
            company_id,
        )

        if not branch:
            return {
                "success": False,
                "status_code": status.HTTP_404_NOT_FOUND,
                "code": "BRANCH_NOT_FOUND",
                "message": "Branch not found or does not belong to the selected company",
                "data": None,
            }

    else:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_ROLE",
            "message": "Invalid user role",
            "data": None,
        }

    return None


def _can_manage_target(
    current_user: User,
    target_user: User,
):
    current_role = current_user.role.name
    target_role = target_user.role.name

    if current_role == GLOBAL_ADMIN:
        return True

    if current_role == SUPER_ADMIN:
        if target_user.company_id != current_user.company_id:
            return False

        if target_role in {
            GLOBAL_ADMIN,
            SUPER_ADMIN,
        }:
            return False

        return True

    if current_role == BRANCH_ADMIN:
        if target_user.company_id != current_user.company_id:
            return False

        if target_user.branch_id != current_user.branch_id:
            return False

        if target_role != DRIVER:
            return False

        return True

    return target_user.id == current_user.id


def _get_driver_for_user(
    db: Session,
    user_id: UUID,
):
    return (
        db.query(Driver)
        .filter(Driver.user_id == user_id)
        .first()
    )


def create_user(
    db: Session,
    current_user: User,
    company_id: UUID | None,
    branch_id: UUID | None,
    role_id: UUID,
    first_name: str,
    last_name: str | None,
    email: str,
    phone: str | None,
    password_hash: str,
):
    current_role = current_user.role.name

    if current_role == DRIVER:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "USER_CREATION_FORBIDDEN",
            "message": "Drivers cannot create users",
            "data": None,
        }

    role = get_role_by_id_query(
        db,
        role_id,
    )

    if not role:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "ROLE_NOT_FOUND",
            "message": "Role not found",
            "data": None,
        }

    if current_role == SUPER_ADMIN:
        if role.name not in {
            BRANCH_ADMIN,
            DRIVER,
        }:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "ROLE_ASSIGNMENT_FORBIDDEN",
                "message": "SUPER_ADMIN can only create BRANCH_ADMIN or DRIVER users",
                "data": None,
            }

        if company_id != current_user.company_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "COMPANY_ACCESS_DENIED",
                "message": "You can only create users in your own company",
                "data": None,
            }

    elif current_role == BRANCH_ADMIN:
        if role.name != DRIVER:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "ROLE_ASSIGNMENT_FORBIDDEN",
                "message": "BRANCH_ADMIN can only create DRIVER users",
                "data": None,
            }

        if company_id != current_user.company_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "COMPANY_ACCESS_DENIED",
                "message": "You can only create users in your own company",
                "data": None,
            }

        if branch_id != current_user.branch_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "BRANCH_ACCESS_DENIED",
                "message": "You can only create users in your own branch",
                "data": None,
            }

    elif current_role != GLOBAL_ADMIN:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "USER_CREATION_FORBIDDEN",
            "message": "You do not have permission to create users",
            "data": None,
        }

    scope_error = _validate_role_scope(
        db=db,
        role_name=role.name,
        company_id=company_id,
        branch_id=branch_id,
    )

    if scope_error:
        return scope_error

    existing_user = get_user_by_email_auth_query(
        db,
        email,
    )

    if existing_user:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "USER_ALREADY_EXISTS",
            "message": "User already exists",
            "data": None,
        }

    new_user = User(
        company_id=company_id,
        branch_id=branch_id,
        role_id=role.id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        password_hash=password_hash,
        is_active=True,
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
            "data": new_user,
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "USER_ALREADY_EXISTS",
            "message": "User already exists",
            "data": None,
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None,
        }


def find_user_by_id(
    db: Session,
    current_user: User,
    user_id: UUID,
):
    target_user = get_user_by_id_admin_query(
        db,
        user_id,
    )

    if not target_user:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "USER_NOT_FOUND",
            "message": "User not found",
            "data": None,
        }

    if not _can_manage_target(
        current_user,
        target_user,
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "USER_ACCESS_DENIED",
            "message": "You do not have permission to access this user",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "USER_FOUND",
        "message": "User found successfully",
        "data": target_user,
    }


def find_user_by_email(
    db: Session,
    current_user: User,
    email: str,
):
    target_user = get_user_by_email_auth_query(
        db,
        email,
    )

    if not target_user:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "USER_NOT_FOUND",
            "message": "User not found",
            "data": None,
        }

    if not _can_manage_target(
        current_user,
        target_user,
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "USER_ACCESS_DENIED",
            "message": "You do not have permission to access this user",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "USER_FOUND",
        "message": "User found successfully",
        "data": target_user,
    }


def get_all_active_users(
    db: Session,
    current_user: User,
):
    role_name = current_user.role.name

    if role_name == GLOBAL_ADMIN:
        users = (
            db.query(User)
            .filter(User.is_active.is_(True))
            .all()
        )

    elif role_name == SUPER_ADMIN:
        if current_user.company_id is None:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "COMPANY_REQUIRED",
                "message": "SUPER_ADMIN must belong to a company",
                "data": None,
            }

        users = get_users_by_company_query(
            db,
            current_user.company_id,
        )

    elif role_name == BRANCH_ADMIN:
        if current_user.branch_id is None:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "BRANCH_REQUIRED",
                "message": "BRANCH_ADMIN must belong to a branch",
                "data": None,
            }

        users = get_users_by_branch_query(
            db,
            current_user.branch_id,
        )

    elif role_name == DRIVER:
        users = [current_user]

    else:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "USER_ACCESS_DENIED",
            "message": "You do not have permission to access users",
            "data": None,
        }

    if not users:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_USERS_FOUND",
            "message": "No users found",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "USERS_FOUND",
        "message": "Users retrieved successfully",
        "data": users,
    }


def get_all_users_admin(
    db: Session,
    current_user: User,
):
    if current_user.role.name != GLOBAL_ADMIN:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "ADMIN_ACCESS_REQUIRED",
            "message": "Only GLOBAL_ADMIN can access all users",
            "data": None,
        }

    users = db.query(User).all()

    if not users:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_USERS_FOUND",
            "message": "No users found",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "USERS_FOUND",
        "message": "Users retrieved successfully",
        "data": users,
    }


def update_user(
    db: Session,
    current_user: User,
    user_id: UUID,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
    role_id: UUID | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
):
    user = get_user_by_id_admin_query(
        db,
        user_id,
    )

    if not user:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "USER_NOT_FOUND",
            "message": "User not found",
            "data": None,
        }

    current_target_role = user.role.name

    if not _can_manage_target(
        current_user,
        user,
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "USER_UPDATE_FORBIDDEN",
            "message": "You do not have permission to update this user",
            "data": None,
        }

    requested_role = user.role

    if role_id is not None:
        requested_role = get_role_by_id_query(
            db,
            role_id,
        )

        if not requested_role:
            return {
                "success": False,
                "status_code": status.HTTP_404_NOT_FOUND,
                "code": "ROLE_NOT_FOUND",
                "message": "Role not found",
                "data": None,
            }

    requested_role_name = requested_role.name

    if current_user.role.name == DRIVER:
        if user.id != current_user.id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "USER_UPDATE_FORBIDDEN",
                "message": "You can only update your own profile",
                "data": None,
            }

        if (
            company_id is not None
            or branch_id is not None
            or role_id is not None
        ):
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "SCOPE_UPDATE_FORBIDDEN",
                "message": "You cannot change company, branch, or role",
                "data": None,
            }

    if current_user.role.name == SUPER_ADMIN:
        if (
            company_id is not None
            and company_id != current_user.company_id
        ):
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "COMPANY_CHANGE_FORBIDDEN",
                "message": "You cannot move a user to another company",
                "data": None,
            }

        if (
            branch_id is not None
            and requested_role_name == SUPER_ADMIN
        ):
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "INVALID_SUPER_ADMIN_BRANCH",
                "message": "SUPER_ADMIN cannot belong to a branch",
                "data": None,
            }

        if requested_role_name not in {
            BRANCH_ADMIN,
            DRIVER,
        } and requested_role_name != current_target_role:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "ROLE_CHANGE_FORBIDDEN",
                "message": "SUPER_ADMIN cannot assign this role",
                "data": None,
            }

    if current_user.role.name == BRANCH_ADMIN:
        if (
            company_id is not None
            and company_id != current_user.company_id
        ):
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "COMPANY_CHANGE_FORBIDDEN",
                "message": "You cannot change the company",
                "data": None,
            }

        if (
            branch_id is not None
            and branch_id != current_user.branch_id
        ):
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "BRANCH_CHANGE_FORBIDDEN",
                "message": "You cannot move a user to another branch",
                "data": None,
            }

        if requested_role_name != DRIVER:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "ROLE_CHANGE_FORBIDDEN",
                "message": "BRANCH_ADMIN can only manage DRIVER users",
                "data": None,
            }

    # Driver records are managed by driver_service.
    # Do not create/remove a Driver record through the generic User API.
    if current_target_role == DRIVER and requested_role_name != DRIVER:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "DRIVER_ROLE_CHANGE_FORBIDDEN",
            "message": "Driver role changes must be handled through driver management",
            "data": None,
        }

    if current_target_role != DRIVER and requested_role_name == DRIVER:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "DRIVER_ROLE_CHANGE_FORBIDDEN",
            "message": "Create a driver through driver management instead",
            "data": None,
        }

    final_company_id = (
        company_id
        if company_id is not None
        else user.company_id
    )

    final_branch_id = (
        branch_id
        if branch_id is not None
        else user.branch_id
    )

    scope_error = _validate_role_scope(
        db=db,
        role_name=requested_role_name,
        company_id=final_company_id,
        branch_id=final_branch_id,
    )

    if scope_error:
        return scope_error

    if email is not None:
        existing_user = get_user_by_email_auth_query(
            db,
            email,
        )

        if existing_user and existing_user.id != user.id:
            return {
                "success": False,
                "status_code": status.HTTP_409_CONFLICT,
                "code": "EMAIL_ALREADY_EXISTS",
                "message": "Email already exists",
                "data": None,
            }

        user.email = email

    user.company_id = final_company_id
    user.branch_id = final_branch_id
    user.role_id = requested_role.id

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
            "data": user,
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "USER_UPDATE_CONFLICT",
            "message": "User update conflicts with existing data",
            "data": None,
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None,
        }


def activate_user(
    db: Session,
    current_user: User,
    user_id: UUID,
):
    user = get_user_by_id_admin_query(
        db,
        user_id,
    )

    if not user:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "USER_NOT_FOUND",
            "message": "User not found",
            "data": None,
        }

    if not _can_manage_target(
        current_user,
        user,
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "USER_ACCESS_DENIED",
            "message": "You do not have permission to activate this user",
            "data": None,
        }

    if user.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "USER_ALREADY_ACTIVE",
            "message": "User already active",
            "data": None,
        }

    user.is_active = True

    driver = None

    if user.role.name == DRIVER:
        driver = _get_driver_for_user(
            db,
            user.id,
        )

        if driver:
            driver.is_active = True

    try:
        db.commit()
        db.refresh(user)

        if driver:
            db.refresh(driver)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "USER_ACTIVATED",
            "message": "User activated successfully",
            "data": user,
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "USER_ACTIVATION_CONFLICT",
            "message": "User could not be activated because of a data conflict",
            "data": None,
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None,
        }


def deactivate_user(
    db: Session,
    current_user: User,
    user_id: UUID,
):
    user = get_user_by_id_admin_query(
        db,
        user_id,
    )

    if not user:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "USER_NOT_FOUND",
            "message": "User not found",
            "data": None,
        }

    if not _can_manage_target(
        current_user,
        user,
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "USER_ACCESS_DENIED",
            "message": "You do not have permission to deactivate this user",
            "data": None,
        }

    if user.id == current_user.id:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "SELF_DEACTIVATION_FORBIDDEN",
            "message": "You cannot deactivate your own account",
            "data": None,
        }

    if not user.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "USER_ALREADY_INACTIVE",
            "message": "User already inactive",
            "data": None,
        }

    user.is_active = False

    driver = None

    if user.role.name == DRIVER:
        driver = _get_driver_for_user(
            db,
            user.id,
        )

        if driver:
            driver.is_active = False

    try:
        db.commit()
        db.refresh(user)

        if driver:
            db.refresh(driver)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "USER_DEACTIVATED",
            "message": "User deactivated successfully",
            "data": user,
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "USER_DEACTIVATION_CONFLICT",
            "message": "User could not be deactivated because of a data conflict",
            "data": None,
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None,
        }


def bulk_activate_users(
    db: Session,
    current_user: User,
    user_ids: list[UUID],
):
    users = get_users_by_ids_query(
        db,
        user_ids,
    )

    if not users:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_USERS_FOUND",
            "message": "No users found",
            "data": None,
        }

    activated_users = []
    already_active_users = []
    inaccessible_users = []

    for user in users:
        if not _can_manage_target(
            current_user,
            user,
        ):
            inaccessible_users.append({
                "id": str(user.id),
                "name": f"{user.first_name} {user.last_name or ''}".strip(),
            })
            continue

        if user.is_active:
            already_active_users.append({
                "id": str(user.id),
                "name": f"{user.first_name} {user.last_name or ''}".strip(),
            })
            continue

        user.is_active = True

        if user.role.name == DRIVER:
            driver = _get_driver_for_user(
                db,
                user.id,
            )

            if driver:
                driver.is_active = True

        activated_users.append({
            "id": str(user.id),
            "name": f"{user.first_name} {user.last_name or ''}".strip(),
        })

    try:
        db.commit()

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "BULK_USER_ACTIVATION_COMPLETED",
            "message": "Bulk activation completed",
            "data": {
                "activated_users": activated_users,
                "already_active_users": already_active_users,
                "inaccessible_users": inaccessible_users,
            },
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "BULK_USER_ACTIVATION_CONFLICT",
            "message": "Bulk user activation could not be completed",
            "data": None,
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None,
        }


def bulk_deactivate_users(
    db: Session,
    current_user: User,
    user_ids: list[UUID],
):
    users = get_users_by_ids_query(
        db,
        user_ids,
    )

    if not users:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_USERS_FOUND",
            "message": "No users found",
            "data": None,
        }

    deactivated_users = []
    already_inactive_users = []
    inaccessible_users = []

    for user in users:
        if user.id == current_user.id:
            inaccessible_users.append({
                "id": str(user.id),
                "name": f"{user.first_name} {user.last_name or ''}".strip(),
                "reason": "Cannot deactivate your own account",
            })
            continue

        if not _can_manage_target(
            current_user,
            user,
        ):
            inaccessible_users.append({
                "id": str(user.id),
                "name": f"{user.first_name} {user.last_name or ''}".strip(),
            })
            continue

        if not user.is_active:
            already_inactive_users.append({
                "id": str(user.id),
                "name": f"{user.first_name} {user.last_name or ''}".strip(),
            })
            continue

        user.is_active = False

        if user.role.name == DRIVER:
            driver = _get_driver_for_user(
                db,
                user.id,
            )

            if driver:
                driver.is_active = False

        deactivated_users.append({
            "id": str(user.id),
            "name": f"{user.first_name} {user.last_name or ''}".strip(),
        })

    try:
        db.commit()

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "BULK_USER_DEACTIVATION_COMPLETED",
            "message": "Bulk deactivation completed",
            "data": {
                "deactivated_users": deactivated_users,
                "already_inactive_users": already_inactive_users,
                "inaccessible_users": inaccessible_users,
            },
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "BULK_USER_DEACTIVATION_CONFLICT",
            "message": "Bulk user deactivation could not be completed",
            "data": None,
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None,
        }