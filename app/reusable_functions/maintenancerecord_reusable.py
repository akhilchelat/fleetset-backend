from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.maintenance_record import MaintenanceRecord


def get_by_id(
    db: Session,
    maintenance_id: UUID,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
    active_only: bool = True,
):
    query = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.id == maintenance_id,
    )

    if company_id is not None:
        query = query.filter(
            MaintenanceRecord.company_id == company_id,
        )

    if branch_id is not None:
        query = query.filter(
            MaintenanceRecord.branch_id == branch_id,
        )

    if active_only:
        query = query.filter(
            MaintenanceRecord.is_active.is_(True),
        )

    return query.first()


def get_by_company(
    db: Session,
    company_id: UUID,
    branch_id: UUID | None = None,
    active_only: bool = True,
):
    query = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.company_id == company_id,
    )

    if branch_id is not None:
        query = query.filter(
            MaintenanceRecord.branch_id == branch_id,
        )

    if active_only:
        query = query.filter(
            MaintenanceRecord.is_active.is_(True),
        )

    return (
        query
        .order_by(MaintenanceRecord.service_date.desc())
        .all()
    )


def get_by_vehicle(
    db: Session,
    vehicle_id: UUID,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
    active_only: bool = True,
):
    query = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.vehicle_id == vehicle_id,
    )

    if company_id is not None:
        query = query.filter(
            MaintenanceRecord.company_id == company_id,
        )

    if branch_id is not None:
        query = query.filter(
            MaintenanceRecord.branch_id == branch_id,
        )

    if active_only:
        query = query.filter(
            MaintenanceRecord.is_active.is_(True),
        )

    return (
        query
        .order_by(MaintenanceRecord.service_date.desc())
        .all()
    )


def get_by_date_range(
    db: Session,
    company_id: UUID,
    start_date: date,
    end_date: date,
    branch_id: UUID | None = None,
    active_only: bool = True,
):
    query = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.company_id == company_id,
        MaintenanceRecord.service_date >= start_date,
        MaintenanceRecord.service_date <= end_date,
    )

    if branch_id is not None:
        query = query.filter(
            MaintenanceRecord.branch_id == branch_id,
        )

    if active_only:
        query = query.filter(
            MaintenanceRecord.is_active.is_(True),
        )

    return (
        query
        .order_by(MaintenanceRecord.service_date.desc())
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
):
    query = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.vehicle_id == vehicle_id,
        MaintenanceRecord.service_date >= start_date,
        MaintenanceRecord.service_date <= end_date,
    )

    if company_id is not None:
        query = query.filter(
            MaintenanceRecord.company_id == company_id,
        )

    if branch_id is not None:
        query = query.filter(
            MaintenanceRecord.branch_id == branch_id,
        )

    if active_only:
        query = query.filter(
            MaintenanceRecord.is_active.is_(True),
        )

    return (
        query
        .order_by(MaintenanceRecord.service_date.desc())
        .all()
    )


def get_by_maintenance_type(
    db: Session,
    company_id: UUID,
    maintenance_type: str,
    branch_id: UUID | None = None,
    active_only: bool = True,
):
    query = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.company_id == company_id,
        MaintenanceRecord.maintenance_type == maintenance_type,
    )

    if branch_id is not None:
        query = query.filter(
            MaintenanceRecord.branch_id == branch_id,
        )

    if active_only:
        query = query.filter(
            MaintenanceRecord.is_active.is_(True),
        )

    return (
        query
        .order_by(MaintenanceRecord.service_date.desc())
        .all()
    )


def get_inactive_by_id(
    db: Session,
    maintenance_id: UUID,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
):
    query = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.id == maintenance_id,
        MaintenanceRecord.is_active.is_(False),
    )

    if company_id is not None:
        query = query.filter(
            MaintenanceRecord.company_id == company_id,
        )

    if branch_id is not None:
        query = query.filter(
            MaintenanceRecord.branch_id == branch_id,
        )

    return query.first()


def get_total_cost(
    db: Session,
    company_id: UUID,
    branch_id: UUID | None = None,
) -> Decimal:
    query = db.query(
        func.coalesce(
            func.sum(MaintenanceRecord.cost),
            0,
        )
    ).filter(
        MaintenanceRecord.company_id == company_id,
        MaintenanceRecord.is_active.is_(True),
    )

    if branch_id is not None:
        query = query.filter(
            MaintenanceRecord.branch_id == branch_id,
        )

    total = query.scalar()

    return Decimal(total)


def get_vehicle_total_cost(
    db: Session,
    vehicle_id: UUID,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
) -> Decimal:
    query = db.query(
        func.coalesce(
            func.sum(MaintenanceRecord.cost),
            0,
        )
    ).filter(
        MaintenanceRecord.vehicle_id == vehicle_id,
        MaintenanceRecord.is_active.is_(True),
    )

    if company_id is not None:
        query = query.filter(
            MaintenanceRecord.company_id == company_id,
        )

    if branch_id is not None:
        query = query.filter(
            MaintenanceRecord.branch_id == branch_id,
        )

    total = query.scalar()

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
    branch_id: UUID | None = None,
) -> Decimal:
    query = db.query(
        func.coalesce(
            func.sum(MaintenanceRecord.cost),
            0,
        )
    ).filter(
        MaintenanceRecord.company_id == company_id,
        MaintenanceRecord.service_date >= start_date,
        MaintenanceRecord.service_date <= end_date,
        MaintenanceRecord.is_active.is_(True),
    )

    if branch_id is not None:
        query = query.filter(
            MaintenanceRecord.branch_id == branch_id,
        )

    total = query.scalar()

    return Decimal(total)


def get_vehicle_total_cost_by_date_range(
    db: Session,
    vehicle_id: UUID,
    start_date: date,
    end_date: date,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
) -> Decimal:
    query = db.query(
        func.coalesce(
            func.sum(MaintenanceRecord.cost),
            0,
        )
    ).filter(
        MaintenanceRecord.vehicle_id == vehicle_id,
        MaintenanceRecord.service_date >= start_date,
        MaintenanceRecord.service_date <= end_date,
        MaintenanceRecord.is_active.is_(True),
    )

    if company_id is not None:
        query = query.filter(
            MaintenanceRecord.company_id == company_id,
        )

    if branch_id is not None:
        query = query.filter(
            MaintenanceRecord.branch_id == branch_id,
        )

    total = query.scalar()

    return Decimal(total)


def get_upcoming_by_date(
    db: Session,
    company_id: UUID,
    target_date: date,
    branch_id: UUID | None = None,
):
    query = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.company_id == company_id,
        MaintenanceRecord.next_service_date.isnot(None),
        MaintenanceRecord.next_service_date <= target_date,
        MaintenanceRecord.is_active.is_(True),
    )

    if branch_id is not None:
        query = query.filter(
            MaintenanceRecord.branch_id == branch_id,
        )

    return (
        query
        .order_by(MaintenanceRecord.next_service_date.asc())
        .all()
    )


def get_by_due_date(
    db: Session,
    company_id: UUID,
    target_date: date,
    branch_id: UUID | None = None,
):
    query = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.company_id == company_id,
        MaintenanceRecord.next_service_date.isnot(None),
        MaintenanceRecord.next_service_date <= target_date,
        MaintenanceRecord.is_active.is_(True),
    )

    if branch_id is not None:
        query = query.filter(
            MaintenanceRecord.branch_id == branch_id,
        )

    return (
        query
        .order_by(MaintenanceRecord.next_service_date.asc())
        .all()
    )