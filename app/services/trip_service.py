from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.trip import Trip, TripStatus

from app.reusable_functions.trip_reusable import (
    create_record,
    delete_record,
    get_by_company,
    get_by_date_range,
    get_by_driver,
    get_by_driver_and_date_range,
    get_by_id,
    get_by_status,
    get_by_vehicle,
    get_by_vehicle_and_date_range,
    update_record,
)

from app.reusable_functions.company_reusable import (
    get_company_by_id_query,
)

from app.reusable_functions.vehicle_reusable import (
    get_vehicle_by_id_query,
)

from app.reusable_functions.driver_reusable import (
    get_driver_by_id_query,
)

from app.reusable_functions.drivervehicleassignment_reusable import (
    get_active_assignment_by_vehicle_id_query,
)


# =========================================================
# ROLE HELPERS
# =========================================================

MANAGEMENT_ROLES = {
    "GLOBAL_ADMIN",
    "SUPER_ADMIN",
    "BRANCH_ADMIN",
}

OPERATIONAL_ROLES = {
    "GLOBAL_ADMIN",
    "SUPER_ADMIN",
    "BRANCH_ADMIN",
    "DRIVER",
}


def _get_role_name(current_user) -> str | None:
    if not current_user or not current_user.role:
        return None

    return current_user.role.name


def _is_global_admin(current_user) -> bool:
    return _get_role_name(current_user) == "GLOBAL_ADMIN"


def _is_super_admin(current_user) -> bool:
    return _get_role_name(current_user) == "SUPER_ADMIN"


def _is_branch_admin(current_user) -> bool:
    return _get_role_name(current_user) == "BRANCH_ADMIN"


def _is_driver(current_user) -> bool:
    return _get_role_name(current_user) == "DRIVER"


def _can_manage_trips(current_user) -> bool:
    return _get_role_name(current_user) in MANAGEMENT_ROLES


# =========================================================
# SCOPE HELPERS
# =========================================================

def _validate_company_scope(
    current_user,
    company_id: UUID,
):
    role_name = _get_role_name(current_user)

    if role_name == "GLOBAL_ADMIN":
        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "SCOPE_VALID",
            "message": "Scope valid",
            "data": None,
        }

    if current_user.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_SCOPE_DENIED",
            "message": "You do not have access to this company",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "SCOPE_VALID",
        "message": "Scope valid",
        "data": None,
    }


def _get_branch_scope(
    current_user,
    requested_branch_id: UUID | None = None,
):
    role_name = _get_role_name(current_user)

    if role_name == "GLOBAL_ADMIN":
        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "SCOPE_VALID",
            "message": "Scope valid",
            "data": requested_branch_id,
        }

    if role_name == "SUPER_ADMIN":
        if requested_branch_id is not None:
            return {
                "success": True,
                "status_code": status.HTTP_200_OK,
                "code": "SCOPE_VALID",
                "message": "Scope valid",
                "data": requested_branch_id,
            }

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "SCOPE_VALID",
            "message": "Scope valid",
            "data": None,
        }

    if role_name in {"BRANCH_ADMIN", "DRIVER"}:
        if current_user.branch_id is None:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "BRANCH_SCOPE_MISSING",
                "message": "User is not assigned to a branch",
                "data": None,
            }

        if (
            requested_branch_id is not None
            and requested_branch_id != current_user.branch_id
        ):
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "BRANCH_SCOPE_DENIED",
                "message": "You do not have access to this branch",
                "data": None,
            }

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "SCOPE_VALID",
            "message": "Scope valid",
            "data": current_user.branch_id,
        }

    return {
        "success": False,
        "status_code": status.HTTP_403_FORBIDDEN,
        "code": "ROLE_ACCESS_DENIED",
        "message": "You do not have permission to access trips",
        "data": None,
    }


