from datetime import date
from uuid import UUID

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.driver import Driver, DriverStatus
from app.models.user import User

from app.reusable_functions.branch_reusable import (
    get_branch_by_company_query,
)

from app.reusable_functions.company_reusable import (
    get_company_by_id_query,
)

from app.reusable_functions.driver_reusable import (
    get_driver_by_license_number_query,
    get_driver_by_id_query,
    get_all_drivers_query,
    get_all_drivers_admin_query,
    get_driver_by_license_number_admin_query,
    get_active_driver_by_id_admin_query,
    get_driver_by_id_admin_query,
    get_drivers_by_ids_query,
)

from app.reusable_functions.role_reusable import (
    get_role_by_name_query,
)

from app.reusable_functions.user_reusable import (
    get_user_by_email_auth_query,
)


GLOBAL_ADMIN = "GLOBAL_ADMIN"
SUPER_ADMIN = "SUPER_ADMIN"
BRANCH_ADMIN = "BRANCH_ADMIN"
DRIVER = "DRIVER"


def _driver_response(driver: Driver):
    user = driver.user

    return {
        "id": driver.id,
        "company_id": driver.company_id,
        "branch_id": driver.branch_id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone": user.phone,
        "license_number": driver.license_number,
        "license_expiry": driver.license_expiry,
        "experience_years": driver.experience_years,
        "emergency_contact": driver.emergency_contact,
        "status": driver.status,
        "is_active": driver.is_active,
        "created_at": driver.created_at,
        "updated_at": driver.updated_at,
    }


def _driver_bulk_item(driver: Driver):
    first_name = driver.user.first_name
    last_name = driver.user.last_name or ""

    return {
        "id": driver.id,
        "name": f"{first_name} {last_name}".strip(),
    }


def _current_role_name(current_user: User):
    return current_user.role.name


def _can_access_driver(
    current_user: User,
    driver: Driver,
):
    role_name = _current_role_name(current_user)

    if role_name == GLOBAL_ADMIN:
        return True

    if role_name == SUPER_ADMIN:
        return (
            current_user.company_id == driver.company_id
        )

    if role_name == BRANCH_ADMIN:
        return (
            current_user.company_id == driver.company_id
            and current_user.branch_id == driver.branch_id
        )

    if role_name == DRIVER:
        return driver.user_id == current_user.id

    return False


def _can_manage_drivers(
    current_user: User,
):
    return _current_role_name(current_user) in {
        GLOBAL_ADMIN,
        SUPER_ADMIN,
        BRANCH_ADMIN,
    }


def _get_driver_phone_query(
    db: Session,
    phone: str,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
):
    query = (
        db.query(Driver)
        .join(User, Driver.user_id == User.id)
        .filter(
            User.phone == phone,
            User.is_active.is_(True),
            Driver.is_active.is_(True),
        )
    )

    if company_id is not None:
        query = query.filter(
            Driver.company_id == company_id
        )

    if branch_id is not None:
        query = query.filter(
            Driver.branch_id == branch_id
        )

    return query.first()


