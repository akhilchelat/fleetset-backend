from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date
from decimal import Decimal
from sqlalchemy import func
from app.models.fuel_log import FuelLog


def get_by_id(db: Session, fuel_log_id: UUID,) -> FuelLog | None:

    return (db.query(FuelLog).filter(FuelLog.id == fuel_log_id).first())


def get_by_company(db: Session, company_id: UUID,) -> list[FuelLog]:

    return (db.query(FuelLog).filter(FuelLog.company_id == company_id).order_by(FuelLog.fuel_date.desc()).all())


def get_by_vehicle(db: Session, vehicle_id: UUID,) -> list[FuelLog]:

    return (db.query(FuelLog).filter(FuelLog.vehicle_id == vehicle_id).order_by(FuelLog.fuel_date.desc()).all())


def get_by_driver(db: Session, driver_id: UUID,) -> list[FuelLog]:

    return (db.query(FuelLog).filter(FuelLog.driver_id == driver_id).order_by(FuelLog.fuel_date.desc()).all())


def get_by_date_range(db: Session, company_id: UUID, start_date: date, end_date: date,) -> list[FuelLog]:

    return (db.query(FuelLog).filter(FuelLog.company_id == company_id,
                                     FuelLog.fuel_date >= start_date,
                                     FuelLog.fuel_date <= end_date,)
                                     .order_by(FuelLog.fuel_date.desc()).all())


def get_by_vehicle_and_date_range(db: Session, vehicle_id: UUID, start_date: date, end_date: date,) -> list[FuelLog]:

    return (db.query(FuelLog).filter(
        FuelLog.vehicle_id == vehicle_id,
        FuelLog.fuel_date >= start_date,
        FuelLog.fuel_date <= end_date,)
        .order_by(FuelLog.fuel_date.desc())
        .all())


def get_by_driver_and_date_range(db: Session, driver_id: UUID, start_date: date, end_date: date,) -> list[FuelLog]:

    return (db.query(FuelLog).filter(
        FuelLog.driver_id == driver_id,
        FuelLog.fuel_date >= start_date,
        FuelLog.fuel_date <= end_date,)
        .order_by(FuelLog.fuel_date.desc())
        .all())


def create_record(db: Session, fuel_log: FuelLog,) -> FuelLog:

    db.add(fuel_log)
    db.commit()
    db.refresh(fuel_log)

    return fuel_log


def update_record(db: Session, fuel_log: FuelLog,) -> FuelLog:

    db.commit()
    db.refresh(fuel_log)

    return fuel_log


def soft_delete_record(db: Session, fuel_log: FuelLog,) -> FuelLog:

    fuel_log.is_active = False

    db.commit()
    db.refresh(fuel_log)

    return fuel_log


def get_total_cost(fuel_logs: list[FuelLog],) -> Decimal:

    return sum((fuel_log.fuel_cost for fuel_log in fuel_logs),Decimal("0.00"),)


def get_total_cost_by_date_range(
    db: Session,
    company_id: UUID,
    start_date: date,
    end_date: date,
):
    return (
        db.query(func.coalesce(func.sum(FuelLog.fuel_cost), 0))
        .filter(
            FuelLog.company_id == company_id,
            FuelLog.fuel_date >= start_date,
            FuelLog.fuel_date <= end_date,
            FuelLog.is_active.is_(True),
        )
        .scalar()
    )