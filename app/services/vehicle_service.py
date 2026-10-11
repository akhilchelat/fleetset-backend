from datetime import date
from uuid import UUID

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.vehicle import Vehicle, VehicleStatus

from app.reusable_functions.branch_reusable import (
    get_branch_by_company_query,
)
from app.reusable_functions.company_reusable import (
    get_company_by_id_query,
)
from app.reusable_functions.vehicle_reusable import (
    get_vehicle_by_registration_number_query,
    get_vehicle_by_registration_number_admin_query,
    get_vehicle_by_id_query,
    get_active_vehicle_by_id_admin_query,
    get_vehicle_by_id_admin_query,
    get_all_vehicles_admin_query,
    get_company_vehicles_by_ids_query,
    get_all_active_vehicles_query,
    get_all_inactive_vehicles_query,
    get_vehicle_by_company_id_query,
    get_inactive_vehicle_by_id_query,
)


GLOBAL_ADMIN = "GLOBAL_ADMIN"
SUPER_ADMIN = "SUPER_ADMIN"
BRANCH_ADMIN = "BRANCH_ADMIN"
DRIVER = "DRIVER"


def _get_role_name(current_user: User) -> str | None:
    if not current_user.role:
        return None

    return current_user.role.name


def _can_access_company(
    current_user: User,
    company_id: UUID
) -> bool:

    role = _get_role_name(current_user)

    if role == GLOBAL_ADMIN:
        return True

    return current_user.company_id == company_id


def _get_branch_scope(
    current_user: User,
    company_id: UUID
) -> UUID | None:

    role = _get_role_name(current_user)

    if role == GLOBAL_ADMIN:
        return None

    if current_user.company_id != company_id:
        return None

    if role in {BRANCH_ADMIN, DRIVER}:
        return current_user.branch_id

    return None


def _can_access_branch(
    current_user: User,
    company_id: UUID,
    branch_id: UUID
) -> bool:

    role = _get_role_name(current_user)

    if role == GLOBAL_ADMIN:
        return True

    if current_user.company_id != company_id:
        return False

    if role == SUPER_ADMIN:
        return True

    if role in {BRANCH_ADMIN, DRIVER}:
        return current_user.branch_id == branch_id

    return False


def _validate_vehicle_status(
    vehicle_status: str | None
) -> bool:

    if vehicle_status is None:
        return True

    return vehicle_status in {
        VehicleStatus.ACTIVE,
        VehicleStatus.IN_MAINTENANCE,
        VehicleStatus.OUT_OF_SERVICE,
    }


def create_vehicle(
    db: Session,
    current_user: User,
    company_id: UUID,
    branch_id: UUID,
    registration_number: str,
    manufacturer: str | None,
    model: str | None,
    vehicle_type: str | None,
    year: int | None,
    purchase_date: date | None,
    current_odometer: int | None,
):
    if not _can_access_company(current_user, company_id):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_ACCESS_DENIED",
            "message": "You do not have access to this company",
            "data": None,
        }

    role = _get_role_name(current_user)

    if role not in {
        GLOBAL_ADMIN,
        SUPER_ADMIN,
        BRANCH_ADMIN,
    }:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "VEHICLE_CREATE_FORBIDDEN",
            "message": "You do not have permission to create vehicles",
            "data": None,
        }

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
            "data": None,
        }

    branch = get_branch_by_company_query(
        db,
        branch_id,
        company_id
    )

    if not branch:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "BRANCH_NOT_FOUND",
            "message": "Branch not found",
            "data": None,
        }

    if not _can_access_branch(
        current_user,
        company_id,
        branch_id
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "BRANCH_ACCESS_DENIED",
            "message": "You do not have access to this branch",
            "data": None,
        }

    vehicle = get_vehicle_by_registration_number_admin_query(
        db,
        registration_number
    )

    if vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "VEHICLE_ALREADY_EXISTS",
            "message": "Vehicle with this registration number already exists",
            "data": None,
        }

    new_vehicle = Vehicle(
        company_id=company.id,
        branch_id=branch.id,
        registration_number=registration_number,
        manufacturer=manufacturer,
        model=model,
        vehicle_type=vehicle_type,
        year=year,
        purchase_date=purchase_date,
        current_odometer=(
            current_odometer
            if current_odometer is not None
            else 0
        ),
    )

    db.add(new_vehicle)

    try:
        db.commit()
        db.refresh(new_vehicle)

        return {
            "success": True,
            "status_code": status.HTTP_201_CREATED,
            "code": "VEHICLE_CREATED",
            "message": "Vehicle created successfully",
            "data": new_vehicle,
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "VEHICLE_ALREADY_EXISTS",
            "message": "Vehicle with this registration number already exists",
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


def find_vehicle_by_id(
    db: Session,
    current_user: User,
    company_id: UUID,
    vehicle_id: UUID
):
    if not _can_access_company(
        current_user,
        company_id
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_ACCESS_DENIED",
            "message": "You do not have access to this company",
            "data": None,
        }

    branch_id = _get_branch_scope(
        current_user,
        company_id
    )

    if branch_id is not None:
        vehicle = get_vehicle_by_id_query(
            db,
            company_id,
            branch_id,
            vehicle_id
        )
    else:
        vehicle = get_vehicle_by_company_id_query(
            db,
            company_id,
            vehicle_id
        )

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "VEHICLE_FOUND",
        "message": "Vehicle retrieved successfully",
        "data": vehicle,
    }


