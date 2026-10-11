from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import status
from sqlalchemy.orm import Session

from app.models.fuel_log import FuelLog
from app.models.user import User

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

from app.reusable_functions.fuel_log_reusable import (
    get_by_id,
    get_by_company,
    get_by_vehicle,
    get_by_driver,
    get_by_date_range,
    get_by_vehicle_and_date_range,
    get_by_driver_and_date_range,
    create_record,
    update_record,
    soft_delete_record,
    get_total_cost_by_date_range,
)


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


def _get_role_name(current_user: User) -> str:
    if not current_user.role:
        return ""

    return current_user.role.name


def _is_management_role(current_user: User) -> bool:
    return _get_role_name(current_user) in MANAGEMENT_ROLES


def _is_operational_role(current_user: User) -> bool:
    return _get_role_name(current_user) in OPERATIONAL_ROLES


def _get_driver_id_for_user(current_user: User):
    if current_user.driver:
        return current_user.driver.id

    return None


def _validate_company_scope(
    current_user: User,
    company_id: UUID,
):
    role_name = _get_role_name(current_user)

    if role_name == "GLOBAL_ADMIN":
        return True

    if current_user.company_id != company_id:
        return False

    return True


def _validate_branch_scope(
    current_user: User,
    branch_id: UUID,
):
    role_name = _get_role_name(current_user)

    if role_name == "GLOBAL_ADMIN":
        return True

    if current_user.branch_id != branch_id:
        return False

    return True


def _validate_fuel_log_access(
    current_user: User,
    fuel_log: FuelLog,
) -> bool:
    role_name = _get_role_name(current_user)

    if role_name == "GLOBAL_ADMIN":
        return True

    if current_user.company_id != fuel_log.company_id:
        return False

    if role_name == "SUPER_ADMIN":
        return True

    if current_user.branch_id != fuel_log.branch_id:
        return False

    if role_name == "BRANCH_ADMIN":
        return True

    if role_name == "DRIVER":
        driver_id = _get_driver_id_for_user(current_user)

        if driver_id is None:
            return False

        return fuel_log.driver_id == driver_id

    return False


def _get_vehicle_for_user(
    db: Session,
    current_user: User,
    vehicle_id: UUID,
):
    if current_user.company_id is None:
        return None

    vehicle = get_vehicle_by_id_query(
    db=db,
    company_id=current_user.company_id,
    branch_id=current_user.branch_id,
    vehicle_id=vehicle_id,
)

    if not vehicle:
        return None

    role_name = _get_role_name(current_user)

    if role_name == "GLOBAL_ADMIN":
        return vehicle

    if vehicle.company_id != current_user.company_id:
        return None

    if vehicle.branch_id != current_user.branch_id:
        return None

    return vehicle


def _get_driver_for_user(
    db: Session,
    current_user: User,
    driver_id: UUID,
):
    if current_user.company_id is None:
        return None

    driver = get_driver_by_id_query(
        db=db,
        company_id=current_user.company_id,
        driver_id=driver_id,
    )

    if not driver:
        return None

    role_name = _get_role_name(current_user)

    if role_name == "GLOBAL_ADMIN":
        return driver

    if driver.company_id != current_user.company_id:
        return None

    if driver.branch_id != current_user.branch_id:
        return None

    return driver


