from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.models.maintenance_record import MaintenanceRecord


def get_by_id(
    db: Session,
    maintenance_id: UUID,
):
    return (
        db.query(MaintenanceRecord)
        .filter(
            MaintenanceRecord.id == maintenance_id,
            MaintenanceRecord.is_active.is_(True),
        )
        .first()
    )


def get_by_company(
    db: Session,
    company_id: UUID,
):
    return (
        db.query(MaintenanceRecord)
        .filter(
            MaintenanceRecord.company_id == company_id,
            MaintenanceRecord.is_active.is_(True),
        )
        .order_by(MaintenanceRecord.service_date.desc())
        .all()
    )


def get_by_vehicle(
    db: Session,
    vehicle_id: UUID,
):
    return (
        db.query(MaintenanceRecord)
        .filter(
            MaintenanceRecord.vehicle_id == vehicle_id,
            MaintenanceRecord.is_active.is_(True),
        )
        .order_by(MaintenanceRecord.service_date.desc())
        .all()
    )



def get_by_date_range(
    db: Session,
    company_id: UUID,
    start_date: date,
    end_date: date,
):
    return (
        db.query(MaintenanceRecord)
        .filter(
            MaintenanceRecord.company_id == company_id,
            MaintenanceRecord.service_date >= start_date,
            MaintenanceRecord.service_date <= end_date,
            MaintenanceRecord.is_active.is_(True),
        )
        .order_by(MaintenanceRecord.service_date.desc())
        .all()
    )


def get_by_vehicle_and_date_range(
    db: Session,
    vehicle_id: UUID,
    start_date: date,
    end_date: date,
):
    return (
        db.query(MaintenanceRecord)
        .filter(
            MaintenanceRecord.vehicle_id == vehicle_id,
            MaintenanceRecord.service_date >= start_date,
            MaintenanceRecord.service_date <= end_date,
            MaintenanceRecord.is_active.is_(True),
        )
        .order_by(MaintenanceRecord.service_date.desc())
        .all()
    )


def get_by_maintenance_type(
    db: Session,
    company_id: UUID,
    maintenance_type: str,
):
    return (
        db.query(MaintenanceRecord)
        .filter(
            MaintenanceRecord.company_id == company_id,
            MaintenanceRecord.maintenance_type == maintenance_type,
            MaintenanceRecord.is_active.is_(True),
        )
        .order_by(MaintenanceRecord.service_date.desc())
        .all()
    )


def get_inactive_by_id(
    db: Session,
    maintenance_id: UUID,
):
    return (
        db.query(MaintenanceRecord)
        .filter(
            MaintenanceRecord.id == maintenance_id,
            MaintenanceRecord.is_active.is_(False),
        )
        .first()
    )


def get_total_cost(
    db: Session,
    company_id: UUID,
) -> Decimal:

    total = (
        db.query(func.coalesce(func.sum(MaintenanceRecord.cost), 0))
        .filter(
            MaintenanceRecord.company_id == company_id,
            MaintenanceRecord.is_active.is_(True),
        )
        .scalar()
    )

    return Decimal(total)


def get_vehicle_total_cost(
    db: Session,
    vehicle_id: UUID,
) -> Decimal:

    total = (
        db.query(func.coalesce(func.sum(MaintenanceRecord.cost), 0))
        .filter(
            MaintenanceRecord.vehicle_id == vehicle_id,
            MaintenanceRecord.is_active.is_(True),
        )
        .scalar()
    )

    return Decimal(total)


def create_record(
    db: Session,
    maintenance: MaintenanceRecord,
):
    db.add(maintenance)
    db.commit()
    db.refresh(maintenance)

    return maintenance


def update_record(
    db: Session,
    maintenance: MaintenanceRecord,
):
    db.commit()
    db.refresh(maintenance)

    return maintenance


def soft_delete_record(
    db: Session,
    maintenance: MaintenanceRecord,
):
    maintenance.is_active = False

    db.commit()
    db.refresh(maintenance)

    return maintenance


def get_total_cost_by_date_range(
    db: Session,
    company_id: UUID,
    start_date: date,
    end_date: date,
) -> Decimal:

    total = (
        db.query(func.coalesce(func.sum(MaintenanceRecord.cost), 0))
        .filter(
            MaintenanceRecord.company_id == company_id,
            MaintenanceRecord.service_date >= start_date,
            MaintenanceRecord.service_date <= end_date,
            MaintenanceRecord.is_active.is_(True),
        )
        .scalar()
    )

    return Decimal(total)


def get_vehicle_total_cost_by_date_range(
    db: Session,
    vehicle_id: UUID,
    start_date: date,
    end_date: date,
) -> Decimal:

    total = (
        db.query(func.coalesce(func.sum(MaintenanceRecord.cost), 0))
        .filter(
            MaintenanceRecord.vehicle_id == vehicle_id,
            MaintenanceRecord.service_date >= start_date,
            MaintenanceRecord.service_date <= end_date,
            MaintenanceRecord.is_active.is_(True),
        )
        .scalar()
    )

    return Decimal(total)


def get_upcoming_by_date(
    db: Session,
    company_id: UUID,
    target_date: date,
):

    return (
        db.query(MaintenanceRecord)
        .filter(
            MaintenanceRecord.company_id == company_id,
            MaintenanceRecord.next_service_date.isnot(None),
            MaintenanceRecord.next_service_date <= target_date,
            MaintenanceRecord.is_active.is_(True),
        )
        .order_by(MaintenanceRecord.next_service_date.asc())
        .all()
    )


def get_by_due_date(
    db: Session,
    company_id: UUID,
    target_date: date,
):

    return (
        db.query(MaintenanceRecord)
        .filter(
            MaintenanceRecord.company_id == company_id,
            MaintenanceRecord.next_service_date.isnot(None),
            MaintenanceRecord.next_service_date <= target_date,
            MaintenanceRecord.is_active.is_(True),
        )
        .order_by(
            MaintenanceRecord.next_service_date.asc()
        )
        .all()
    )