def find_active_vehicle_by_id(
    db: Session,
    vehicle_id: UUID
):
    vehicle = get_active_vehicle_by_id_admin_query(
        db,
        vehicle_id
    )

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "VEHICLE_FOUND",
        "message": "Vehicle retrieved successfully",
        "data": vehicle,
    }


def find_vehicle_by_registration_number(
    db: Session,
    current_user: User,
    company_id: UUID,
    registration_number: str
):
    if not _can_access_company(
        current_user,
        company_id
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_ACCESS_DENIED",
            "message": "You do not have access to this company",
            "data": None,
        }

    branch_id = _get_branch_scope(
        current_user,
        company_id
    )

    if branch_id is not None:
        vehicle = get_vehicle_by_registration_number_query(
            db,
            company_id,
            branch_id,
            registration_number
        )
    else:
        vehicle = get_vehicle_by_registration_number_admin_query(
            db,
            registration_number
        )

        if vehicle and vehicle.company_id != company_id:
            vehicle = None

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "VEHICLE_FOUND",
        "message": "Vehicle retrieved successfully",
        "data": vehicle,
    }


def find_vehicle_by_registration_number_admin(
    db: Session,
    registration_number: str
):
    vehicle = get_vehicle_by_registration_number_admin_query(
        db,
        registration_number
    )

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "VEHICLE_FOUND",
        "message": "Vehicle retrieved successfully",
        "data": vehicle,
    }


def get_all_active_vehicles(
    db: Session,
    current_user: User,
    company_id: UUID
):
    if not _can_access_company(
        current_user,
        company_id
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_ACCESS_DENIED",
            "message": "You do not have access to this company",
            "data": None,
        }

    branch_id = _get_branch_scope(
        current_user,
        company_id
    )

    vehicles = get_all_active_vehicles_query(
        db,
        company_id,
        branch_id
    )

    if not vehicles:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_VEHICLES_FOUND",
            "message": "No active vehicles found",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "VEHICLES_RETRIEVED",
        "message": "Active vehicles retrieved successfully",
        "data": vehicles,
    }


def get_all_inactive_vehicles(
    db: Session,
    current_user: User,
    company_id: UUID
):
    if not _can_access_company(
        current_user,
        company_id
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_ACCESS_DENIED",
            "message": "You do not have access to this company",
            "data": None,
        }

    branch_id = _get_branch_scope(
        current_user,
        company_id
    )

    vehicles = get_all_inactive_vehicles_query(
        db,
        company_id,
        branch_id
    )

    if not vehicles:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_VEHICLES_FOUND",
            "message": "No inactive vehicles found",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "VEHICLES_RETRIEVED",
        "message": "Inactive vehicles retrieved successfully",
        "data": vehicles,
    }


def get_all_vehicles_admin(
    db: Session
):
    vehicles = get_all_vehicles_admin_query(
        db
    )

    if not vehicles:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_VEHICLES_FOUND",
            "message": "No vehicles found",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "VEHICLES_RETRIEVED",
        "message": "Vehicles retrieved successfully",
        "data": vehicles,
    }