def create_fuel_log(
    db: Session,
    current_user: User,
    vehicle_id: UUID,
    driver_id: UUID | None,
    fuel_date: date,
    fuel_cost: Decimal,
):
    if not _is_operational_role(current_user):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "FUEL_LOG_CREATE_FORBIDDEN",
            "message": "You do not have permission to create fuel logs",
            "data": None,
        }

    if current_user.company_id is None:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "COMPANY_NOT_ASSIGNED",
            "message": "Current user is not assigned to a company",
            "data": None,
        }

    vehicle = _get_vehicle_for_user(
        db=db,
        current_user=current_user,
        vehicle_id=vehicle_id,
    )

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found or inaccessible",
            "data": None,
        }

    if not vehicle.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "VEHICLE_INACTIVE",
            "message": "Fuel log cannot be created for an inactive vehicle",
            "data": None,
        }

    active_assignment = get_active_assignment_by_vehicle_id_query(
        db=db,
        vehicle_id=vehicle.id,
    )

    if not active_assignment:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "VEHICLE_DRIVER_NOT_ASSIGNED",
            "message": "Fuel log cannot be created because this vehicle has no assigned driver",
            "data": None,
        }

    assigned_driver = active_assignment.driver

    if not assigned_driver:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "VEHICLE_DRIVER_NOT_ASSIGNED",
            "message": "Fuel log cannot be created because this vehicle has no assigned driver",
            "data": None,
        }

    if not assigned_driver.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "VEHICLE_DRIVER_NOT_ASSIGNED",
            "message": "Fuel log cannot be created because the assigned driver is inactive",
            "data": None,
        }

    if active_assignment.company_id != vehicle.company_id:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "INVALID_ASSIGNMENT",
            "message": "Vehicle assignment is invalid",
            "data": None,
        }

    if active_assignment.branch_id != vehicle.branch_id:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "INVALID_ASSIGNMENT",
            "message": "Vehicle assignment branch does not match the vehicle branch",
            "data": None,
        }

    if assigned_driver.company_id != vehicle.company_id:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "INVALID_ASSIGNMENT",
            "message": "Assigned driver does not belong to the vehicle company",
            "data": None,
        }

    if assigned_driver.branch_id != vehicle.branch_id:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "INVALID_ASSIGNMENT",
            "message": "Assigned driver does not belong to the vehicle branch",
            "data": None,
        }

    assigned_driver_id = assigned_driver.id

    if driver_id is not None and driver_id != assigned_driver_id:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "DRIVER_ASSIGNMENT_MISMATCH",
            "message": "Selected driver is not the currently assigned driver for this vehicle",
            "data": None,
        }

    driver_id = assigned_driver_id

    role_name = _get_role_name(current_user)

    if role_name == "DRIVER":
        current_driver_id = _get_driver_id_for_user(current_user)

        if current_driver_id is None:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "DRIVER_PROFILE_NOT_FOUND",
                "message": "Driver profile not found for current user",
                "data": None,
            }

        if current_driver_id != driver_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "DRIVER_ACCESS_DENIED",
                "message": "You can only create fuel logs for your assigned vehicle",
                "data": None,
            }

    fuel_log = FuelLog(
        company_id=vehicle.company_id,
        branch_id=vehicle.branch_id,
        vehicle_id=vehicle.id,
        driver_id=driver_id,
        recorded_by=current_user.id,
        fuel_date=fuel_date,
        fuel_cost=fuel_cost,
        is_active=True,
    )

    try:
        fuel_log = create_record(db, fuel_log)

        return {
            "success": True,
            "status_code": status.HTTP_201_CREATED,
            "code": "FUEL_LOG_CREATED",
            "message": "Fuel log created successfully",
            "data": fuel_log,
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "FUEL_LOG_CREATE_FAILED",
            "message": "Failed to create fuel log",
            "data": None,
        }


def get_fuel_log(
    db: Session,
    fuel_log_id: UUID,
    current_user: User,
):
    fuel_log = get_by_id(
        db=db,
        fuel_log_id=fuel_log_id,
        active_only=True,
    )

    if not fuel_log:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "FUEL_LOG_NOT_FOUND",
            "message": "Fuel log not found",
            "data": None,
        }

    if not _validate_fuel_log_access(current_user, fuel_log):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "FUEL_LOG_ACCESS_DENIED",
            "message": "You do not have access to this fuel log",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "FUEL_LOG_FOUND",
        "message": "Fuel log retrieved successfully",
        "data": fuel_log,
    }


def get_company_fuel_logs(
    db: Session,
    current_user: User,
):
    role_name = _get_role_name(current_user)

    if role_name == "DRIVER":
        driver_id = _get_driver_id_for_user(current_user)

        if driver_id is None:
            return {
                "success": False,
                "status_code": status.HTTP_404_NOT_FOUND,
                "code": "DRIVER_PROFILE_NOT_FOUND",
                "message": "Driver profile not found",
                "data": None,
            }

        logs = get_by_driver(
            db=db,
            driver_id=driver_id,
            company_id=current_user.company_id,
            branch_id=current_user.branch_id,
        )

    elif role_name == "GLOBAL_ADMIN":
        logs = get_by_company(
            db=db,
            company_id=current_user.company_id,
        )

    elif role_name == "SUPER_ADMIN":
        logs = get_by_company(
            db=db,
            company_id=current_user.company_id,
        )

    elif role_name == "BRANCH_ADMIN":
        logs = get_by_company(
            db=db,
            company_id=current_user.company_id,
            branch_id=current_user.branch_id,
        )

    else:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "FUEL_LOG_ACCESS_DENIED",
            "message": "You do not have permission to view fuel logs",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "FUEL_LOGS_RETRIEVED",
        "message": "Fuel logs retrieved successfully",
        "data": logs,
    }