def create_driver(
    db: Session,
    current_user: User,
    company_id: UUID,
    branch_id: UUID,
    first_name: str,
    last_name: str | None,
    email: str,
    phone: str,
    password_hash: str,
    license_number: str,
    license_expiry: date | None,
    experience_years: int | None,
    emergency_contact: str | None,
):

    role_name = _current_role_name(current_user)

    if role_name == DRIVER:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "DRIVER_ACCESS_DENIED",
            "message": "Drivers cannot create drivers",
            "data": None,
        }

    if role_name not in {
        GLOBAL_ADMIN,
        SUPER_ADMIN,
        BRANCH_ADMIN,
    }:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "DRIVER_CREATION_NOT_ALLOWED",
            "message": "You do not have permission to create drivers",
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

    if role_name == SUPER_ADMIN:
        if current_user.company_id != company_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "COMPANY_ACCESS_DENIED",
                "message": "You can only create drivers within your company",
                "data": None,
            }

    if role_name == BRANCH_ADMIN:
        if (
            current_user.company_id != company_id
            or current_user.branch_id != branch_id
        ):
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "BRANCH_ACCESS_DENIED",
                "message": "You can only create drivers within your branch",
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
            "message": "Branch not found for this company",
            "data": None,
        }

    existing_user = get_user_by_email_auth_query(
        db,
        email,
    )

    if existing_user:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "EMAIL_ALREADY_EXISTS",
            "message": "Email already exists",
            "data": None,
        }

    existing_driver = get_driver_by_license_number_admin_query(
        db,
        license_number,
    )

    if existing_driver:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "LICENSE_NUMBER_ALREADY_EXISTS",
            "message": "License number already exists",
            "data": None,
        }

    phone_exists = _get_driver_phone_query(
        db,
        phone,
    )

    if phone_exists:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "PHONE_ALREADY_EXISTS",
            "message": "Phone number already exists",
            "data": None,
        }

    driver_role = get_role_by_name_query(
        db,
        DRIVER,
    )

    if not driver_role:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_ROLE_NOT_FOUND",
            "message": "Driver role not found",
            "data": None,
        }

    new_user = User(
        company_id=company.id,
        branch_id=branch.id,
        role_id=driver_role.id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        password_hash=password_hash,
        is_active=True,
    )

    db.add(new_user)

    try:
        db.flush()

        new_driver = Driver(
            user_id=new_user.id,
            company_id=company.id,
            branch_id=branch.id,
            license_number=license_number,
            license_expiry=license_expiry,
            experience_years=experience_years,
            emergency_contact=emergency_contact,
            status=DriverStatus.ACTIVE,
            is_active=True,
        )

        db.add(new_driver)

        db.commit()

        db.refresh(new_driver)

        return {
            "success": True,
            "status_code": status.HTTP_201_CREATED,
            "code": "DRIVER_CREATED",
            "message": "Driver created successfully",
            "data": _driver_response(new_driver),
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "DRIVER_ALREADY_EXISTS",
            "message": "Driver already exists or conflicts with existing data",
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


def find_driver_by_id(
    db: Session,
    current_user: User,
    company_id: UUID,
    driver_id: UUID,
):

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

    role_name = _current_role_name(current_user)

    if role_name == SUPER_ADMIN:
        if current_user.company_id != company_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "COMPANY_ACCESS_DENIED",
                "message": "You do not have access to this company",
                "data": None,
            }

    elif role_name == BRANCH_ADMIN:
        if current_user.company_id != company_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "COMPANY_ACCESS_DENIED",
                "message": "You do not have access to this company",
                "data": None,
            }

    elif role_name == DRIVER:
        if current_user.company_id != company_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "COMPANY_ACCESS_DENIED",
                "message": "You do not have access to this company",
                "data": None,
            }

    driver = get_driver_by_id_query(
        db,
        company_id,
        driver_id,
        current_user.branch_id
        if role_name in {BRANCH_ADMIN, DRIVER}
        else None,
    )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found",
            "data": None,
        }

    if not _can_access_driver(
        current_user,
        driver,
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "DRIVER_ACCESS_DENIED",
            "message": "You do not have access to this driver",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DRIVER_FOUND",
        "message": "Driver found successfully",
        "data": _driver_response(driver),
    }


def find_active_driver_by_id(
    db: Session,
    current_user: User,
    driver_id: UUID,
):

    if _current_role_name(current_user) != GLOBAL_ADMIN:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "GLOBAL_ADMIN_ACCESS_REQUIRED",
            "message": "Global admin access is required",
            "data": None,
        }

    driver = get_active_driver_by_id_admin_query(
        db,
        driver_id,
    )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DRIVER_FOUND",
        "message": "Driver found successfully",
        "data": _driver_response(driver),
    }


