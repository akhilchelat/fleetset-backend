from datetime import datetime, timezone
from uuid import UUID

from fastapi import status
from sqlalchemy.orm import Session

from app.models.drivervehicleassignment import DriverVehicleAssignment
from app.models.user import User

from app.reusable_functions.company_reusable import (
    get_company_by_id_query,
)

from app.reusable_functions.branch_reusable import (
    get_branch_by_company_query,
)

from app.reusable_functions.driver_reusable import (
    get_driver_by_id_query,
)

from app.reusable_functions.vehicle_reusable import (
    get_vehicle_by_id_query, get_vehicle_by_company_id_query,
)

from app.reusable_functions.drivervehicleassignment_reusable import (
    get_active_assignment_by_driver_id_query,
    get_active_assignment_by_vehicle_id_query,
    create_assignment_query,
    get_assignment_by_id_query,
    update_assignment_query,
    get_company_assignments_query,
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
    company_id: UUID,
) -> bool:
    role_name = _get_role_name(current_user)

    if role_name == GLOBAL_ADMIN:
        return True

    return current_user.company_id == company_id


def _get_scope_branch_id(
    current_user: User,
) -> UUID | None:
    role_name = _get_role_name(current_user)

    if role_name in (BRANCH_ADMIN, DRIVER):
        return current_user.branch_id

    return None


def _can_manage_assignments(
    current_user: User,
) -> bool:
    role_name = _get_role_name(current_user)

    return role_name in (
        GLOBAL_ADMIN,
        SUPER_ADMIN,
        BRANCH_ADMIN,
    )


def assign_driver_to_vehicle_service(
    db: Session,
    company_id: UUID,
    driver_id: UUID,
    vehicle_id: UUID,
    current_user: User,
):
    if not _can_manage_assignments(current_user):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "ASSIGNMENT_ACCESS_DENIED",
            "message": "You do not have permission to assign vehicles",
            "data": None,
        }

    if not _can_access_company(current_user, company_id):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_ACCESS_DENIED",
            "message": "You do not have access to this company",
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

    driver = get_driver_by_id_query(
        db,
        company_id,
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

    if not driver.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "DRIVER_INACTIVE",
            "message": "Driver is inactive",
            "data": None,
        }

    scope_branch_id = _get_scope_branch_id(current_user)
    if scope_branch_id is not None:
        vehicle = get_vehicle_by_id_query(
            db,
            company_id,
            scope_branch_id,
            vehicle_id,
    )
    else:
        vehicle = get_vehicle_by_company_id_query(
            db,
            company_id,
            vehicle_id,)

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
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "VEHICLE_INACTIVE",
            "message": "Vehicle is inactive",
            "data": None,
        }

    if not driver.branch_id:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "DRIVER_BRANCH_REQUIRED",
            "message": "Driver is not assigned to a branch",
            "data": None,
        }

    if not vehicle.branch_id:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "VEHICLE_BRANCH_REQUIRED",
            "message": "Vehicle is not assigned to a branch",
            "data": None,
        }

    if driver.branch_id != vehicle.branch_id:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "BRANCH_MISMATCH",
            "message": "Driver and vehicle must belong to the same branch",
            "data": None,
        }

    branch_id = driver.branch_id

    scope_branch_id = _get_scope_branch_id(
        current_user,
    )

    if scope_branch_id is not None and scope_branch_id != branch_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "BRANCH_ACCESS_DENIED",
            "message": "You do not have access to this branch",
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
            "message": "Branch not found",
            "data": None,
        }

    active_driver_assignment = get_active_assignment_by_driver_id_query(
        db,
        driver_id,
        company_id=company_id,
        branch_id=branch_id,
    )

    if active_driver_assignment:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "DRIVER_ALREADY_ASSIGNED",
            "message": "Driver is already assigned to another vehicle",
            "data": None,
        }

    active_vehicle_assignment = get_active_assignment_by_vehicle_id_query(
        db,
        vehicle_id,
        company_id=company_id,
        branch_id=branch_id,
    )

    if active_vehicle_assignment:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "VEHICLE_ALREADY_ASSIGNED",
            "message": "Vehicle is already assigned to another driver",
            "data": None,
        }

    assignment = DriverVehicleAssignment(
        company_id=company_id,
        branch_id=branch_id,
        driver_id=driver_id,
        vehicle_id=vehicle_id,
        assigned_by=current_user.id,
    )

    assignment = create_assignment_query(
        db,
        assignment,
    )

    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "code": "ASSIGNMENT_CREATED",
        "message": "Driver assigned successfully",
        "data": assignment,
    }


def unassign_driver_from_vehicle_service(
    db: Session,
    company_id: UUID,
    assignment_id: UUID,
    current_user: User,
):
    if not _can_manage_assignments(current_user):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "ASSIGNMENT_ACCESS_DENIED",
            "message": "You do not have permission to unassign vehicles",
            "data": None,
        }

    if not _can_access_company(current_user, company_id):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_ACCESS_DENIED",
            "message": "You do not have access to this company",
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

    scope_branch_id = _get_scope_branch_id(
        current_user,
    )

    assignment = get_assignment_by_id_query(
        db,
        assignment_id,
        company_id=company_id,
        branch_id=scope_branch_id,
    )

    if not assignment:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "ASSIGNMENT_NOT_FOUND",
            "message": "Assignment not found",
            "data": None,
        }

    if not assignment.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "ASSIGNMENT_ALREADY_INACTIVE",
            "message": "Assignment is already inactive",
            "data": None,
        }

    assignment.is_active = False
    assignment.unassigned_at = datetime.now(timezone.utc)

    assignment = update_assignment_query(
        db,
        assignment,
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "ASSIGNMENT_UNASSIGNED",
        "message": "Driver unassigned successfully",
        "data": assignment,
    }


