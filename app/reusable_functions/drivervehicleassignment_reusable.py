from uuid import UUID

from sqlalchemy.orm import Session

from app.models.drivervehicleassignment import DriverVehicleAssignment


def get_assignment_by_id_query(
    db: Session,
    assignment_id: UUID,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
) -> DriverVehicleAssignment | None:
    query = db.query(DriverVehicleAssignment).filter(
        DriverVehicleAssignment.id == assignment_id
    )

    if company_id is not None:
        query = query.filter(
            DriverVehicleAssignment.company_id == company_id
        )

    if branch_id is not None:
        query = query.filter(
            DriverVehicleAssignment.branch_id == branch_id
        )

    return query.first()


def get_active_assignment_by_driver_id_query(
    db: Session,
    driver_id: UUID,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
) -> DriverVehicleAssignment | None:
    query = db.query(DriverVehicleAssignment).filter(
        DriverVehicleAssignment.driver_id == driver_id,
        DriverVehicleAssignment.is_active.is_(True),
    )

    if company_id is not None:
        query = query.filter(
            DriverVehicleAssignment.company_id == company_id
        )

    if branch_id is not None:
        query = query.filter(
            DriverVehicleAssignment.branch_id == branch_id
        )

    return query.first()


def get_active_assignment_by_vehicle_id_query(
    db: Session,
    vehicle_id: UUID,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
) -> DriverVehicleAssignment | None:
    query = db.query(DriverVehicleAssignment).filter(
        DriverVehicleAssignment.vehicle_id == vehicle_id,
        DriverVehicleAssignment.is_active.is_(True),
    )

    if company_id is not None:
        query = query.filter(
            DriverVehicleAssignment.company_id == company_id
        )

    if branch_id is not None:
        query = query.filter(
            DriverVehicleAssignment.branch_id == branch_id
        )

    return query.first()


def get_driver_assignments_query(
    db: Session,
    driver_id: UUID,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
) -> list[DriverVehicleAssignment]:
    query = db.query(DriverVehicleAssignment).filter(
        DriverVehicleAssignment.driver_id == driver_id
    )

    if company_id is not None:
        query = query.filter(
            DriverVehicleAssignment.company_id == company_id
        )

    if branch_id is not None:
        query = query.filter(
            DriverVehicleAssignment.branch_id == branch_id
        )

    return (
        query
        .order_by(DriverVehicleAssignment.assigned_at.desc())
        .all()
    )


def get_vehicle_assignments_query(
    db: Session,
    vehicle_id: UUID,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
) -> list[DriverVehicleAssignment]:
    query = db.query(DriverVehicleAssignment).filter(
        DriverVehicleAssignment.vehicle_id == vehicle_id
    )

    if company_id is not None:
        query = query.filter(
            DriverVehicleAssignment.company_id == company_id
        )

    if branch_id is not None:
        query = query.filter(
            DriverVehicleAssignment.branch_id == branch_id
        )

    return (
        query
        .order_by(DriverVehicleAssignment.assigned_at.desc())
        .all()
    )


def get_company_assignments_query(
    db: Session,
    company_id: UUID,
    branch_id: UUID | None = None,
) -> list[DriverVehicleAssignment]:
    query = db.query(DriverVehicleAssignment).filter(
        DriverVehicleAssignment.company_id == company_id
    )

    if branch_id is not None:
        query = query.filter(
            DriverVehicleAssignment.branch_id == branch_id
        )

    return (
        query
        .order_by(DriverVehicleAssignment.assigned_at.desc())
        .all()
    )


def create_assignment_query(
    db: Session,
    assignment: DriverVehicleAssignment,
) -> DriverVehicleAssignment:
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return assignment


def update_assignment_query(
    db: Session,
    assignment: DriverVehicleAssignment,
) -> DriverVehicleAssignment:
    db.commit()
    db.refresh(assignment)

    return assignment


def deactivate_assignment_query(
    db: Session,
    assignment: DriverVehicleAssignment,
) -> DriverVehicleAssignment:
    assignment.is_active = False

    db.commit()
    db.refresh(assignment)

    return assignment