def get_inactive_company_fuel_logs(
    db: Session,
    current_user: User,
):
    if not _is_management_role(current_user):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "FUEL_LOG_ACCESS_DENIED",
            "message": "You do not have permission to view inactive fuel logs",
            "data": None,
        }

    if current_user.company_id is None:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "COMPANY_NOT_ASSIGNED",
            "message": "Current user is not assigned to a company",
            "data": None,
        }

    logs = get_by_company(
        db=db,
        company_id=current_user.company_id,
        branch_id=(
            None
            if _get_role_name(current_user) in {"GLOBAL_ADMIN", "SUPER_ADMIN"}
            else current_user.branch_id
        ),
        active_only=False,
    )

    logs = [log for log in logs if not log.is_active]

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "INACTIVE_FUEL_LOGS_RETRIEVED",
        "message": "Inactive fuel logs retrieved successfully",
        "data": logs,
    }


def get_vehicle_fuel_logs(
    db: Session,
    vehicle_id: UUID,
    current_user: User,
):
    vehicle = _get_vehicle_for_user(
        db=db,
        current_user=current_user,
        vehicle_id=vehicle_id,
    )

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found or inaccessible",
            "data": None,
        }

    role_name = _get_role_name(current_user)

    if role_name == "DRIVER":
        driver_id = _get_driver_id_for_user(current_user)

        if driver_id is None:
            return {
                "success": False,
                "status_code": status.HTTP_404_NOT_FOUND,
                "code": "DRIVER_PROFILE_NOT_FOUND",
                "message": "Driver profile not found",
                "data": None,
            }

        logs = get_by_vehicle(
            db=db,
            vehicle_id=vehicle_id,
            company_id=current_user.company_id,
            branch_id=current_user.branch_id,
        )

        logs = [
            log
            for log in logs
            if log.driver_id == driver_id
        ]

    else:
        logs = get_by_vehicle(
            db=db,
            vehicle_id=vehicle_id,
            company_id=vehicle.company_id,
            branch_id=(
                None
                if role_name in {"GLOBAL_ADMIN", "SUPER_ADMIN"}
                else current_user.branch_id
            ),
        )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "VEHICLE_FUEL_LOGS_RETRIEVED",
        "message": "Vehicle fuel logs retrieved successfully",
        "data": logs,
    }


def get_driver_fuel_logs(
    db: Session,
    driver_id: UUID,
    current_user: User,
):
    driver = _get_driver_for_user(
        db=db,
        current_user=current_user,
        driver_id=driver_id,
    )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found or inaccessible",
            "data": None,
        }

    role_name = _get_role_name(current_user)

    if role_name == "DRIVER":
        current_driver_id = _get_driver_id_for_user(current_user)

        if current_driver_id != driver_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "DRIVER_ACCESS_DENIED",
                "message": "You can only view your own fuel logs",
                "data": None,
            }

    logs = get_by_driver(
        db=db,
        driver_id=driver_id,
        company_id=driver.company_id,
        branch_id=(
            None
            if role_name in {"GLOBAL_ADMIN", "SUPER_ADMIN"}
            else current_user.branch_id
        ),
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DRIVER_FUEL_LOGS_RETRIEVED",
        "message": "Driver fuel logs retrieved successfully",
        "data": logs,
    }


def get_fuel_logs_by_date_range(
    db: Session,
    current_user: User,
    start_date: date,
    end_date: date,
):
    if start_date > end_date:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DATE_RANGE",
            "message": "Start date cannot be after end date",
            "data": None,
        }

    role_name = _get_role_name(current_user)

    if role_name == "DRIVER":
        driver_id = _get_driver_id_for_user(current_user)

        if driver_id is None:
            return {
                "success": False,
                "status_code": status.HTTP_404_NOT_FOUND,
                "code": "DRIVER_PROFILE_NOT_FOUND",
                "message": "Driver profile not found",
                "data": None,
            }

        logs = get_by_driver_and_date_range(
            db=db,
            driver_id=driver_id,
            start_date=start_date,
            end_date=end_date,
            company_id=current_user.company_id,
            branch_id=current_user.branch_id,
        )

    else:
        logs = get_by_date_range(
            db=db,
            company_id=current_user.company_id,
            start_date=start_date,
            end_date=end_date,
            branch_id=(
                None
                if role_name in {"GLOBAL_ADMIN", "SUPER_ADMIN"}
                else current_user.branch_id
            ),
        )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "FUEL_LOGS_RETRIEVED",
        "message": "Fuel logs retrieved successfully",
        "data": logs,
    }