def _validate_trip_access(
    current_user,
    trip: Trip,
    allow_driver: bool = True,
):
    role_name = _get_role_name(current_user)

    if role_name == "GLOBAL_ADMIN":
        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "ACCESS_GRANTED",
            "message": "Access granted",
            "data": None,
        }

    if current_user.company_id != trip.company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "TRIP_COMPANY_SCOPE_DENIED",
            "message": "Trip does not belong to your company",
            "data": None,
        }

    if role_name == "SUPER_ADMIN":
        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "ACCESS_GRANTED",
            "message": "Access granted",
            "data": None,
        }

    if role_name == "BRANCH_ADMIN":
        if current_user.branch_id != trip.branch_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "TRIP_BRANCH_SCOPE_DENIED",
                "message": "Trip does not belong to your branch",
                "data": None,
            }

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "ACCESS_GRANTED",
            "message": "Access granted",
            "data": None,
        }

    if role_name == "DRIVER":
        if not allow_driver:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "DRIVER_ACCESS_DENIED",
                "message": "Drivers do not have permission for this operation",
                "data": None,
            }

        if current_user.branch_id != trip.branch_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "TRIP_BRANCH_SCOPE_DENIED",
                "message": "Trip does not belong to your branch",
                "data": None,
            }

        if not current_user.driver:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "DRIVER_PROFILE_NOT_FOUND",
                "message": "Driver profile not found",
                "data": None,
            }

        if current_user.driver.id != trip.driver_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "TRIP_DRIVER_ACCESS_DENIED",
                "message": "This trip is not assigned to you",
                "data": None,
            }

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "ACCESS_GRANTED",
            "message": "Access granted",
            "data": None,
        }

    return {
        "success": False,
        "status_code": status.HTTP_403_FORBIDDEN,
        "code": "ROLE_ACCESS_DENIED",
        "message": "You do not have permission to access trips",
        "data": None,
    }


# =========================================================
# CREATE
# =========================================================

def create_trip(
    db: Session,
    current_user,
    company_id: UUID,
    vehicle_id: UUID,
    driver_id: UUID,
    origin: str,
    destination: str,
    cargo_description: str | None = None,
    remarks: str | None = None,
):
    if not _can_manage_trips(current_user):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "TRIP_CREATE_FORBIDDEN",
            "message": "You do not have permission to create trips",
            "data": None,
        }

    company_scope = _validate_company_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not company_scope["success"]:
        return company_scope

    branch_scope = _get_branch_scope(
        current_user=current_user,
    )

    if not branch_scope["success"]:
        return branch_scope

    branch_id = branch_scope["data"]

    if branch_id is None and current_user.role.name == "SUPER_ADMIN":
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "BRANCH_REQUIRED",
            "message": "A branch must be specified when creating a trip",
            "data": None,
        }

    company = get_company_by_id_query(
        db=db,
        company_id=company_id,
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": None,
        }

    vehicle = get_vehicle_by_id_query(
        db=db,
        company_id=company_id,
        vehicle_id=vehicle_id,
        branch_id=branch_id,
    )

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found, inactive, or outside your branch",
            "data": None,
        }

    driver = get_driver_by_id_query(
        db=db,
        company_id=company_id,
        driver_id=driver_id,
        branch_id=branch_id,
    )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found, inactive, or outside your branch",
            "data": None,
        }

    active_assignment = get_active_assignment_by_vehicle_id_query(
        db=db,
        vehicle_id=vehicle_id,
    )

    if not active_assignment:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "VEHICLE_HAS_NO_DRIVER",
            "message": "This vehicle does not have an active driver assigned",
            "data": None,
        }

    if active_assignment.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "ASSIGNMENT_COMPANY_MISMATCH",
            "message": "Vehicle assignment does not belong to this company",
            "data": None,
        }

    if active_assignment.branch_id != branch_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "ASSIGNMENT_BRANCH_MISMATCH",
            "message": "Vehicle assignment does not belong to this branch",
            "data": None,
        }

    if active_assignment.driver_id != driver_id:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "DRIVER_NOT_ASSIGNED_TO_VEHICLE",
            "message": "The selected driver is not assigned to this vehicle",
            "data": None,
        }

    trip = Trip(
        company_id=company_id,
        branch_id=branch_id,
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        created_by=current_user.id,
        origin=origin,
        destination=destination,
        cargo_description=cargo_description,
        remarks=remarks,
        status=TripStatus.CREATED,
        is_active=True,
    )

    try:
        trip = create_record(
            db=db,
            trip=trip,
        )

        return {
            "success": True,
            "status_code": status.HTTP_201_CREATED,
            "code": "TRIP_CREATED",
            "message": "Trip created successfully",
            "data": trip,
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "TRIP_CREATION_FAILED",
            "message": "Trip could not be created",
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


# =========================================================
# GET ONE
# =========================================================

def get_trip(
    db: Session,
    current_user,
    company_id: UUID,
    trip_id: UUID,
):
    company_scope = _validate_company_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not company_scope["success"]:
        return company_scope

    branch_scope = _get_branch_scope(
        current_user=current_user,
    )

    if not branch_scope["success"]:
        return branch_scope

    trip = get_by_id(
        db=db,
        trip_id=trip_id,
        company_id=company_id,
        branch_id=branch_scope["data"],
    )

    if not trip:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "TRIP_NOT_FOUND",
            "message": "Trip not found",
            "data": None,
        }

    access = _validate_trip_access(
        current_user=current_user,
        trip=trip,
        allow_driver=True,
    )

    if not access["success"]:
        return access

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "TRIP_FOUND",
        "message": "Trip found successfully",
        "data": trip,
    }