def find_driver_by_license_number(
    db: Session,
    current_user: User,
    company_id: UUID,
    license_number: str,
):

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

    role_name = _current_role_name(current_user)

    if role_name != GLOBAL_ADMIN:
        if current_user.company_id != company_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "COMPANY_ACCESS_DENIED",
                "message": "You do not have access to this company",
                "data": None,
            }

    if role_name == DRIVER:
        driver = get_driver_by_license_number_query(
            db,
            company_id,
            license_number,
            current_user.branch_id,
        )
    elif role_name == BRANCH_ADMIN:
        driver = get_driver_by_license_number_query(
            db,
            company_id,
            license_number,
            current_user.branch_id,
        )
    else:
        driver = get_driver_by_license_number_query(
            db,
            company_id,
            license_number,
        )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found",
            "data": None,
        }

    if not _can_access_driver(
        current_user,
        driver,
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "DRIVER_ACCESS_DENIED",
            "message": "You do not have access to this driver",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DRIVER_FOUND",
        "message": "Driver found successfully",
        "data": _driver_response(driver),
    }


def find_driver_by_license_number_admin(
    db: Session,
    current_user: User,
    license_number: str,
):

    if _current_role_name(current_user) != GLOBAL_ADMIN:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "GLOBAL_ADMIN_ACCESS_REQUIRED",
            "message": "Global admin access is required",
            "data": None,
        }

    driver = get_driver_by_license_number_admin_query(
        db,
        license_number,
    )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DRIVER_FOUND",
        "message": "Driver found successfully",
        "data": _driver_response(driver),
    }


def get_all_drivers(
    db: Session,
    current_user: User,
    company_id: UUID,
):

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

    role_name = _current_role_name(current_user)

    if role_name == GLOBAL_ADMIN:
        drivers = get_all_drivers_query(
            db,
            company_id,
        )

    elif role_name == SUPER_ADMIN:
        if current_user.company_id != company_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "COMPANY_ACCESS_DENIED",
                "message": "You do not have access to this company",
                "data": None,
            }

        drivers = get_all_drivers_query(
            db,
            company_id,
        )

    elif role_name == BRANCH_ADMIN:
        if current_user.company_id != company_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "COMPANY_ACCESS_DENIED",
                "message": "You do not have access to this company",
                "data": None,
            }

        drivers = get_all_drivers_query(
            db,
            company_id,
            current_user.branch_id,
        )

    elif role_name == DRIVER:
        if current_user.company_id != company_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "COMPANY_ACCESS_DENIED",
                "message": "You do not have access to this company",
                "data": None,
            }

        driver = (
            db.query(Driver)
            .filter(
                Driver.user_id == current_user.id,
                Driver.company_id == company_id,
                Driver.is_active.is_(True),
            )
            .first()
        )

        drivers = [driver] if driver else []

    else:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "DRIVER_ACCESS_DENIED",
            "message": "You do not have permission to view drivers",
            "data": None,
        }

    if not drivers:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_DRIVERS_FOUND",
            "message": "No drivers found",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DRIVERS_FOUND",
        "message": "Drivers retrieved successfully",
        "data": [
            _driver_response(driver)
            for driver in drivers
        ],
    }


def get_all_drivers_admin(
    db: Session,
    current_user: User,
):

    if _current_role_name(current_user) != GLOBAL_ADMIN:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "GLOBAL_ADMIN_ACCESS_REQUIRED",
            "message": "Global admin access is required",
            "data": None,
        }

    drivers = get_all_drivers_admin_query(
        db,
    )

    if not drivers:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_DRIVERS_FOUND",
            "message": "No drivers found",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DRIVERS_FOUND",
        "message": "Drivers retrieved successfully",
        "data": [
            _driver_response(driver)
            for driver in drivers
        ],
    }


