from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.maintenance_record import MaintenanceRecord, MaintenanceType

from app.reusable_functions.maintenancerecord_reusable import (
    create_record,
    get_by_id,
    get_by_company,
    get_by_vehicle,
    get_by_vehicle_and_date_range,
    get_by_date_range,
    get_by_maintenance_type,
    get_total_cost,
    get_vehicle_total_cost,
    get_total_cost_by_date_range,
    get_vehicle_total_cost_by_date_range,
    update_record,
    soft_delete_record,
    get_upcoming_by_date,
    get_by_due_date,
)

from app.reusable_functions.company_reusable import (
    get_company_by_id_query,
)

from app.reusable_functions.vehicle_reusable import (
    get_vehicle_by_id_query,
    get_vehicle_by_company_id_query,
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


VALID_MAINTENANCE_TYPES = {
    MaintenanceType.ENGINE_OIL,
    MaintenanceType.OIL_FILTER,
    MaintenanceType.AIR_FILTER,
    MaintenanceType.FUEL_FILTER,
    MaintenanceType.BRAKE_SERVICE,
    MaintenanceType.TYRE_CHANGE,
    MaintenanceType.WHEEL_ALIGNMENT,
    MaintenanceType.WHEEL_BALANCING,
    MaintenanceType.BATTERY_REPLACEMENT,
    MaintenanceType.CLUTCH_REPLACEMENT,
    MaintenanceType.GEARBOX_SERVICE,
    MaintenanceType.ENGINE_REPAIR,
    MaintenanceType.COOLANT_SERVICE,
    MaintenanceType.SUSPENSION_SERVICE,
    MaintenanceType.ELECTRICAL_REPAIR,
    MaintenanceType.AC_SERVICE,
    MaintenanceType.GENERAL_SERVICE,
    MaintenanceType.INSPECTION,
    MaintenanceType.OTHER,
}


def _get_role_name(current_user):
    return getattr(
        getattr(current_user, "role", None),
        "name",
        None,
    )


def _get_scope(
    current_user,
    company_id: UUID,
    branch_id: UUID | None = None,
):
    role_name = _get_role_name(current_user)

    if role_name not in OPERATIONAL_ROLES:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "INSUFFICIENT_PERMISSIONS",
            "message": "You do not have permission to access maintenance records",
            "data": None,
        }

    if role_name == "GLOBAL_ADMIN":
        return {
            "success": True,
            "company_id": company_id,
            "branch_id": branch_id,
        }

    if current_user.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_ACCESS_DENIED",
            "message": "You do not have access to this company",
            "data": None,
        }

    if role_name in {"BRANCH_ADMIN", "DRIVER"}:
        if branch_id is not None and current_user.branch_id != branch_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "BRANCH_ACCESS_DENIED",
                "message": "You do not have access to this branch",
                "data": None,
            }

        return {
            "success": True,
            "company_id": company_id,
            "branch_id": current_user.branch_id,
        }

    return {
        "success": True,
        "company_id": company_id,
        "branch_id": branch_id,
    }


def _check_management_access(current_user):
    role_name = _get_role_name(current_user)

    if role_name not in MANAGEMENT_ROLES:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "MAINTENANCE_MANAGEMENT_ACCESS_DENIED",
            "message": "Only management users can update or delete maintenance records",
            "data": None,
        }

    return None


def _validate_company(
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
            "data": None,
        }

    return None


def _validate_vehicle(
    db: Session,
    company_id: UUID,
    vehicle_id: UUID,
    branch_id: UUID | None = None,
):
    if branch_id is not None:
        vehicle = get_vehicle_by_id_query(
            db=db,
            company_id=company_id,
            branch_id=branch_id,
            vehicle_id=vehicle_id,
        )
    else:
        vehicle = get_vehicle_by_company_id_query(
            db=db,
            company_id=company_id,
            vehicle_id=vehicle_id,
        )

    if not vehicle:
        return (
            None,
            {
                "success": False,
                "status_code": status.HTTP_404_NOT_FOUND,
                "code": "VEHICLE_NOT_FOUND",
                "message": "Vehicle not found, inactive, or does not belong to this company",
                "data": None,
            },
        )

    if branch_id is not None and vehicle.branch_id != branch_id:
        return (
            None,
            {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "VEHICLE_BRANCH_ACCESS_DENIED",
                "message": "Vehicle does not belong to your branch",
                "data": None,
            },
        )

    return vehicle, None