# =========================================================
# GET COMPANY TRIPS
# =========================================================

def get_company_trips(
    db: Session,
    current_user,
    company_id: UUID,
):
    company_scope = _validate_company_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not company_scope["success"]:
        return company_scope

    branch_scope = _get_branch_scope(
        current_user=current_user,
    )

    if not branch_scope["success"]:
        return branch_scope

    branch_id = branch_scope["data"]

    if _is_driver(current_user):
        if not current_user.driver:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "DRIVER_PROFILE_NOT_FOUND",
                "message": "Driver profile not found",
                "data": None,
            }

        trips = get_by_driver(
            db=db,
            driver_id=current_user.driver.id,
            company_id=company_id,
            branch_id=branch_id,
        )
    else:
        trips = get_by_company(
            db=db,
            company_id=company_id,
            branch_id=branch_id,
        )

    if not trips:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_TRIPS_FOUND",
            "message": "No trips found",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "TRIPS_FOUND",
        "message": "Trips retrieved successfully",
        "data": trips,
    }


# =========================================================
# GET VEHICLE TRIPS
# =========================================================

def get_vehicle_trips(
    db: Session,
    current_user,
    company_id: UUID,
    vehicle_id: UUID,
):
    if _is_driver(current_user):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "DRIVER_VEHICLE_TRIP_ACCESS_DENIED",
            "message": "Drivers cannot query trips by vehicle",
            "data": None,
        }

    company_scope = _validate_company_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not company_scope["success"]:
        return company_scope

    branch_scope = _get_branch_scope(
        current_user=current_user,
    )

    if not branch_scope["success"]:
        return branch_scope

    branch_id = branch_scope["data"]

    vehicle = get_vehicle_by_id_query(
        db=db,
        company_id=company_id,
        vehicle_id=vehicle_id,
        branch_id=branch_id,
    )

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found, inactive, or outside your branch",
            "data": None,
        }

    trips = get_by_vehicle(
        db=db,
        vehicle_id=vehicle_id,
        company_id=company_id,
        branch_id=branch_id,
    )

    if not trips:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_TRIPS_FOUND",
            "message": "No trips found for this vehicle",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "VEHICLE_TRIPS_FOUND",
        "message": "Vehicle trips retrieved successfully",
        "data": trips,
    }


# =========================================================
# GET DRIVER TRIPS
# =========================================================

