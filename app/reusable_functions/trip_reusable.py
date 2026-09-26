from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date, timedelta
from app.models.trip import Trip


def get_by_id(db: Session, trip_id: UUID,) -> Trip | None:

    return (db.query(Trip).filter(Trip.id == trip_id).first())


def get_by_company(db: Session, company_id: UUID,) -> list[Trip]:

    return (db.query(Trip).filter(Trip.company_id == company_id).order_by(Trip.created_at.desc()).all())


def get_by_vehicle(db: Session, vehicle_id: UUID,) -> list[Trip]:

    return (db.query(Trip).filter(Trip.vehicle_id == vehicle_id).order_by(Trip.created_at.desc()).all())


def get_by_driver(db: Session,driver_id: UUID,) -> list[Trip]:

    return (db.query(Trip).filter(Trip.driver_id == driver_id).order_by(Trip.created_at.desc()).all())


def get_by_status(db: Session, company_id: UUID, status: str,) -> list[Trip]:

    return (db.query(Trip).filter(
        Trip.company_id == company_id,
        Trip.status == status).order_by(Trip.created_at.desc()).all())


def get_by_date_range(
    db: Session,
    company_id: UUID,
    start_date: date,
    end_date: date,
) -> list[Trip]:

    end_datetime = end_date + timedelta(days=1)

    return (
        db.query(Trip)
        .filter(
            Trip.company_id == company_id,
            Trip.created_at >= start_date,
            Trip.created_at < end_datetime,
        )
        .order_by(Trip.created_at.desc())
        .all()
    )


def get_by_vehicle_and_date_range(
    db: Session,
    vehicle_id: UUID,
    start_date: date,
    end_date: date,
) -> list[Trip]:

    end_datetime = end_date + timedelta(days=1)

    return (
        db.query(Trip)
        .filter(
            Trip.vehicle_id == vehicle_id,
            Trip.created_at >= start_date,
            Trip.created_at < end_datetime,
        )
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
) -> None:

    db.delete(trip)
    db.commit()


def get_by_driver_and_date_range(
    db: Session,
    driver_id: UUID,
    start_date: date,
    end_date: date,
) -> list[Trip]:

    end_datetime = end_date + timedelta(days=1)

    return (
        db.query(Trip)
        .filter(
            Trip.driver_id == driver_id,
            Trip.created_at >= start_date,
            Trip.created_at < end_datetime,
        )
        .order_by(Trip.created_at.desc())
        .all()
    ) 