def _validate_maintenance_type(maintenance_type: str):
    if maintenance_type not in VALID_MAINTENANCE_TYPES:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_MAINTENANCE_TYPE",
            "message": "Invalid maintenance type",
            "data": None,
        }

    return None


def _validate_dates(
    service_date: date,
    next_service_date: date | None,
):
    if (
        next_service_date is not None
        and next_service_date < service_date
    ):
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_NEXT_SERVICE_DATE",
            "message": "Next service date cannot be earlier than service date",
            "data": None,
        }

    return None


def _validate_cost(cost: Decimal):
    if cost <= Decimal("0"):
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_MAINTENANCE_COST",
            "message": "Maintenance cost must be greater than zero",
            "data": None,
        }

    return None


def _validate_odometer(odometer_reading: int | None):
    if (
        odometer_reading is not None
        and odometer_reading < 0
    ):
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_ODOMETER_READING",
            "message": "Odometer reading cannot be negative",
            "data": None,
        }

    return None


def create_maintenance_record(
    db: Session,
    company_id: UUID,
    vehicle_id: UUID,
    current_user,
    maintenance_type: str,
    description: str | None,
    garage_name: str | None,
    invoice_number: str | None,
    cost: Decimal,
    service_date: date,
    next_service_date: date | None,
    odometer_reading: int | None,
    remarks: str | None,
):
    scope = _get_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not scope["success"]:
        return scope

    company_error = _validate_company(
        db=db,
        company_id=company_id,
    )

    if company_error:
        return company_error

    role_name = _get_role_name(current_user)

    vehicle, vehicle_error = _validate_vehicle(
    db=db,
    company_id=company_id,
    vehicle_id=vehicle_id,
    branch_id=scope["branch_id"],
)

    if vehicle_error:
        return vehicle_error

    type_error = _validate_maintenance_type(
        maintenance_type,
    )

    if type_error:
        return type_error

    cost_error = _validate_cost(cost)

    if cost_error:
        return cost_error

    date_error = _validate_dates(
        service_date=service_date,
        next_service_date=next_service_date,
    )

    if date_error:
        return date_error

    odometer_error = _validate_odometer(
        odometer_reading,
    )

    if odometer_error:
        return odometer_error

    maintenance = MaintenanceRecord(
        company_id=company_id,
        branch_id=vehicle.branch_id,
        vehicle_id=vehicle_id,
        recorded_by=current_user.id,
        maintenance_type=maintenance_type,
        description=description,
        garage_name=garage_name,
        invoice_number=invoice_number,
        cost=cost,
        service_date=service_date,
        next_service_date=next_service_date,
        odometer_reading=odometer_reading,
        remarks=remarks,
        is_active=True,
    )

    try:
        maintenance = create_record(
            db=db,
            maintenance=maintenance,
        )

        return {
            "success": True,
            "status_code": status.HTTP_201_CREATED,
            "code": "MAINTENANCE_CREATED",
            "message": "Maintenance record created successfully",
            "data": maintenance,
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "MAINTENANCE_CREATION_FAILED",
            "message": "Maintenance record could not be created",
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


def get_maintenance_record(
    db: Session,
    company_id: UUID,
    maintenance_id: UUID,
    current_user,
):
    scope = _get_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not scope["success"]:
        return scope

    company_error = _validate_company(
        db=db,
        company_id=company_id,
    )

    if company_error:
        return company_error

    maintenance = get_by_id(
        db=db,
        maintenance_id=maintenance_id,
        company_id=company_id,
        branch_id=scope["branch_id"],
    )

    if not maintenance:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "MAINTENANCE_NOT_FOUND",
            "message": "Maintenance record not found or inaccessible",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "MAINTENANCE_FOUND",
        "message": "Maintenance record retrieved successfully",
        "data": maintenance,
    }


def get_company_maintenance_records(
    db: Session,
    company_id: UUID,
    current_user,
):
    scope = _get_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not scope["success"]:
        return scope

    company_error = _validate_company(
        db=db,
        company_id=company_id,
    )

    if company_error:
        return company_error

    maintenance_records = get_by_company(
        db=db,
        company_id=company_id,
        branch_id=scope["branch_id"],
    )

    if not maintenance_records:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_MAINTENANCE_RECORDS_FOUND",
            "message": "No maintenance records found for this company",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "MAINTENANCE_RECORDS_FOUND",
        "message": "Company maintenance records retrieved successfully",
        "data": maintenance_records,
    }