def get_driver_trips(
    db: Session,
    current_user,
    company_id: UUID,
    driver_id: UUID,
):
    company_scope = _validate_company_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not company_scope["success"]:
        return company_scope

    branch_scope = _get_branch_scope(
        current_user=current_user,
    )

    if not branch_scope["success"]:
        return branch_scope

    branch_id = branch_scope["data"]

    if _is_driver(current_user):
        if not current_user.driver or current_user.driver.id != driver_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "DRIVER_TRIP_ACCESS_DENIED",
                "message": "You can only access your own trips",
                "data": None,
            }

    driver = get_driver_by_id_query(
        db=db,
        company_id=company_id,
        driver_id=driver_id,
        branch_id=branch_id,
    )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found, inactive, or outside your branch",
            "data": None,
        }

    trips = get_by_driver(
        db=db,
        driver_id=driver_id,
        company_id=company_id,
        branch_id=branch_id,
    )

    if not trips:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_TRIPS_FOUND",
            "message": "No trips found for this driver",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DRIVER_TRIPS_FOUND",
        "message": "Driver trips retrieved successfully",
        "data": trips,
    }


# =========================================================
# GET BY STATUS
# =========================================================

def get_trips_by_status(
    db: Session,
    current_user,
    company_id: UUID,
    status_value: str,
):
    company_scope = _validate_company_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not company_scope["success"]:
        return company_scope

    valid_statuses = {
        TripStatus.CREATED,
        TripStatus.STARTED,
        TripStatus.COMPLETED,
        TripStatus.CANCELLED,
    }

    try:
        status_value = TripStatus(status_value)
    except ValueError:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_TRIP_STATUS",
            "message": "Invalid trip status",
            "data": None,
        }

    if status_value not in valid_statuses:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_TRIP_STATUS",
            "message": "Invalid trip status",
            "data": None,
        }

    branch_scope = _get_branch_scope(
        current_user=current_user,
    )

    if not branch_scope["success"]:
        return branch_scope

    branch_id = branch_scope["data"]

    if _is_driver(current_user):
        if not current_user.driver:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "DRIVER_PROFILE_NOT_FOUND",
                "message": "Driver profile not found",
                "data": None,
            }

        trips = get_by_driver(
            db=db,
            driver_id=current_user.driver.id,
            company_id=company_id,
            branch_id=branch_id,
        )

        trips = [
            trip
            for trip in trips
            if trip.status == status_value
        ]
    else:
        trips = get_by_status(
            db=db,
            company_id=company_id,
            status=status_value,
            branch_id=branch_id,
        )

    if not trips:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_TRIPS_FOUND",
            "message": "No trips found with the specified status",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "TRIPS_FOUND",
        "message": "Trips retrieved successfully",
        "data": trips,
    }


# =========================================================
# GET BY DATE RANGE
# =========================================================

def get_trips_by_date_range(
    db: Session,
    current_user,
    company_id: UUID,
    start_date: date,
    end_date: date,
):
    company_scope = _validate_company_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not company_scope["success"]:
        return company_scope

    if start_date > end_date:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DATE_RANGE",
            "message": "Start date cannot be later than end date",
            "data": None,
        }

    branch_scope = _get_branch_scope(
        current_user=current_user,
    )

    if not branch_scope["success"]:
        return branch_scope

    branch_id = branch_scope["data"]

    if _is_driver(current_user):
        if not current_user.driver:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "DRIVER_PROFILE_NOT_FOUND",
                "message": "Driver profile not found",
                "data": None,
            }

        trips = get_by_driver_and_date_range(
            db=db,
            driver_id=current_user.driver.id,
            start_date=start_date,
            end_date=end_date,
            company_id=company_id,
            branch_id=branch_id,
        )
    else:
        trips = get_by_date_range(
            db=db,
            company_id=company_id,
            start_date=start_date,
            end_date=end_date,
            branch_id=branch_id,
        )

    if not trips:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_TRIPS_FOUND",
            "message": "No trips found for the specified date range",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "TRIPS_FOUND",
        "message": "Trips retrieved successfully",
        "data": trips,
    }


