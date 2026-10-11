from uuid import UUID

from sqlalchemy.orm import Session

from app.models.vehicle import Vehicle


def get_vehicle_by_registration_number_query(
    db: Session,
    company_id: UUID,
    branch_id: UUID,
    registration_number: str
):
    return (
        db.query(Vehicle)
        .filter(
            Vehicle.company_id == company_id,
            Vehicle.branch_id == branch_id,
            Vehicle.registration_number == registration_number,
            Vehicle.is_active.is_(True)
        )
        .first()
    )


def get_vehicle_by_registration_number_admin_query(
    db: Session,
    registration_number: str
):
    return (
        db.query(Vehicle)
        .filter(
            Vehicle.registration_number == registration_number,
            Vehicle.is_active.is_(True)
        )
        .first()
    )


def get_vehicle_by_id_query(
    db: Session,
    company_id: UUID,
    branch_id: UUID,
    vehicle_id: UUID
):
    return (
        db.query(Vehicle)
        .filter(
            Vehicle.company_id == company_id,
            Vehicle.branch_id == branch_id,
            Vehicle.id == vehicle_id,
            Vehicle.is_active.is_(True)
        )
        .first()
    )


def get_vehicle_by_company_id_query(
    db: Session,
    company_id: UUID,
    vehicle_id: UUID
):
    return (
        db.query(Vehicle)
        .filter(
            Vehicle.company_id == company_id,
            Vehicle.id == vehicle_id,
            Vehicle.is_active.is_(True)
        )
        .first()
    )


def get_active_vehicle_by_id_admin_query(
    db: Session,
    vehicle_id: UUID
):
    return (
        db.query(Vehicle)
        .filter(
            Vehicle.id == vehicle_id,
            Vehicle.is_active.is_(True)
        )
        .first()
    )


def get_vehicle_by_id_admin_query(
    db: Session,
    vehicle_id: UUID
):
    return (
        db.query(Vehicle)
        .filter(
            Vehicle.id == vehicle_id
        )
        .first()
    )


def get_all_vehicles_query(
    db: Session,
    company_id: UUID,
    branch_id: UUID | None = None
):
    query = (
        db.query(Vehicle)
        .filter(
            Vehicle.company_id == company_id,
            Vehicle.is_active.is_(True)
        )
    )

    if branch_id is not None:
        query = query.filter(
            Vehicle.branch_id == branch_id
        )

    return query.all()


def get_all_vehicles_admin_query(
    db: Session
):
    return db.query(Vehicle).all()


def get_vehicles_by_ids_query(
    db: Session,
    vehicle_ids: list[UUID]
):
    return (
        db.query(Vehicle)
        .filter(
            Vehicle.id.in_(vehicle_ids)
        )
        .all()
    )


def get_company_vehicles_by_ids_query(
    db: Session,
    company_id: UUID,
    vehicle_ids: list[UUID],
    branch_id: UUID | None = None
):
    query = (
        db.query(Vehicle)
        .filter(
            Vehicle.company_id == company_id,
            Vehicle.id.in_(vehicle_ids)
        )
    )

    if branch_id is not None:
        query = query.filter(
            Vehicle.branch_id == branch_id
        )

    return query.all()


def get_active_vehicle_by_id_query(
    db: Session,
    company_id: UUID,
    branch_id: UUID,
    vehicle_id: UUID
):
    return (
        db.query(Vehicle)
        .filter(
            Vehicle.company_id == company_id,
            Vehicle.branch_id == branch_id,
            Vehicle.id == vehicle_id,
            Vehicle.is_active.is_(True)
        )
        .first()
    )


def get_inactive_vehicle_by_id_query(
    db: Session,
    company_id: UUID,
    branch_id: UUID,
    vehicle_id: UUID
):
    return (
        db.query(Vehicle)
        .filter(
            Vehicle.company_id == company_id,
            Vehicle.branch_id == branch_id,
            Vehicle.id == vehicle_id,
            Vehicle.is_active.is_(False)
        )
        .first()
    )


def get_all_active_vehicles_query(
    db: Session,
    company_id: UUID,
    branch_id: UUID | None = None
):
    query = (
        db.query(Vehicle)
        .filter(
            Vehicle.company_id == company_id,
            Vehicle.is_active.is_(True)
        )
    )

    if branch_id is not None:
        query = query.filter(
            Vehicle.branch_id == branch_id
        )

    return query.all()


def get_all_inactive_vehicles_query(
    db: Session,
    company_id: UUID,
    branch_id: UUID | None = None
):
    query = (
        db.query(Vehicle)
        .filter(
            Vehicle.company_id == company_id,
            Vehicle.is_active.is_(False)
        )
    )

    if branch_id is not None:
        query = query.filter(
            Vehicle.branch_id == branch_id
        )

    return query.all()