def get_vehicle_maintenance_records(
    db: Session,
    company_id: UUID,
    vehicle_id: UUID,
    current_user,
):
    scope = _get_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not scope["success"]:
        return scope

    company_error = _validate_company(
        db=db,
        company_id=company_id,
    )

    if company_error:
        return company_error

    vehicle, vehicle_error = _validate_vehicle(
        db=db,
        company_id=company_id,
        vehicle_id=vehicle_id,
        branch_id=scope["branch_id"],
    )

    if vehicle_error:
        return vehicle_error

    maintenance_records = get_by_vehicle(
        db=db,
        vehicle_id=vehicle_id,
        company_id=company_id,
        branch_id=vehicle.branch_id,
    )

    if not maintenance_records:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_MAINTENANCE_RECORDS_FOUND",
            "message": "No maintenance records found for this vehicle",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "VEHICLE_MAINTENANCE_FOUND",
        "message": "Vehicle maintenance records retrieved successfully",
        "data": maintenance_records,
    }


def get_maintenance_records_by_date_range(
    db: Session,
    company_id: UUID,
    start_date: date,
    end_date: date,
    current_user,
):
    scope = _get_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not scope["success"]:
        return scope

    company_error = _validate_company(
        db=db,
        company_id=company_id,
    )

    if company_error:
        return company_error

    if start_date > end_date:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DATE_RANGE",
            "message": "Start date cannot be later than end date",
            "data": None,
        }

    maintenance_records = get_by_date_range(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
        branch_id=scope["branch_id"],
    )

    if not maintenance_records:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_MAINTENANCE_RECORDS_FOUND",
            "message": "No maintenance records found for the specified date range",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "MAINTENANCE_RECORDS_FOUND",
        "message": "Maintenance records retrieved successfully",
        "data": maintenance_records,
    }


def get_vehicle_maintenance_records_by_date_range(
    db: Session,
    company_id: UUID,
    vehicle_id: UUID,
    start_date: date,
    end_date: date,
    current_user,
):
    scope = _get_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not scope["success"]:
        return scope

    company_error = _validate_company(
        db=db,
        company_id=company_id,
    )

    if company_error:
        return company_error

    vehicle, vehicle_error = _validate_vehicle(
        db=db,
        company_id=company_id,
        vehicle_id=vehicle_id,
        branch_id=scope["branch_id"],
    )

    if vehicle_error:
        return vehicle_error

    if start_date > end_date:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DATE_RANGE",
            "message": "Start date cannot be later than end date",
            "data": None,
        }

    maintenance_records = get_by_vehicle_and_date_range(
        db=db,
        vehicle_id=vehicle_id,
        start_date=start_date,
        end_date=end_date,
        company_id=company_id,
        branch_id=vehicle.branch_id,
    )

    if not maintenance_records:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_MAINTENANCE_RECORDS_FOUND",
            "message": "No maintenance records found for this vehicle in the specified date range",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "VEHICLE_MAINTENANCE_FOUND",
        "message": "Maintenance records retrieved successfully",
        "data": maintenance_records,
    }


def get_maintenance_records_by_type(
    db: Session,
    company_id: UUID,
    maintenance_type: str,
    current_user,
):
    scope = _get_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not scope["success"]:
        return scope

    company_error = _validate_company(
        db=db,
        company_id=company_id,
    )

    if company_error:
        return company_error

    type_error = _validate_maintenance_type(
        maintenance_type,
    )

    if type_error:
        return type_error

    maintenance_records = get_by_maintenance_type(
        db=db,
        company_id=company_id,
        maintenance_type=maintenance_type,
        branch_id=scope["branch_id"],
    )

    if not maintenance_records:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_MAINTENANCE_RECORDS_FOUND",
            "message": "No maintenance records found for the specified maintenance type",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "MAINTENANCE_RECORDS_FOUND",
        "message": "Maintenance records retrieved successfully",
        "data": maintenance_records,
    }


def get_total_maintenance_cost(
    db: Session,
    company_id: UUID,
    current_user,
):
    scope = _get_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not scope["success"]:
        return scope

    company_error = _validate_company(
        db=db,
        company_id=company_id,
    )

    if company_error:
        return company_error

    total_cost = get_total_cost(
        db=db,
        company_id=company_id,
        branch_id=scope["branch_id"],
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "TOTAL_MAINTENANCE_COST",
        "message": "Total maintenance cost calculated successfully",
        "data": total_cost,
    }