# =========================================================
# VEHICLE DATE RANGE
# =========================================================

def get_vehicle_trips_by_date_range(
    db: Session,
    current_user,
    company_id: UUID,
    vehicle_id: UUID,
    start_date: date,
    end_date: date,
):
    if _is_driver(current_user):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "DRIVER_VEHICLE_TRIP_ACCESS_DENIED",
            "message": "Drivers cannot query trips by vehicle",
            "data": None,
        }

    company_scope = _validate_company_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not company_scope["success"]:
        return company_scope

    if start_date > end_date:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DATE_RANGE",
            "message": "Start date cannot be later than end date",
            "data": None,
        }

    branch_scope = _get_branch_scope(
        current_user=current_user,
    )

    if not branch_scope["success"]:
        return branch_scope

    branch_id = branch_scope["data"]

    vehicle = get_vehicle_by_id_query(
        db=db,
        company_id=company_id,
        vehicle_id=vehicle_id,
        branch_id=branch_id,
    )

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found, inactive, or outside your branch",
            "data": None,
        }

    trips = get_by_vehicle_and_date_range(
        db=db,
        vehicle_id=vehicle_id,
        start_date=start_date,
        end_date=end_date,
        company_id=company_id,
        branch_id=branch_id,
    )

    if not trips:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_TRIPS_FOUND",
            "message": "No trips found for this vehicle in the specified date range",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "VEHICLE_TRIPS_FOUND",
        "message": "Vehicle trips retrieved successfully",
        "data": trips,
    }


# =========================================================
# DRIVER DATE RANGE
# =========================================================

def get_driver_trips_by_date_range(
    db: Session,
    current_user,
    company_id: UUID,
    driver_id: UUID,
    start_date: date,
    end_date: date,
):
    company_scope = _validate_company_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not company_scope["success"]:
        return company_scope

    if start_date > end_date:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DATE_RANGE",
            "message": "Start date cannot be later than end date",
            "data": None,
        }

    branch_scope = _get_branch_scope(
        current_user=current_user,
    )

    if not branch_scope["success"]:
        return branch_scope

    branch_id = branch_scope["data"]

    if _is_driver(current_user):
        if not current_user.driver or current_user.driver.id != driver_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "DRIVER_TRIP_ACCESS_DENIED",
                "message": "You can only access your own trips",
                "data": None,
            }

    driver = get_driver_by_id_query(
        db=db,
        company_id=company_id,
        driver_id=driver_id,
        branch_id=branch_id,
    )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found, inactive, or outside your branch",
            "data": None,
        }

    trips = get_by_driver_and_date_range(
        db=db,
        driver_id=driver_id,
        start_date=start_date,
        end_date=end_date,
        company_id=company_id,
        branch_id=branch_id,
    )

    if not trips:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_TRIPS_FOUND",
            "message": "No trips found for this driver in the specified date range",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DRIVER_TRIPS_FOUND",
        "message": "Driver trips retrieved successfully",
        "data": trips,
    }


# =========================================================
# UPDATE
# =========================================================

def update_trip(
    db: Session,
    current_user,
    company_id: UUID,
    trip_id: UUID,
    origin: str | None = None,
    destination: str | None = None,
    cargo_description: str | None = None,
    remarks: str | None = None,
):
    if not _can_manage_trips(current_user):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "TRIP_UPDATE_FORBIDDEN",
            "message": "You do not have permission to update trips",
            "data": None,
        }

    company_scope = _validate_company_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not company_scope["success"]:
        return company_scope

    branch_scope = _get_branch_scope(
        current_user=current_user,
    )

    if not branch_scope["success"]:
        return branch_scope

    trip = get_by_id(
        db=db,
        trip_id=trip_id,
        company_id=company_id,
        branch_id=branch_scope["data"],
    )

    if not trip:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "TRIP_NOT_FOUND",
            "message": "Trip not found",
            "data": None,
        }

    if trip.status != TripStatus.CREATED:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "TRIP_UPDATE_NOT_ALLOWED",
            "message": "Only trips with CREATED status can be updated",
            "data": None,
        }

    if origin is not None:
        trip.origin = origin

    if destination is not None:
        trip.destination = destination

    if cargo_description is not None:
        trip.cargo_description = cargo_description

    if remarks is not None:
        trip.remarks = remarks

    try:
        trip = update_record(
            db=db,
            trip=trip,
        )

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "TRIP_UPDATED",
            "message": "Trip updated successfully",
            "data": trip,
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "TRIP_UPDATE_FAILED",
            "message": "Trip could not be updated",
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