def update_driver(
    db: Session,
    current_user: User,
    company_id: UUID,
    driver_id: UUID,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    license_number: str | None = None,
    license_expiry: date | None = None,
    experience_years: int | None = None,
    emergency_contact: str | None = None,
    driver_status: str | None = None,
):

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

    role_name = _current_role_name(current_user)

    if role_name == DRIVER:
        if current_user.company_id != company_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "COMPANY_ACCESS_DENIED",
                "message": "You do not have access to this company",
                "data": None,
            }

        driver = get_driver_by_id_query(
            db,
            company_id,
            driver_id,
            current_user.branch_id,
        )

        if not driver or driver.user_id != current_user.id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "DRIVER_ACCESS_DENIED",
                "message": "Drivers can only update their own profile",
                "data": None,
            }

        if (
            license_number is not None
            or license_expiry is not None
            or experience_years is not None
            or emergency_contact is not None
            or driver_status is not None
        ):
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "DRIVER_FIELDS_UPDATE_DENIED",
                "message": "Drivers cannot update license or driver management fields",
                "data": None,
            }

    else:
        driver = get_driver_by_id_query(
            db,
            company_id,
            driver_id,
            current_user.branch_id
            if role_name == BRANCH_ADMIN
            else None,
        )

        if not driver:
            return {
                "success": False,
                "status_code": status.HTTP_404_NOT_FOUND,
                "code": "DRIVER_NOT_FOUND",
                "message": "Driver not found",
                "data": None,
            }

        if not _can_manage_drivers(current_user):
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "DRIVER_UPDATE_NOT_ALLOWED",
                "message": "You do not have permission to update drivers",
                "data": None,
            }

    user = driver.user

    if email is not None and email != user.email:
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

    if phone is not None and phone != user.phone:
        existing_driver = _get_driver_phone_query(
            db,
            phone,
        )

        if (
            existing_driver
            and existing_driver.id != driver.id
        ):
            return {
                "success": False,
                "status_code": status.HTTP_409_CONFLICT,
                "code": "PHONE_ALREADY_EXISTS",
                "message": "Phone number already exists",
                "data": None,
            }

        user.phone = phone

    if first_name is not None:
        user.first_name = first_name

    if last_name is not None:
        user.last_name = last_name

    if role_name != DRIVER:

        if license_number is not None:
            existing_driver = get_driver_by_license_number_admin_query(
                db,
                license_number,
            )

            if (
                existing_driver
                and existing_driver.id != driver.id
            ):
                return {
                    "success": False,
                    "status_code": status.HTTP_409_CONFLICT,
                    "code": "LICENSE_NUMBER_ALREADY_EXISTS",
                    "message": "License number already exists",
                    "data": None,
                }

            driver.license_number = license_number

        if license_expiry is not None:
            driver.license_expiry = license_expiry

        if experience_years is not None:
            driver.experience_years = experience_years

        if emergency_contact is not None:
            driver.emergency_contact = emergency_contact

        if driver_status is not None:

            valid_statuses = {
                DriverStatus.ACTIVE,
                DriverStatus.ON_LEAVE,
                DriverStatus.SUSPENDED,
            }

            if driver_status not in valid_statuses:
                return {
                    "success": False,
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "code": "INVALID_DRIVER_STATUS",
                    "message": "Invalid driver status",
                    "data": None,
                }

            driver.status = driver_status

    try:
        db.commit()
        db.refresh(driver)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "DRIVER_UPDATED",
            "message": "Driver updated successfully",
            "data": _driver_response(driver),
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "DRIVER_UPDATE_CONFLICT",
            "message": "Driver update conflicts with existing data",
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


def activate_driver(
    db: Session,
    current_user: User,
    driver_id: UUID,
):

    if not _can_manage_drivers(current_user):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "DRIVER_ACTIVATION_NOT_ALLOWED",
            "message": "You do not have permission to activate drivers",
            "data": None,
        }

    driver = get_driver_by_id_admin_query(
        db,
        driver_id,
    )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found",
            "data": None,
        }

    if not _can_access_driver(
        current_user,
        driver,
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "DRIVER_ACCESS_DENIED",
            "message": "You do not have access to this driver",
            "data": None,
        }

    if driver.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "DRIVER_ALREADY_ACTIVE",
            "message": "Driver already active",
            "data": None,
        }

    driver.is_active = True
    driver.user.is_active = True

    try:
        db.commit()
        db.refresh(driver)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "DRIVER_ACTIVATED",
            "message": "Driver activated successfully",
            "data": _driver_response(driver),
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