def get_vehicle_maintenance_cost(
    db: Session,
    company_id: UUID,
    vehicle_id: UUID,
    current_user,
):
    scope = _get_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not scope["success"]:
        return scope

    company_error = _validate_company(
        db=db,
        company_id=company_id,
    )

    if company_error:
        return company_error

    vehicle, vehicle_error = _validate_vehicle(
        db=db,
        company_id=company_id,
        vehicle_id=vehicle_id,
        branch_id=scope["branch_id"],
    )

    if vehicle_error:
        return vehicle_error

    total_cost = get_vehicle_total_cost(
        db=db,
        vehicle_id=vehicle_id,
        company_id=company_id,
        branch_id=vehicle.branch_id,
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "VEHICLE_MAINTENANCE_COST",
        "message": "Vehicle maintenance cost calculated successfully",
        "data": total_cost,
    }


def get_maintenance_cost_by_date_range(
    db: Session,
    company_id: UUID,
    start_date: date,
    end_date: date,
    current_user,
):
    scope = _get_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not scope["success"]:
        return scope

    company_error = _validate_company(
        db=db,
        company_id=company_id,
    )

    if company_error:
        return company_error

    if start_date > end_date:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DATE_RANGE",
            "message": "Start date cannot be later than end date",
            "data": None,
        }

    total_cost = get_total_cost_by_date_range(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
        branch_id=scope["branch_id"],
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "MAINTENANCE_COST_CALCULATED",
        "message": "Maintenance cost calculated successfully",
        "data": {
            "start_date": start_date,
            "end_date": end_date,
            "total_cost": total_cost,
        },
    }


def get_daily_maintenance_cost(
    db: Session,
    company_id: UUID,
    target_date: date,
    current_user,
):
    return get_maintenance_cost_by_date_range(
        db=db,
        company_id=company_id,
        start_date=target_date,
        end_date=target_date,
        current_user=current_user,
    )


def get_weekly_maintenance_cost(
    db: Session,
    company_id: UUID,
    end_date: date,
    current_user,
):
    start_date = end_date - timedelta(days=6)

    return get_maintenance_cost_by_date_range(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
        current_user=current_user,
    )


def get_monthly_maintenance_cost(
    db: Session,
    company_id: UUID,
    end_date: date,
    current_user,
):
    start_date = end_date - timedelta(days=29)

    return get_maintenance_cost_by_date_range(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
        current_user=current_user,
    )


def get_vehicle_maintenance_cost_by_date_range(
    db: Session,
    company_id: UUID,
    vehicle_id: UUID,
    start_date: date,
    end_date: date,
    current_user,
):
    scope = _get_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not scope["success"]:
        return scope

    company_error = _validate_company(
        db=db,
        company_id=company_id,
    )

    if company_error:
        return company_error

    vehicle, vehicle_error = _validate_vehicle(
        db=db,
        company_id=company_id,
        vehicle_id=vehicle_id,
        branch_id=scope["branch_id"],
    )

    if vehicle_error:
        return vehicle_error

    if start_date > end_date:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DATE_RANGE",
            "message": "Start date cannot be later than end date",
            "data": None,
        }

    total_cost = get_vehicle_total_cost_by_date_range(
        db=db,
        vehicle_id=vehicle_id,
        start_date=start_date,
        end_date=end_date,
        company_id=company_id,
        branch_id=vehicle.branch_id,
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "VEHICLE_MAINTENANCE_COST",
        "message": "Vehicle maintenance cost calculated successfully",
        "data": {
            "vehicle_id": vehicle_id,
            "start_date": start_date,
            "end_date": end_date,
            "total_cost": total_cost,
        },
    }