# =========================================================
# START TRIP
# =========================================================

def start_trip(
    db: Session,
    current_user,
    company_id: UUID,
    trip_id: UUID,
):
    if _get_role_name(current_user) not in OPERATIONAL_ROLES:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "TRIP_START_FORBIDDEN",
            "message": "You do not have permission to start trips",
            "data": None,
        }

    company_scope = _validate_company_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not company_scope["success"]:
        return company_scope

    branch_scope = _get_branch_scope(
        current_user=current_user,
    )

    if not branch_scope["success"]:
        return branch_scope

    trip = get_by_id(
        db=db,
        trip_id=trip_id,
        company_id=company_id,
        branch_id=branch_scope["data"],
    )

    if not trip:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "TRIP_NOT_FOUND",
            "message": "Trip not found",
            "data": None,
        }

    access = _validate_trip_access(
        current_user=current_user,
        trip=trip,
        allow_driver=True,
    )

    if not access["success"]:
        return access

    if trip.status != TripStatus.CREATED:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "TRIP_START_NOT_ALLOWED",
            "message": "Only trips with CREATED status can be started",
            "data": None,
        }

    active_assignment = get_active_assignment_by_vehicle_id_query(
        db=db,
        vehicle_id=trip.vehicle_id,
    )

    if not active_assignment:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "VEHICLE_HAS_NO_DRIVER",
            "message": "The vehicle no longer has an active driver assignment",
            "data": None,
        }

    if (
        active_assignment.company_id != trip.company_id
        or active_assignment.branch_id != trip.branch_id
        or active_assignment.driver_id != trip.driver_id
    ):
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "TRIP_ASSIGNMENT_MISMATCH",
            "message": "The trip driver is no longer assigned to this vehicle",
            "data": None,
        }

    started_trips = get_by_status(
        db=db,
        company_id=company_id,
        status=TripStatus.STARTED,
        branch_id=trip.branch_id,
    )

    for started_trip in started_trips:
        if started_trip.id == trip.id:
            continue

        if started_trip.vehicle_id == trip.vehicle_id:
            return {
                "success": False,
                "status_code": status.HTTP_409_CONFLICT,
                "code": "VEHICLE_ALREADY_ON_TRIP",
                "message": "Vehicle already has an active trip",
                "data": None,
            }

        if started_trip.driver_id == trip.driver_id:
            return {
                "success": False,
                "status_code": status.HTTP_409_CONFLICT,
                "code": "DRIVER_ALREADY_ON_TRIP",
                "message": "Driver already has an active trip",
                "data": None,
            }

    trip.status = TripStatus.STARTED
    trip.actual_start = datetime.now(timezone.utc)

    try:
        trip = update_record(
            db=db,
            trip=trip,
        )

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "TRIP_STARTED",
            "message": "Trip started successfully",
            "data": trip,
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "TRIP_START_FAILED",
            "message": "Trip could not be started",
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


# =========================================================
# COMPLETE TRIP
# =========================================================