def deactivate_driver(
    db: Session,
    current_user: User,
    driver_id: UUID,
):

    if not _can_manage_drivers(current_user):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "DRIVER_DEACTIVATION_NOT_ALLOWED",
            "message": "You do not have permission to deactivate drivers",
            "data": None,
        }

    driver = get_driver_by_id_admin_query(
        db,
        driver_id,
    )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found",
            "data": None,
        }

    if not _can_access_driver(
        current_user,
        driver,
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "DRIVER_ACCESS_DENIED",
            "message": "You do not have access to this driver",
            "data": None,
        }

    if not driver.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "DRIVER_ALREADY_INACTIVE",
            "message": "Driver already inactive",
            "data": None,
        }

    driver.is_active = False
    driver.user.is_active = False

    try:
        db.commit()
        db.refresh(driver)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "DRIVER_DEACTIVATED",
            "message": "Driver deactivated successfully",
            "data": _driver_response(driver),
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


def bulk_activate_drivers(
    db: Session,
    current_user: User,
    driver_ids: list[UUID],
):

    if not _can_manage_drivers(current_user):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "DRIVER_ACTIVATION_NOT_ALLOWED",
            "message": "You do not have permission to activate drivers",
            "data": None,
        }

    role_name = _current_role_name(current_user)

    company_id = (
        current_user.company_id
        if role_name in {SUPER_ADMIN, BRANCH_ADMIN}
        else None
    )

    branch_id = (
        current_user.branch_id
        if role_name == BRANCH_ADMIN
        else None
    )

    drivers = get_drivers_by_ids_query(
        db,
        driver_ids,
        company_id,
        branch_id,
    )

    if not drivers:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_DRIVERS_FOUND",
            "message": "No accessible drivers found",
            "data": None,
        }

    already_active_drivers = []
    activated_drivers = []

    for driver in drivers:

        if driver.is_active:
            already_active_drivers.append(
                _driver_bulk_item(driver)
            )
            continue

        driver.is_active = True
        driver.user.is_active = True

        activated_drivers.append(
            _driver_bulk_item(driver)
        )

    if len(already_active_drivers) == len(drivers):
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "ALL_DRIVERS_ALREADY_ACTIVE",
            "message": "All drivers are already active",
            "data": {
                "activated_drivers": [],
                "already_active_drivers": already_active_drivers,
            },
        }

    try:
        db.commit()

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "DRIVERS_ACTIVATED",
            "message": "Drivers activated successfully",
            "data": {
                "activated_drivers": activated_drivers,
                "already_active_drivers": already_active_drivers,
            },
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


def bulk_deactivate_drivers(
    db: Session,
    current_user: User,
    driver_ids: list[UUID],
):

    if not _can_manage_drivers(current_user):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "DRIVER_DEACTIVATION_NOT_ALLOWED",
            "message": "You do not have permission to deactivate drivers",
            "data": None,
        }

    role_name = _current_role_name(current_user)

    company_id = (
        current_user.company_id
        if role_name in {SUPER_ADMIN, BRANCH_ADMIN}
        else None
    )

    branch_id = (
        current_user.branch_id
        if role_name == BRANCH_ADMIN
        else None
    )

    drivers = get_drivers_by_ids_query(
        db,
        driver_ids,
        company_id,
        branch_id,
    )

    if not drivers:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_DRIVERS_FOUND",
            "message": "No accessible drivers found",
            "data": None,
        }

    already_inactive_drivers = []
    deactivated_drivers = []

    for driver in drivers:

        if not driver.is_active:
            already_inactive_drivers.append(
                _driver_bulk_item(driver)
            )
            continue

        driver.is_active = False
        driver.user.is_active = False

        deactivated_drivers.append(
            _driver_bulk_item(driver)
        )

    if len(already_inactive_drivers) == len(drivers):
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "ALL_DRIVERS_ALREADY_INACTIVE",
            "message": "All drivers are already inactive",
            "data": {
                "deactivated_drivers": [],
                "already_inactive_drivers": already_inactive_drivers,
            },
        }

    try:
        db.commit()

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "DRIVERS_DEACTIVATED",
            "message": "Drivers deactivated successfully",
            "data": {
                "deactivated_drivers": deactivated_drivers,
                "already_inactive_drivers": already_inactive_drivers,
            },
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