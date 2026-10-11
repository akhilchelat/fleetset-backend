from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.trip import Trip


def get_by_id(
    db: Session,
    trip_id: UUID,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
    active_only: bool = True,
) -> Trip | None:
    query = db.query(Trip).filter(
        Trip.id == trip_id,
    )

    if active_only:
        query = query.filter(
            Trip.is_active.is_(True),
        )

    if company_id is not None:
        query = query.filter(
            Trip.company_id == company_id,
        )

    if branch_id is not None:
        query = query.filter(
            Trip.branch_id == branch_id,
        )

    return query.first()


def get_by_company(
    db: Session,
    company_id: UUID,
    branch_id: UUID | None = None,
    active_only: bool = True,
) -> list[Trip]:
    query = db.query(Trip).filter(
        Trip.company_id == company_id,
    )

    if branch_id is not None:
        query = query.filter(
            Trip.branch_id == branch_id,
        )

    if active_only:
        query = query.filter(
            Trip.is_active.is_(True),
        )

    return (
        query
        .order_by(Trip.created_at.desc())
        .all()
    )


def get_by_vehicle(
    db: Session,
    vehicle_id: UUID,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
    active_only: bool = True,
) -> list[Trip]:
    query = db.query(Trip).filter(
        Trip.vehicle_id == vehicle_id,
    )

    if company_id is not None:
        query = query.filter(
            Trip.company_id == company_id,
        )

    if branch_id is not None:
        query = query.filter(
            Trip.branch_id == branch_id,
        )

    if active_only:
        query = query.filter(
            Trip.is_active.is_(True),
        )

    return (
        query
        .order_by(Trip.created_at.desc())
        .all()
    )


def get_by_driver(
    db: Session,
    driver_id: UUID,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
    active_only: bool = True,
) -> list[Trip]:
    query = db.query(Trip).filter(
        Trip.driver_id == driver_id,
    )

    if company_id is not None:
        query = query.filter(
            Trip.company_id == company_id,
        )

    if branch_id is not None:
        query = query.filter(
            Trip.branch_id == branch_id,
        )

    if active_only:
        query = query.filter(
            Trip.is_active.is_(True),
        )

    return (
        query
        .order_by(Trip.created_at.desc())
        .all()
    )


def get_by_status(
    db: Session,
    company_id: UUID,
    status: str,
    branch_id: UUID | None = None,
    active_only: bool = True,
) -> list[Trip]:
    query = db.query(Trip).filter(
        Trip.company_id == company_id,
        Trip.status == status,
    )

    if branch_id is not None:
        query = query.filter(
            Trip.branch_id == branch_id,
        )

    if active_only:
        query = query.filter(
            Trip.is_active.is_(True),
        )

    return (
        query
        .order_by(Trip.created_at.desc())
        .all()
    )


def get_by_date_range(
    db: Session,
    company_id: UUID,
    start_date: date,
    end_date: date,
    branch_id: UUID | None = None,
    active_only: bool = True,
) -> list[Trip]:
    end_datetime = end_date + timedelta(days=1)

    query = db.query(Trip).filter(
        Trip.company_id == company_id,
        Trip.created_at >= start_date,
        Trip.created_at < end_datetime,
    )

    if branch_id is not None:
        query = query.filter(
            Trip.branch_id == branch_id,
        )

    if active_only:
        query = query.filter(
            Trip.is_active.is_(True),
        )

    return (
        query
        .order_by(Trip.created_at.desc())
        .all()
    )


def get_by_vehicle_and_date_range(
    db: Session,
    vehicle_id: UUID,
    start_date: date,
    end_date: date,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
    active_only: bool = True,
) -> list[Trip]:
    end_datetime = end_date + timedelta(days=1)

    query = db.query(Trip).filter(
        Trip.vehicle_id == vehicle_id,
        Trip.created_at >= start_date,
        Trip.created_at < end_datetime,
    )

    if company_id is not None:
        query = query.filter(
            Trip.company_id == company_id,
        )

    if branch_id is not None:
        query = query.filter(
            Trip.branch_id == branch_id,
        )

    if active_only:
        query = query.filter(
            Trip.is_active.is_(True),
        )

    return (
        query
        .order_by(Trip.created_at.desc())
        .all()
    )


def get_by_driver_and_date_range(
    db: Session,
    driver_id: UUID,
    start_date: date,
    end_date: date,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
    active_only: bool = True,
) -> list[Trip]:
    end_datetime = end_date + timedelta(days=1)

    query = db.query(Trip).filter(
        Trip.driver_id == driver_id,
        Trip.created_at >= start_date,
        Trip.created_at < end_datetime,
    )

    if company_id is not None:
        query = query.filter(
            Trip.company_id == company_id,
        )

    if branch_id is not None:
        query = query.filter(
            Trip.branch_id == branch_id,
        )

    if active_only:
        query = query.filter(
            Trip.is_active.is_(True),
        )

    return (
        query
        .order_by(Trip.created_at.desc())
        .all()
    )


def create_record(
    db: Session,
    trip: Trip,
) -> Trip:
    db.add(trip)
    db.commit()
    db.refresh(trip)

    return trip


def update_record(
    db: Session,
    trip: Trip,
) -> Trip:
    db.commit()
    db.refresh(trip)

    return trip


def delete_record(
    db: Session,
    trip: Trip,
) -> Trip:
    trip.is_active = False

    db.commit()
    db.refresh(trip)

    return trip