def complete_trip(
    db: Session,
    current_user,
    company_id: UUID,
    trip_id: UUID,
):
    if _get_role_name(current_user) not in OPERATIONAL_ROLES:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "TRIP_COMPLETE_FORBIDDEN",
            "message": "You do not have permission to complete trips",
            "data": None,
        }

    company_scope = _validate_company_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not company_scope["success"]:
        return company_scope

    branch_scope = _get_branch_scope(
        current_user=current_user,
    )

    if not branch_scope["success"]:
        return branch_scope

    trip = get_by_id(
        db=db,
        trip_id=trip_id,
        company_id=company_id,
        branch_id=branch_scope["data"],
    )

    if not trip:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "TRIP_NOT_FOUND",
            "message": "Trip not found",
            "data": None,
        }

    access = _validate_trip_access(
        current_user=current_user,
        trip=trip,
        allow_driver=True,
    )

    if not access["success"]:
        return access

    if trip.status != TripStatus.STARTED:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "TRIP_COMPLETION_NOT_ALLOWED",
            "message": "Only started trips can be completed",
            "data": None,
        }

    trip.status = TripStatus.COMPLETED
    trip.actual_end = datetime.now(timezone.utc)

    try:
        trip = update_record(
            db=db,
            trip=trip,
        )

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "TRIP_COMPLETED",
            "message": "Trip completed successfully",
            "data": trip,
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "TRIP_COMPLETION_FAILED",
            "message": "Trip could not be completed",
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


# =========================================================
# CANCEL TRIP
# =========================================================

def cancel_trip(
    db: Session,
    current_user,
    company_id: UUID,
    trip_id: UUID,
):
    if _get_role_name(current_user) not in OPERATIONAL_ROLES:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "TRIP_CANCEL_FORBIDDEN",
            "message": "You do not have permission to cancel trips",
            "data": None,
        }

    company_scope = _validate_company_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not company_scope["success"]:
        return company_scope

    branch_scope = _get_branch_scope(
        current_user=current_user,
    )

    if not branch_scope["success"]:
        return branch_scope

    trip = get_by_id(
        db=db,
        trip_id=trip_id,
        company_id=company_id,
        branch_id=branch_scope["data"],
    )

    if not trip:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "TRIP_NOT_FOUND",
            "message": "Trip not found",
            "data": None,
        }

    access = _validate_trip_access(
        current_user=current_user,
        trip=trip,
        allow_driver=True,
    )

    if not access["success"]:
        return access

    if trip.status not in (
        TripStatus.CREATED,
        TripStatus.STARTED,
    ):
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "TRIP_CANCELLATION_NOT_ALLOWED",
            "message": "Only created or started trips can be cancelled",
            "data": None,
        }

    trip.status = TripStatus.CANCELLED

    try:
        trip = update_record(
            db=db,
            trip=trip,
        )

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "TRIP_CANCELLED",
            "message": "Trip cancelled successfully",
            "data": trip,
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "TRIP_CANCELLATION_FAILED",
            "message": "Trip could not be cancelled",
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


# =========================================================
# DELETE / SOFT DELETE
# =========================================================

def delete_trip(
    db: Session,
    current_user,
    company_id: UUID,
    trip_id: UUID,
):
    if not _can_manage_trips(current_user):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "TRIP_DELETE_FORBIDDEN",
            "message": "You do not have permission to delete trips",
            "data": None,
        }

    company_scope = _validate_company_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not company_scope["success"]:
        return company_scope

    branch_scope = _get_branch_scope(
        current_user=current_user,
    )

    if not branch_scope["success"]:
        return branch_scope

    trip = get_by_id(
        db=db,
        trip_id=trip_id,
        company_id=company_id,
        branch_id=branch_scope["data"],
    )

    if not trip:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "TRIP_NOT_FOUND",
            "message": "Trip not found",
            "data": None,
        }

    if trip.status != TripStatus.CREATED:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "TRIP_DELETE_NOT_ALLOWED",
            "message": "Only created trips can be deleted",
            "data": None,
        }

    try:
        trip = delete_record(
            db=db,
            trip=trip,
        )

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "TRIP_DELETED",
            "message": "Trip deleted successfully",
            "data": trip,
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "TRIP_DELETE_FAILED",
            "message": "Trip could not be deleted",
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