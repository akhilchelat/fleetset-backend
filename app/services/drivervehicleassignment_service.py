from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.drivervehicleassignment import DriverVehicleAssignment

from app.reusable_functions.company_reusable import (
    get_company_by_id_query
)

from app.reusable_functions.driver_reusable import (
    get_driver_by_id_query
)

from app.reusable_functions.vehicle_reusable import (
    get_vehicle_by_id_query
)

from app.reusable_functions.drivervehicleassignment_reusable import (
    get_active_assignment_by_driver_id_query,
    get_active_assignment_by_vehicle_id_query,
    create_assignment_query,
    get_assignment_by_id_query,
    update_assignment_query,
)


def assign_driver_to_vehicle_service(
    db: Session,
    company_id: UUID,
    driver_id: UUID,
    vehicle_id: UUID,
    assigned_by: UUID
):
    company = get_company_by_id_query(
        db,
        company_id
    )

    if not company:
        return {
            "success": False,
            "message": "Company not found."
        }

    # Company-scoped driver lookup
    driver = get_driver_by_id_query(
        db,
        company_id,
        driver_id
    )

    if not driver:
        return {
            "success": False,
            "message": "Driver not found."
        }

    if driver.company_id != company_id:
        return {
            "success": False,
            "message": "Driver does not belong to this company."
        }

    if not driver.is_active:
        return {
            "success": False,
            "message": "Driver is inactive."
        }

    # Company-scoped vehicle lookup
    vehicle = get_vehicle_by_id_query(
        db,
        company_id,
        vehicle_id
    )

    if not vehicle:
        return {
            "success": False,
            "message": "Vehicle not found."
        }

    if vehicle.company_id != company_id:
        return {
            "success": False,
            "message": "Vehicle does not belong to this company."
        }

    if not vehicle.is_active:
        return {
            "success": False,
            "message": "Vehicle is inactive."
        }

    # Make sure driver is not already assigned
    active_driver_assignment = get_active_assignment_by_driver_id_query(
        db,
        driver_id
    )

    if active_driver_assignment:
        return {
            "success": False,
            "message": "Driver is already assigned to another vehicle."
        }

    # Make sure vehicle is not already assigned
    active_vehicle_assignment = get_active_assignment_by_vehicle_id_query(
        db,
        vehicle_id
    )

    if active_vehicle_assignment:
        return {
            "success": False,
            "message": "Vehicle is already assigned to another driver."
        }

    assignment = DriverVehicleAssignment(
        company_id=company_id,
        driver_id=driver_id,
        vehicle_id=vehicle_id,
        assigned_by=assigned_by
    )

    assignment = create_assignment_query(
        db,
        assignment
    )

    return {
        "success": True,
        "message": "Driver assigned successfully.",
        "assignment": assignment
    }


def unassign_driver_from_vehicle_service(
    db: Session,
    company_id: UUID,
    assignment_id: UUID
):
    company = get_company_by_id_query(
        db,
        company_id
    )

    if not company:
        return {
            "success": False,
            "message": "Company not found."
        }

    assignment = get_assignment_by_id_query(
        db,
        assignment_id
    )

    if not assignment:
        return {
            "success": False,
            "message": "Assignment not found."
        }

    if assignment.company_id != company_id:
        return {
            "success": False,
            "message": "Assignment does not belong to this company."
        }

    if not assignment.is_active:
        return {
            "success": False,
            "message": "Assignment is already inactive."
        }

    assignment.is_active = False
    assignment.unassigned_at = datetime.now(timezone.utc)

    assignment = update_assignment_query(
        db,
        assignment
    )

    return {
        "success": True,
        "message": "Driver unassigned successfully.",
        "assignment": assignment
    }


def transfer_driver_to_vehicle_service(
    db: Session,
    company_id: UUID,
    driver_id: UUID,
    new_vehicle_id: UUID,
    assigned_by: UUID
):
    company = get_company_by_id_query(
        db,
        company_id
    )

    if not company:
        return {
            "success": False,
            "message": "Company not found."
        }

    # Company-scoped driver lookup
    driver = get_driver_by_id_query(
        db,
        company_id,
        driver_id
    )

    if not driver:
        return {
            "success": False,
            "message": "Driver not found."
        }

    if driver.company_id != company_id:
        return {
            "success": False,
            "message": "Driver does not belong to this company."
        }

    if not driver.is_active:
        return {
            "success": False,
            "message": "Driver is inactive."
        }

    # Company-scoped vehicle lookup
    new_vehicle = get_vehicle_by_id_query(
        db,
        company_id,
        new_vehicle_id
    )

    if not new_vehicle:
        return {
            "success": False,
            "message": "Vehicle not found."
        }

    if new_vehicle.company_id != company_id:
        return {
            "success": False,
            "message": "Vehicle does not belong to this company."
        }

    if not new_vehicle.is_active:
        return {
            "success": False,
            "message": "Vehicle is inactive."
        }

    current_assignment = get_active_assignment_by_driver_id_query(
        db,
        driver_id
    )

    if not current_assignment:
        return {
            "success": False,
            "message": "Driver has no active assignment."
        }

    if current_assignment.vehicle_id == new_vehicle_id:
        return {
            "success": False,
            "message": "Driver is already assigned to this vehicle."
        }

    active_vehicle_assignment = get_active_assignment_by_vehicle_id_query(
        db,
        new_vehicle_id
    )

    if active_vehicle_assignment:
        return {
            "success": False,
            "message": "Vehicle is already assigned to another driver."
        }

    current_assignment.is_active = False
    current_assignment.unassigned_at = datetime.now(timezone.utc)

    update_assignment_query(
        db,
        current_assignment
    )

    new_assignment = DriverVehicleAssignment(
        company_id=company_id,
        driver_id=driver_id,
        vehicle_id=new_vehicle_id,
        assigned_by=assigned_by
    )

    new_assignment = create_assignment_query(
        db,
        new_assignment
    )

    return {
        "success": True,
        "message": "Driver transferred successfully.",
        "assignment": new_assignment
    }


def get_assignment_service(
    db: Session,
    company_id: UUID,
    assignment_id: UUID
):
    company = get_company_by_id_query(
        db,
        company_id
    )

    if not company:
        return {
            "success": False,
            "message": "Company not found."
        }

    assignment = get_assignment_by_id_query(
        db,
        assignment_id
    )

    if not assignment:
        return {
            "success": False,
            "message": "Assignment not found."
        }

    if assignment.company_id != company_id:
        return {
            "success": False,
            "message": "Assignment does not belong to this company."
        }

    return {
        "success": True,
        "assignment": assignment
    }


def get_company_assignments_service(
    db: Session,
    company_id: UUID
):
    company = get_company_by_id_query(
        db,
        company_id
    )

    if not company:
        return {
            "success": False,
            "message": "Company not found.",
            "assignments": []
        }

    assignments = (
        db.query(DriverVehicleAssignment)
        .filter(
            DriverVehicleAssignment.company_id == company_id,
            DriverVehicleAssignment.is_active.is_(True)
        )
        .all()
    )

    return {
        "success": True,
        "message": "Company assignments retrieved successfully.",
        "assignments": assignments
    }