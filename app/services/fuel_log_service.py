from datetime import date
from fastapi import status
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
from datetime import date, timedelta
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.fuel_log import FuelLog
from app.reusable_functions.fuel_log_reusable import (
    create_record,
    get_by_id,
    get_by_company,
    get_by_vehicle, 
    get_by_driver,
    get_by_date_range,
    get_total_cost,
    get_by_vehicle_and_date_range,
    get_by_driver_and_date_range,
    update_record,
    soft_delete_record, get_total_cost_by_date_range
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

from app.reusable_functions.user_reusable import (
    get_user_by_id_query,
)

def create_fuel_log(
    db: Session,
    company_id: UUID,
    vehicle_id: UUID,
    driver_id: UUID | None,
    recorded_by: UUID,
    fuel_date: date,
    fuel_cost: Decimal,
):

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
            "data": None
        }

    vehicle = get_vehicle_by_id_query(
        db=db,
        company_id=company_id,
        vehicle_id=vehicle_id,
    )

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found, inactive, or does not belong to this company",
            "data": None
        }

    if driver_id is not None:

        driver = get_driver_by_id_query(
            db=db,
            company_id=company_id,
            driver_id=driver_id,
        )

        if not driver:
            return {
                "success": False,
                "status_code": status.HTTP_404_NOT_FOUND,
                "code": "DRIVER_NOT_FOUND",
                "message": "Driver not found, inactive, or does not belong to this company",
                "data": None
            }

    user = get_user_by_id_query(
        db=db,
        user_id=recorded_by,
    )

    if not user:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "USER_NOT_FOUND",
            "message": "User not found or inactive",
            "data": None
        }

    if user.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "USER_COMPANY_MISMATCH",
            "message": "User does not belong to this company",
            "data": None
        }

    if fuel_cost <= Decimal("0"):
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_FUEL_COST",
            "message": "Fuel cost must be greater than zero",
            "data": None
        }

    fuel_log = FuelLog(
        company_id=company_id,
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        recorded_by=recorded_by,
        fuel_date=fuel_date,
        fuel_cost=fuel_cost,
        is_active=True,
    )

    try:
        fuel_log = create_record(
            db=db,
            fuel_log=fuel_log,
        )

        return {
            "success": True,
            "status_code": status.HTTP_201_CREATED,
            "code": "FUEL_LOG_CREATED",
            "message": "Fuel log created successfully",
            "data": fuel_log
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "FUEL_LOG_CREATION_FAILED",
            "message": "Fuel log could not be created",
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
    
    
def get_fuel_log(
    db: Session,
    company_id: UUID,
    fuel_log_id: UUID,
):

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
            "data": None
        }

    fuel_log = get_by_id(
        db=db,
        fuel_log_id=fuel_log_id,
    )

    if not fuel_log:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "FUEL_LOG_NOT_FOUND",
            "message": "Fuel log not found or inactive",
            "data": None
        }

    if fuel_log.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "FUEL_LOG_COMPANY_MISMATCH",
            "message": "Fuel log does not belong to this company",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "FUEL_LOG_FOUND",
        "message": "Fuel log retrieved successfully",
        "data": fuel_log
    }


def get_company_fuel_logs(
    db: Session,
    company_id: UUID,
):

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
            "data": None
        }

    fuel_logs = get_by_company(
        db=db,
        company_id=company_id,
    )

    if not fuel_logs:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_FUEL_LOGS_FOUND",
            "message": "No fuel logs found for this company",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "FUEL_LOGS_FOUND",
        "message": "Company fuel logs retrieved successfully",
        "data": fuel_logs
    }


def get_inactive_company_fuel_logs(
    db: Session,
    company_id: UUID,
):
    fuel_logs = get_by_company(
        db=db,
        company_id=company_id,
    )

    inactive_fuel_logs = [
        fuel_log
        for fuel_log in fuel_logs
        if not fuel_log.is_active
    ]

    if not inactive_fuel_logs:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_INACTIVE_FUEL_LOGS_FOUND",
            "message": "No inactive fuel logs found for this company",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "INACTIVE_FUEL_LOGS_FOUND",
        "message": "Inactive fuel logs retrieved successfully",
        "data": inactive_fuel_logs
    }