def update_maintenance_record(
    db: Session,
    company_id: UUID,
    maintenance_id: UUID,
    current_user,
    maintenance_type: str | None = None,
    description: str | None = None,
    garage_name: str | None = None,
    invoice_number: str | None = None,
    cost: Decimal | None = None,
    service_date: date | None = None,
    next_service_date: date | None = None,
    odometer_reading: int | None = None,
    remarks: str | None = None,
):
    management_error = _check_management_access(
        current_user,
    )

    if management_error:
        return management_error

    scope = _get_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not scope["success"]:
        return scope

    company_error = _validate_company(
        db=db,
        company_id=company_id,
    )

    if company_error:
        return company_error

    maintenance = get_by_id(
        db=db,
        maintenance_id=maintenance_id,
        company_id=company_id,
        branch_id=scope["branch_id"],
    )

    if not maintenance:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "MAINTENANCE_NOT_FOUND",
            "message": "Maintenance record not found or inaccessible",
            "data": None,
        }

    if maintenance_type is not None:
        type_error = _validate_maintenance_type(
            maintenance_type,
        )

        if type_error:
            return type_error

    if cost is not None:
        cost_error = _validate_cost(cost)

        if cost_error:
            return cost_error

    effective_service_date = (
        service_date
        if service_date is not None
        else maintenance.service_date
    )

    effective_next_service_date = (
        next_service_date
        if next_service_date is not None
        else maintenance.next_service_date
    )

    date_error = _validate_dates(
        service_date=effective_service_date,
        next_service_date=effective_next_service_date,
    )

    if date_error:
        return date_error

    odometer_error = _validate_odometer(
        odometer_reading,
    )

    if odometer_error:
        return odometer_error

    if maintenance_type is not None:
        maintenance.maintenance_type = maintenance_type

    if description is not None:
        maintenance.description = description

    if garage_name is not None:
        maintenance.garage_name = garage_name

    if invoice_number is not None:
        maintenance.invoice_number = invoice_number

    if cost is not None:
        maintenance.cost = cost

    if service_date is not None:
        maintenance.service_date = service_date

    if next_service_date is not None:
        maintenance.next_service_date = next_service_date

    if odometer_reading is not None:
        maintenance.odometer_reading = odometer_reading

    if remarks is not None:
        maintenance.remarks = remarks

    try:
        maintenance = update_record(
            db=db,
            maintenance=maintenance,
        )

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "MAINTENANCE_UPDATED",
            "message": "Maintenance record updated successfully",
            "data": maintenance,
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "MAINTENANCE_UPDATE_FAILED",
            "message": "Maintenance record could not be updated",
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


def delete_maintenance_record(
    db: Session,
    company_id: UUID,
    maintenance_id: UUID,
    current_user,
):
    management_error = _check_management_access(
        current_user,
    )

    if management_error:
        return management_error

    scope = _get_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not scope["success"]:
        return scope

    company_error = _validate_company(
        db=db,
        company_id=company_id,
    )

    if company_error:
        return company_error

    maintenance = get_by_id(
        db=db,
        maintenance_id=maintenance_id,
        company_id=company_id,
        branch_id=scope["branch_id"],
    )

    if not maintenance:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "MAINTENANCE_NOT_FOUND",
            "message": "Maintenance record not found or inaccessible",
            "data": None,
        }

    try:
        maintenance = soft_delete_record(
            db=db,
            maintenance=maintenance,
        )

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "MAINTENANCE_DELETED",
            "message": "Maintenance record deleted successfully",
            "data": None,
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "MAINTENANCE_DELETE_FAILED",
            "message": "Maintenance record could not be deleted",
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


def get_upcoming_maintenance(
    db: Session,
    company_id: UUID,
    target_date: date,
    current_user,
):
    scope = _get_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not scope["success"]:
        return scope

    company_error = _validate_company(
        db=db,
        company_id=company_id,
    )

    if company_error:
        return company_error

    maintenance_records = get_upcoming_by_date(
        db=db,
        company_id=company_id,
        target_date=target_date,
        branch_id=scope["branch_id"],
    )

    if not maintenance_records:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_UPCOMING_MAINTENANCE",
            "message": "No upcoming maintenance found",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "UPCOMING_MAINTENANCE_FOUND",
        "message": "Upcoming maintenance records retrieved successfully",
        "data": maintenance_records,
    }


def get_due_maintenance(
    db: Session,
    company_id: UUID,
    target_date: date,
    current_user,
):
    scope = _get_scope(
        current_user=current_user,
        company_id=company_id,
    )

    if not scope["success"]:
        return scope

    company_error = _validate_company(
        db=db,
        company_id=company_id,
    )

    if company_error:
        return company_error

    maintenance_records = get_by_due_date(
        db=db,
        company_id=company_id,
        target_date=target_date,
        branch_id=scope["branch_id"],
    )

    if not maintenance_records:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_DUE_MAINTENANCE",
            "message": "No due maintenance records found",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DUE_MAINTENANCE_FOUND",
        "message": "Due maintenance records retrieved successfully",
        "data": maintenance_records,
    }