def transfer_driver_to_vehicle_service(
    db: Session,
    company_id: UUID,
    driver_id: UUID,
    new_vehicle_id: UUID,
    current_user: User,
):
    if not _can_manage_assignments(current_user):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "ASSIGNMENT_ACCESS_DENIED",
            "message": "You do not have permission to transfer vehicle assignments",
            "data": None,
        }

    if not _can_access_company(current_user, company_id):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_ACCESS_DENIED",
            "message": "You do not have access to this company",
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

    driver = get_driver_by_id_query(
        db,
        company_id,
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

    if not driver.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "DRIVER_INACTIVE",
            "message": "Driver is inactive",
            "data": None,
        }

    new_vehicle = get_vehicle_by_id_query(
        db,
        company_id,
        new_vehicle_id,
    )

    if not new_vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found",
            "data": None,
        }

    if not new_vehicle.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "VEHICLE_INACTIVE",
            "message": "Vehicle is inactive",
            "data": None,
        }

    if not driver.branch_id:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "DRIVER_BRANCH_REQUIRED",
            "message": "Driver is not assigned to a branch",
            "data": None,
        }

    if not new_vehicle.branch_id:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "VEHICLE_BRANCH_REQUIRED",
            "message": "Vehicle is not assigned to a branch",
            "data": None,
        }

    if driver.branch_id != new_vehicle.branch_id:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "BRANCH_MISMATCH",
            "message": "Driver and vehicle must belong to the same branch",
            "data": None,
        }

    branch_id = driver.branch_id

    scope_branch_id = _get_scope_branch_id(
        current_user,
    )

    if scope_branch_id is not None and scope_branch_id != branch_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "BRANCH_ACCESS_DENIED",
            "message": "You do not have access to this branch",
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
            "message": "Branch not found",
            "data": None,
        }

    current_assignment = get_active_assignment_by_driver_id_query(
        db,
        driver_id,
        company_id=company_id,
        branch_id=branch_id,
    )

    if not current_assignment:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "ACTIVE_ASSIGNMENT_NOT_FOUND",
            "message": "Driver has no active assignment",
            "data": None,
        }

    if current_assignment.vehicle_id == new_vehicle_id:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "SAME_VEHICLE",
            "message": "Driver is already assigned to this vehicle",
            "data": None,
        }

    active_vehicle_assignment = get_active_assignment_by_vehicle_id_query(
        db,
        new_vehicle_id,
        company_id=company_id,
        branch_id=branch_id,
    )

    if active_vehicle_assignment:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "VEHICLE_ALREADY_ASSIGNED",
            "message": "Vehicle is already assigned to another driver",
            "data": None,
        }

    current_assignment.is_active = False
    current_assignment.unassigned_at = datetime.now(timezone.utc)

    update_assignment_query(
        db,
        current_assignment,
    )

    new_assignment = DriverVehicleAssignment(
        company_id=company_id,
        branch_id=branch_id,
        driver_id=driver_id,
        vehicle_id=new_vehicle_id,
        assigned_by=current_user.id,
    )

    new_assignment = create_assignment_query(
        db,
        new_assignment,
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "ASSIGNMENT_TRANSFERRED",
        "message": "Driver transferred successfully",
        "data": new_assignment,
    }


def get_assignment_service(
    db: Session,
    company_id: UUID,
    assignment_id: UUID,
    current_user: User,
):
    if not _can_access_company(current_user, company_id):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_ACCESS_DENIED",
            "message": "You do not have access to this company",
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

    scope_branch_id = _get_scope_branch_id(
        current_user,
    )

    assignment = get_assignment_by_id_query(
        db,
        assignment_id,
        company_id=company_id,
        branch_id=scope_branch_id,
    )

    if not assignment:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "ASSIGNMENT_NOT_FOUND",
            "message": "Assignment not found",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "ASSIGNMENT_RETRIEVED",
        "message": "Assignment retrieved successfully",
        "data": assignment,
    }


def get_company_assignments_service(
    db: Session,
    company_id: UUID,
    current_user: User,
):
    if not _can_access_company(current_user, company_id):
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_ACCESS_DENIED",
            "message": "You do not have access to this company",
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
            "data": [],
        }

    scope_branch_id = _get_scope_branch_id(
        current_user,
    )

    assignments = get_company_assignments_query(
        db,
        company_id,
        branch_id=scope_branch_id,
    )

    active_assignments = [
        assignment
        for assignment in assignments
        if assignment.is_active
    ]

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "ASSIGNMENTS_RETRIEVED",
        "message": "Company assignments retrieved successfully",
        "data": active_assignments,
    }