def get_vehicle_fuel_logs_by_date_range(
    db: Session,
    vehicle_id: UUID,
    current_user: User,
    start_date: date,
    end_date: date,
):
    if start_date > end_date:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DATE_RANGE",
            "message": "Start date cannot be after end date",
            "data": None,
        }

    vehicle = _get_vehicle_for_user(
        db=db,
        current_user=current_user,
        vehicle_id=vehicle_id,
    )

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found or inaccessible",
            "data": None,
        }

    role_name = _get_role_name(current_user)

    logs = get_by_vehicle_and_date_range(
        db=db,
        vehicle_id=vehicle_id,
        start_date=start_date,
        end_date=end_date,
        company_id=vehicle.company_id,
        branch_id=(
            None
            if role_name in {"GLOBAL_ADMIN", "SUPER_ADMIN"}
            else current_user.branch_id
        ),
    )

    if role_name == "DRIVER":
        driver_id = _get_driver_id_for_user(current_user)

        logs = [
            log
            for log in logs
            if log.driver_id == driver_id
        ]

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "VEHICLE_FUEL_LOGS_RETRIEVED",
        "message": "Vehicle fuel logs retrieved successfully",
        "data": logs,
    }


def get_driver_fuel_logs_by_date_range(
    db: Session,
    driver_id: UUID,
    current_user: User,
    start_date: date,
    end_date: date,
):
    if start_date > end_date:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DATE_RANGE",
            "message": "Start date cannot be after end date",
            "data": None,
        }

    driver = _get_driver_for_user(
        db=db,
        current_user=current_user,
        driver_id=driver_id,
    )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found or inaccessible",
            "data": None,
        }

    if _get_role_name(current_user) == "DRIVER":
        current_driver_id = _get_driver_id_for_user(current_user)

        if current_driver_id != driver_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "DRIVER_ACCESS_DENIED",
                "message": "You can only view your own fuel logs",
                "data": None,
            }

    role_name = _get_role_name(current_user)

    logs = get_by_driver_and_date_range(
        db=db,
        driver_id=driver_id,
        start_date=start_date,
        end_date=end_date,
        company_id=driver.company_id,
        branch_id=(
            None
            if role_name in {"GLOBAL_ADMIN", "SUPER_ADMIN"}
            else current_user.branch_id
        ),
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DRIVER_FUEL_LOGS_RETRIEVED",
        "message": "Driver fuel logs retrieved successfully",
        "data": logs,
    }


def get_total_fuel_expense(
    db: Session,
    current_user: User,
    start_date: date,
    end_date: date,
):
    if start_date > end_date:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DATE_RANGE",
            "message": "Start date cannot be after end date",
            "data": None,
        }

    role_name = _get_role_name(current_user)

    if role_name == "DRIVER":
        driver_id = _get_driver_id_for_user(current_user)

        if driver_id is None:
            return {
                "success": False,
                "status_code": status.HTTP_404_NOT_FOUND,
                "code": "DRIVER_PROFILE_NOT_FOUND",
                "message": "Driver profile not found",
                "data": None,
            }

        logs = get_by_driver_and_date_range(
            db=db,
            driver_id=driver_id,
            start_date=start_date,
            end_date=end_date,
            company_id=current_user.company_id,
            branch_id=current_user.branch_id,
        )

        total_cost = sum(
            (log.fuel_cost for log in logs),
            Decimal("0.00"),
        )

    else:
        total_cost = get_total_cost_by_date_range(
            db=db,
            company_id=current_user.company_id,
            start_date=start_date,
            end_date=end_date,
            branch_id=(
                None
                if role_name in {"GLOBAL_ADMIN", "SUPER_ADMIN"}
                else current_user.branch_id
            ),
        )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "FUEL_EXPENSE_RETRIEVED",
        "message": "Fuel expense retrieved successfully",
        "data": {
            "start_date": start_date,
            "end_date": end_date,
            "total_cost": total_cost,
        },
    }