def update_vehicle(
    db: Session,
    current_user: User,
    company_id: UUID,
    vehicle_id: UUID,
    registration_number: str | None = None,
    manufacturer: str | None = None,
    model: str | None = None,
    vehicle_type: str | None = None,
    year: int | None = None,
    purchase_date: date | None = None,
    vehicle_status: str | None = None,
    current_odometer: int | None = None,
):
    role = _get_role_name(current_user)

    if role not in {
        GLOBAL_ADMIN,
        SUPER_ADMIN,
        BRANCH_ADMIN,
    }:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "VEHICLE_UPDATE_FORBIDDEN",
            "message": "You do not have permission to update vehicles",
            "data": None,
        }

    if not _can_access_company(
        current_user,
        company_id
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_ACCESS_DENIED",
            "message": "You do not have access to this company",
            "data": None,
        }

    branch_id = _get_branch_scope(
        current_user,
        company_id
    )

    if branch_id is not None:
        vehicle = get_vehicle_by_id_query(
            db,
            company_id,
            branch_id,
            vehicle_id
        )
    else:
        vehicle = get_vehicle_by_company_id_query(
            db,
            company_id,
            vehicle_id
        )

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found",
            "data": None,
        }

    if not _validate_vehicle_status(vehicle_status):
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_VEHICLE_STATUS",
            "message": "Invalid vehicle status",
            "data": None,
        }

    if registration_number is not None:
        existing_vehicle = get_vehicle_by_registration_number_admin_query(
            db,
            registration_number
        )

        if (
            existing_vehicle
            and existing_vehicle.id != vehicle.id
        ):
            return {
                "success": False,
                "status_code": status.HTTP_409_CONFLICT,
                "code": "REGISTRATION_NUMBER_ALREADY_EXISTS",
                "message": "Registration number already exists",
                "data": None,
            }

        vehicle.registration_number = registration_number

    if manufacturer is not None:
        vehicle.manufacturer = manufacturer

    if model is not None:
        vehicle.model = model

    if vehicle_type is not None:
        vehicle.vehicle_type = vehicle_type

    if year is not None:
        vehicle.year = year

    if purchase_date is not None:
        vehicle.purchase_date = purchase_date

    if vehicle_status is not None:
        vehicle.status = vehicle_status

    if current_odometer is not None:
        vehicle.current_odometer = current_odometer

    try:
        db.commit()
        db.refresh(vehicle)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "VEHICLE_UPDATED",
            "message": "Vehicle updated successfully",
            "data": vehicle,
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "REGISTRATION_NUMBER_ALREADY_EXISTS",
            "message": "Registration number already exists",
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


def activate_vehicle(
    db: Session,
    current_user: User,
    company_id: UUID,
    vehicle_id: UUID
):
    role = _get_role_name(current_user)

    if role not in {
        GLOBAL_ADMIN,
        SUPER_ADMIN,
        BRANCH_ADMIN,
    }:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "VEHICLE_ACTIVATE_FORBIDDEN",
            "message": "You do not have permission to activate vehicles",
            "data": None,
        }

    if not _can_access_company(
        current_user,
        company_id
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_ACCESS_DENIED",
            "message": "You do not have access to this company",
            "data": None,
        }

    branch_id = _get_branch_scope(
        current_user,
        company_id
    )

    if branch_id is not None:
        vehicle = get_inactive_vehicle_by_id_query(
            db,
            company_id,
            branch_id,
            vehicle_id
    )
    else:
        vehicle = get_vehicle_by_id_admin_query(
            db,
            vehicle_id
    )

    if vehicle and vehicle.company_id != company_id:
        vehicle = None

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found",
            "data": None,
        }

    if vehicle.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "VEHICLE_ALREADY_ACTIVE",
            "message": "Vehicle already active",
            "data": None,
        }

    vehicle.is_active = True

    try:
        db.commit()
        db.refresh(vehicle)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "VEHICLE_ACTIVATED",
            "message": "Vehicle activated successfully",
            "data": vehicle,
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


def deactivate_vehicle(
    db: Session,
    current_user: User,
    company_id: UUID,
    vehicle_id: UUID
):
    role = _get_role_name(current_user)

    if role not in {
        GLOBAL_ADMIN,
        SUPER_ADMIN,
        BRANCH_ADMIN,
    }:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "VEHICLE_DEACTIVATE_FORBIDDEN",
            "message": "You do not have permission to deactivate vehicles",
            "data": None,
        }

    if not _can_access_company(
        current_user,
        company_id
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_ACCESS_DENIED",
            "message": "You do not have access to this company",
            "data": None,
        }

    branch_id = _get_branch_scope(
        current_user,
        company_id
    )

    if branch_id is not None:
        vehicle = get_vehicle_by_id_admin_query(
            db,
            vehicle_id
        )

        if (
            not vehicle
            or vehicle.company_id != company_id
            or vehicle.branch_id != branch_id
        ):
            vehicle = None
    else:
        vehicle = get_vehicle_by_id_admin_query(
            db,
            vehicle_id
        )

        if vehicle and vehicle.company_id != company_id:
            vehicle = None

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found",
            "data": None,
        }

    if not vehicle.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "VEHICLE_ALREADY_INACTIVE",
            "message": "Vehicle already inactive",
            "data": None,
        }

    vehicle.is_active = False

    try:
        db.commit()
        db.refresh(vehicle)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "VEHICLE_DEACTIVATED",
            "message": "Vehicle deactivated successfully",
            "data": vehicle,
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