def get_vehicle_fuel_logs(
    db: Session,
    company_id: UUID,
    vehicle_id: UUID,
):

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
            "data": None
        }

    vehicle = get_vehicle_by_id_query(
        db=db,
        company_id=company_id,
        vehicle_id=vehicle_id,
    )

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found, inactive, or does not belong to this company",
            "data": None
        }

    fuel_logs = get_by_vehicle(
        db=db,
        vehicle_id=vehicle_id,
    )

    if not fuel_logs:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_FUEL_LOGS_FOUND",
            "message": "No fuel logs found for this vehicle",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "VEHICLE_FUEL_LOGS_FOUND",
        "message": "Vehicle fuel logs retrieved successfully",
        "data": fuel_logs
    }


def get_driver_fuel_logs(
    db: Session,
    company_id: UUID,
    driver_id: UUID,
):

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
            "data": None
        }

    driver = get_driver_by_id_query(
        db=db,
        company_id=company_id,
        driver_id=driver_id,
    )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found, inactive, or does not belong to this company",
            "data": None
        }

    fuel_logs = get_by_driver(
        db=db,
        driver_id=driver_id,
    )

    if not fuel_logs:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_FUEL_LOGS_FOUND",
            "message": "No fuel logs found for this driver",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DRIVER_FUEL_LOGS_FOUND",
        "message": "Driver fuel logs retrieved successfully",
        "data": fuel_logs
    }


def get_fuel_logs_by_date_range(
    db: Session,
    company_id: UUID,
    start_date: date,
    end_date: date,
):

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
            "data": None
        }

    if start_date > end_date:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DATE_RANGE",
            "message": "Start date cannot be later than end date",
            "data": None
        }

    fuel_logs = get_by_date_range(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
    )

    if not fuel_logs:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_FUEL_LOGS_FOUND",
            "message": "No fuel logs found for the specified date range",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "FUEL_LOGS_FOUND",
        "message": "Fuel logs retrieved successfully",
        "data": fuel_logs
    }


def get_vehicle_fuel_logs_by_date_range(
    db: Session,
    company_id: UUID,
    vehicle_id: UUID,
    start_date: date,
    end_date: date,
):

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
            "data": None
        }

    vehicle = get_vehicle_by_id_query(
        db=db,
        company_id=company_id,
        vehicle_id=vehicle_id,
    )

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found, inactive, or does not belong to this company",
            "data": None
        }

    if start_date > end_date:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DATE_RANGE",
            "message": "Start date cannot be later than end date",
            "data": None
        }

    fuel_logs = get_by_vehicle_and_date_range(
        db=db,
        vehicle_id=vehicle_id,
        start_date=start_date,
        end_date=end_date,
    )

    if not fuel_logs:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_FUEL_LOGS_FOUND",
            "message": "No fuel logs found for this vehicle in the specified date range",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "VEHICLE_FUEL_LOGS_FOUND",
        "message": "Vehicle fuel logs retrieved successfully",
        "data": fuel_logs
    }


def get_7_day_fuel_expense(
    db: Session,
    company_id: UUID,
    end_date: date,
):

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
            "data": None
        }

    start_date = end_date - timedelta(days=6)

    total_cost = get_total_cost_by_date_range(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "SEVEN_DAY_FUEL_EXPENSE",
        "message": "7-day fuel expense calculated successfully",
        "data": {
            "start_date": start_date,
            "end_date": end_date,
            "total_cost": total_cost,
        }
    }


def get_30_day_fuel_expense(
    db: Session,
    company_id: UUID,
    end_date: date,
):

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
            "data": None
        }

    start_date = end_date - timedelta(days=29)

    total_cost = get_total_cost_by_date_range(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "THIRTY_DAY_FUEL_EXPENSE",
        "message": "30-day fuel expense calculated successfully",
        "data": {
            "start_date": start_date,
            "end_date": end_date,
            "total_cost": total_cost,
        }
    }