def get_daily_fuel_expense(
    db: Session,
    current_user: User,
    target_date: date,
):
    role_name = _get_role_name(current_user)

    if role_name == "DRIVER":
        driver_id = _get_driver_id_for_user(current_user)

        if driver_id is None:
            return {
                "success": False,
                "status_code": status.HTTP_404_NOT_FOUND,
                "code": "DRIVER_PROFILE_NOT_FOUND",
                "message": "Driver profile not found",
                "data": None,
            }

        logs = get_by_driver_and_date_range(
            db=db,
            driver_id=driver_id,
            start_date=target_date,
            end_date=target_date,
            company_id=current_user.company_id,
            branch_id=current_user.branch_id,
        )

        total_cost = sum(
            (log.fuel_cost for log in logs),
            Decimal("0.00"),
        )

    else:
        total_cost = get_total_cost_by_date_range(
            db=db,
            company_id=current_user.company_id,
            start_date=target_date,
            end_date=target_date,
            branch_id=(
                None
                if role_name in {"GLOBAL_ADMIN", "SUPER_ADMIN"}
                else current_user.branch_id
            ),
        )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DAILY_FUEL_EXPENSE_RETRIEVED",
        "message": "Daily fuel expense retrieved successfully",
        "data": {
            "expense_date": target_date,
            "total_cost": total_cost,
        },
    }


def get_seven_day_fuel_expense(
    db: Session,
    current_user: User,
    target_date: date,
):
    start_date = target_date - timedelta(days=6)

    return get_total_fuel_expense(
        db=db,
        current_user=current_user,
        start_date=start_date,
        end_date=target_date,
    )


def get_thirty_day_fuel_expense(
    db: Session,
    current_user: User,
    target_date: date,
):
    start_date = target_date - timedelta(days=29)

    return get_total_fuel_expense(
        db=db,
        current_user=current_user,
        start_date=start_date,
        end_date=target_date,
    )


def update_fuel_log(
    db: Session,
    current_user: User,
    fuel_log_id: UUID,
    fuel_date: date | None = None,
    fuel_cost: Decimal | None = None,
):
    if not _is_management_role(current_user):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "FUEL_LOG_UPDATE_FORBIDDEN",
            "message": "You do not have permission to update fuel logs",
            "data": None,
        }

    fuel_log = get_by_id(
        db=db,
        fuel_log_id=fuel_log_id,
        active_only=True,
    )

    if not fuel_log:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "FUEL_LOG_NOT_FOUND",
            "message": "Fuel log not found",
            "data": None,
        }

    if not _validate_fuel_log_access(current_user, fuel_log):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "FUEL_LOG_ACCESS_DENIED",
            "message": "You do not have access to this fuel log",
            "data": None,
        }

    if fuel_date is not None:
        fuel_log.fuel_date = fuel_date

    if fuel_cost is not None:
        fuel_log.fuel_cost = fuel_cost

    try:
        fuel_log = update_record(db, fuel_log)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "FUEL_LOG_UPDATED",
            "message": "Fuel log updated successfully",
            "data": fuel_log,
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "FUEL_LOG_UPDATE_FAILED",
            "message": "Failed to update fuel log",
            "data": None,
        }


def delete_fuel_log(
    db: Session,
    current_user: User,
    fuel_log_id: UUID,
):
    if not _is_management_role(current_user):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "FUEL_LOG_DELETE_FORBIDDEN",
            "message": "You do not have permission to delete fuel logs",
            "data": None,
        }

    fuel_log = get_by_id(
        db=db,
        fuel_log_id=fuel_log_id,
        active_only=True,
    )

    if not fuel_log:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "FUEL_LOG_NOT_FOUND",
            "message": "Fuel log not found",
            "data": None,
        }

    if not _validate_fuel_log_access(current_user, fuel_log):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "FUEL_LOG_ACCESS_DENIED",
            "message": "You do not have access to this fuel log",
            "data": None,
        }

    try:
        fuel_log = soft_delete_record(
            db=db,
            fuel_log=fuel_log,
        )

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "FUEL_LOG_DELETED",
            "message": "Fuel log deleted successfully",
            "data": fuel_log,
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "FUEL_LOG_DELETE_FAILED",
            "message": "Failed to delete fuel log",
            "data": None,
        }