def bulk_activate_vehicles(
    db: Session,
    current_user: User,
    company_id: UUID,
    vehicle_ids: list[UUID]
):
    role = _get_role_name(current_user)

    if role not in {
        GLOBAL_ADMIN,
        SUPER_ADMIN,
        BRANCH_ADMIN,
    }:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "VEHICLE_BULK_ACTIVATE_FORBIDDEN",
            "message": "You do not have permission to activate vehicles",
            "data": None,
        }

    if not _can_access_company(
        current_user,
        company_id
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_ACCESS_DENIED",
            "message": "You do not have access to this company",
            "data": None,
        }

    branch_id = _get_branch_scope(
        current_user,
        company_id
    )

    vehicles = get_company_vehicles_by_ids_query(
        db,
        company_id,
        vehicle_ids,
        branch_id
    )

    if not vehicles:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_VEHICLES_FOUND",
            "message": "No vehicles found",
            "data": None,
        }

    already_active_vehicles = []
    activated_vehicles = []

    for vehicle in vehicles:
        item = {
            "id": vehicle.id,
            "registration_number": vehicle.registration_number,
        }

        if vehicle.is_active:
            already_active_vehicles.append(item)
            continue

        vehicle.is_active = True
        activated_vehicles.append(item)

    if len(already_active_vehicles) == len(vehicles):
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "ALL_VEHICLES_ALREADY_ACTIVE",
            "message": "All vehicles are already active",
            "data": {
                "vehicles": already_active_vehicles
            },
        }

    try:
        db.commit()

        for vehicle in vehicles:
            db.refresh(vehicle)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "VEHICLES_ACTIVATED",
            "message": "Vehicles activated successfully",
            "data": {
                "activated_vehicles": activated_vehicles,
                "already_active_vehicles": already_active_vehicles,
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


def bulk_deactivate_vehicles(
    db: Session,
    current_user: User,
    company_id: UUID,
    vehicle_ids: list[UUID]
):
    role = _get_role_name(current_user)

    if role not in {
        GLOBAL_ADMIN,
        SUPER_ADMIN,
        BRANCH_ADMIN,
    }:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "VEHICLE_BULK_DEACTIVATE_FORBIDDEN",
            "message": "You do not have permission to deactivate vehicles",
            "data": None,
        }

    if not _can_access_company(
        current_user,
        company_id
    ):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_ACCESS_DENIED",
            "message": "You do not have access to this company",
            "data": None,
        }

    branch_id = _get_branch_scope(
        current_user,
        company_id
    )

    vehicles = get_company_vehicles_by_ids_query(
        db,
        company_id,
        vehicle_ids,
        branch_id
    )

    if not vehicles:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_VEHICLES_FOUND",
            "message": "No vehicles found",
            "data": None,
        }

    already_inactive_vehicles = []
    deactivated_vehicles = []

    for vehicle in vehicles:
        item = {
            "id": vehicle.id,
            "registration_number": vehicle.registration_number,
        }

        if not vehicle.is_active:
            already_inactive_vehicles.append(item)
            continue

        vehicle.is_active = False
        deactivated_vehicles.append(item)

    if len(already_inactive_vehicles) == len(vehicles):
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "ALL_VEHICLES_ALREADY_INACTIVE",
            "message": "All vehicles are already inactive",
            "data": {
                "vehicles": already_inactive_vehicles
            },
        }

    try:
        db.commit()

        for vehicle in vehicles:
            db.refresh(vehicle)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "VEHICLES_DEACTIVATED",
            "message": "Vehicles deactivated successfully",
            "data": {
                "deactivated_vehicles": deactivated_vehicles,
                "already_inactive_vehicles": already_inactive_vehicles,
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