def get_driver_fuel_logs_by_date_range(
    db: Session,
    company_id: UUID,
    driver_id: UUID,
    start_date: date,
    end_date: date,
):

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
            "data": None
        }

    driver = get_driver_by_id_query(
        db=db,
        company_id=company_id,
        driver_id=driver_id,
    )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found, inactive, or does not belong to this company",
            "data": None
        }

    if start_date > end_date:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DATE_RANGE",
            "message": "Start date cannot be later than end date",
            "data": None
        }

    fuel_logs = get_by_driver_and_date_range(
        db=db,
        driver_id=driver_id,
        start_date=start_date,
        end_date=end_date,
    )

    if not fuel_logs:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_FUEL_LOGS_FOUND",
            "message": "No fuel logs found for this driver in the specified date range",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DRIVER_FUEL_LOGS_FOUND",
        "message": "Driver fuel logs retrieved successfully",
        "data": fuel_logs
    }


def update_fuel_log(
    db: Session,
    company_id: UUID,
    fuel_log_id: UUID,
    fuel_date: date | None = None,
    fuel_cost: Decimal | None = None,
):

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
            "data": None
        }

    fuel_log = get_by_id(
        db=db,
        fuel_log_id=fuel_log_id,
    )

    if not fuel_log:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "FUEL_LOG_NOT_FOUND",
            "message": "Fuel log not found or inactive",
            "data": None
        }

    if fuel_log.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "FUEL_LOG_COMPANY_MISMATCH",
            "message": "Fuel log does not belong to this company",
            "data": None
        }

    if fuel_cost is not None and fuel_cost <= Decimal("0"):
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_FUEL_COST",
            "message": "Fuel cost must be greater than zero",
            "data": None
        }

    if fuel_date is not None:
        fuel_log.fuel_date = fuel_date

    if fuel_cost is not None:
        fuel_log.fuel_cost = fuel_cost

    try:
        fuel_log = update_record(
            db=db,
            fuel_log=fuel_log,
        )

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "FUEL_LOG_UPDATED",
            "message": "Fuel log updated successfully",
            "data": fuel_log
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "FUEL_LOG_UPDATE_FAILED",
            "message": "Fuel log could not be updated",
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

        

def delete_fuel_log(
    db: Session,
    company_id: UUID,
    fuel_log_id: UUID,
):

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
            "data": None
        }

    fuel_log = get_by_id(
        db=db,
        fuel_log_id=fuel_log_id,
    )

    if not fuel_log:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "FUEL_LOG_NOT_FOUND",
            "message": "Fuel log not found or inactive",
            "data": None
        }

    if fuel_log.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "FUEL_LOG_COMPANY_MISMATCH",
            "message": "Fuel log does not belong to this company",
            "data": None
        }

    if not fuel_log.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "FUEL_LOG_ALREADY_DELETED",
            "message": "Fuel log is already inactive",
            "data": None
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
            "data": None
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "FUEL_LOG_DELETE_FAILED",
            "message": "Fuel log could not be deleted",
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


def get_total_fuel_expense(
    db: Session,
    company_id: UUID,
):

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
            "data": None
        }

    fuel_logs = get_by_company(
        db=db,
        company_id=company_id,
    )

    active_fuel_logs = [
        fuel_log
        for fuel_log in fuel_logs
        if fuel_log.is_active
    ]

    total_cost = get_total_cost(active_fuel_logs)

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "TOTAL_FUEL_EXPENSE",
        "message": "Total fuel expense calculated successfully",
        "data": total_cost
    }


def get_daily_fuel_expense(
    db: Session,
    company_id: UUID,
    target_date: date,
):

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
            "data": None
        }

    fuel_logs = get_by_date_range(
        db=db,
        company_id=company_id,
        start_date=target_date,
        end_date=target_date,
    )

    active_fuel_logs = [
        fuel_log
        for fuel_log in fuel_logs
        if fuel_log.is_active
    ]

    total_cost = get_total_cost(active_fuel_logs)

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DAILY_FUEL_EXPENSE",
        "message": "Daily fuel expense calculated successfully",
        "data": {
            "date": target_date,
            "total_cost": total_cost,
        }
    }
