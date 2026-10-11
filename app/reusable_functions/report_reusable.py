from datetime import date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.trip import Trip
from app.models.fuel_log import FuelLog
from app.models.maintenance_record import MaintenanceRecord

from app.reusable_functions.company_reusable import (
    get_company_by_id_query,
)

from app.reusable_functions.vehicle_reusable import (
    get_all_active_vehicles_query,
    get_all_inactive_vehicles_query,
)

from app.reusable_functions.driver_reusable import (
    get_all_drivers_query,
)

from app.reusable_functions.fuel_log_reusable import (
    get_by_date_range as get_fuel_logs_by_date_range,
    get_total_cost as get_fuel_total_cost,
)

from app.reusable_functions.maintenancerecord_reusable import (
    get_by_date_range as get_maintenance_by_date_range,
    get_total_cost_by_date_range as get_maintenance_total_cost_by_date_range,
)


def get_report_company(
    db: Session,
    company_id: UUID,
):
    return get_company_by_id_query(
        db=db,
        company_id=company_id,
    )


def get_report_active_vehicles(
    db: Session,
    company_id: UUID,
    branch_id: UUID | None = None,
):
    vehicles = get_all_active_vehicles_query(
        db=db,
        company_id=company_id,
    )

    if branch_id is not None:
        vehicles = [
            vehicle
            for vehicle in vehicles
            if vehicle.branch_id == branch_id
        ]

    return vehicles


def get_report_inactive_vehicles(
    db: Session,
    company_id: UUID,
    branch_id: UUID | None = None,
):
    vehicles = get_all_inactive_vehicles_query(
        db=db,
        company_id=company_id,
    )

    if branch_id is not None:
        vehicles = [
            vehicle
            for vehicle in vehicles
            if vehicle.branch_id == branch_id
        ]

    return vehicles


def get_report_all_vehicles(
    db: Session,
    company_id: UUID,
    branch_id: UUID | None = None,
):
    active_vehicles = get_report_active_vehicles(
        db=db,
        company_id=company_id,
        branch_id=branch_id,
    )

    inactive_vehicles = get_report_inactive_vehicles(
        db=db,
        company_id=company_id,
        branch_id=branch_id,
    )

    return active_vehicles + inactive_vehicles


def get_report_drivers(
    db: Session,
    company_id: UUID,
    branch_id: UUID | None = None,
):
    return get_all_drivers_query(
        db=db,
        company_id=company_id,
        branch_id=branch_id,
    )


def get_report_trips(
    db: Session,
    company_id: UUID,
    start_date: date,
    end_date: date,
    branch_id: UUID | None = None,
):
    start_datetime = datetime.combine(
        start_date,
        time.min,
    )

    end_datetime = datetime.combine(
        end_date + timedelta(days=1),
        time.min,
    )

    query = (
        db.query(Trip)
        .filter(
            Trip.company_id == company_id,
            Trip.created_at >= start_datetime,
            Trip.created_at < end_datetime,
            Trip.is_active.is_(True),
        )
    )

    if branch_id is not None:
        query = query.filter(
            Trip.branch_id == branch_id,
        )

    return (
        query
        .order_by(Trip.created_at.desc())
        .all()
    )


def get_report_fuel_logs(
    db: Session,
    company_id: UUID,
    start_date: date,
    end_date: date,
    branch_id: UUID | None = None,
):
    fuel_logs = get_fuel_logs_by_date_range(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
        branch_id=branch_id,
    )

    return [
        fuel
        for fuel in fuel_logs
        if fuel.is_active is True
    ]


def get_report_fuel_total(
    fuel_logs: list[FuelLog],
) -> Decimal:
    active_fuel_logs = [
        fuel
        for fuel in fuel_logs
        if fuel.is_active is True
    ]

    return get_fuel_total_cost(
        fuel_logs=active_fuel_logs,
    )


def get_report_fuel_total_by_date_range(
    db: Session,
    company_id: UUID,
    start_date: date,
    end_date: date,
    branch_id: UUID | None = None,
) -> Decimal:
    query = (
        db.query(
            func.coalesce(
                func.sum(FuelLog.fuel_cost),
                0,
            )
        )
        .filter(
            FuelLog.company_id == company_id,
            FuelLog.fuel_date >= start_date,
            FuelLog.fuel_date <= end_date,
            FuelLog.is_active.is_(True),
        )
    )

    if branch_id is not None:
        query = query.filter(
            FuelLog.branch_id == branch_id,
        )

    total = query.scalar()

    return Decimal(total)


def get_report_maintenance_records(
    db: Session,
    company_id: UUID,
    start_date: date,
    end_date: date,
    branch_id: UUID | None = None,
):
    return get_maintenance_by_date_range(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
        branch_id=branch_id,
    )


def get_report_maintenance_total_by_date_range(
    db: Session,
    company_id: UUID,
    start_date: date,
    end_date: date,
    branch_id: UUID | None = None,
) -> Decimal:
    return get_maintenance_total_cost_by_date_range(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
        branch_id=branch_id,
    )


def get_vehicle_report_fuel_total(
    db: Session,
    vehicle_id: UUID,
    start_date: date,
    end_date: date,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
) -> Decimal:
    query = (
        db.query(
            func.coalesce(
                func.sum(FuelLog.fuel_cost),
                0,
            )
        )
        .filter(
            FuelLog.vehicle_id == vehicle_id,
            FuelLog.fuel_date >= start_date,
            FuelLog.fuel_date <= end_date,
            FuelLog.is_active.is_(True),
        )
    )

    if company_id is not None:
        query = query.filter(
            FuelLog.company_id == company_id,
        )

    if branch_id is not None:
        query = query.filter(
            FuelLog.branch_id == branch_id,
        )

    total = query.scalar()

    return Decimal(total)


def get_vehicle_report_maintenance_total(
    db: Session,
    vehicle_id: UUID,
    start_date: date,
    end_date: date,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
) -> Decimal:
    query = (
        db.query(
            func.coalesce(
                func.sum(MaintenanceRecord.cost),
                0,
            )
        )
        .filter(
            MaintenanceRecord.vehicle_id == vehicle_id,
            MaintenanceRecord.service_date >= start_date,
            MaintenanceRecord.service_date <= end_date,
            MaintenanceRecord.is_active.is_(True),
        )
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


def get_driver_report_trip_count(
    db: Session,
    driver_id: UUID,
    start_date: date,
    end_date: date,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
) -> int:
    start_datetime = datetime.combine(
        start_date,
        time.min,
    )

    end_datetime = datetime.combine(
        end_date + timedelta(days=1),
        time.min,
    )

    query = (
        db.query(func.count(Trip.id))
        .filter(
            Trip.driver_id == driver_id,
            Trip.created_at >= start_datetime,
            Trip.created_at < end_datetime,
            Trip.is_active.is_(True),
        )
    )

    if company_id is not None:
        query = query.filter(
            Trip.company_id == company_id,
        )

    if branch_id is not None:
        query = query.filter(
            Trip.branch_id == branch_id,
        )

    return query.scalar() or 0


def get_vehicle_report_trip_count(
    db: Session,
    vehicle_id: UUID,
    start_date: date,
    end_date: date,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
) -> int:
    start_datetime = datetime.combine(
        start_date,
        time.min,
    )

    end_datetime = datetime.combine(
        end_date + timedelta(days=1),
        time.min,
    )

    query = (
        db.query(func.count(Trip.id))
        .filter(
            Trip.vehicle_id == vehicle_id,
            Trip.created_at >= start_datetime,
            Trip.created_at < end_datetime,
            Trip.is_active.is_(True),
        )
    )

    if company_id is not None:
        query = query.filter(
            Trip.company_id == company_id,
        )

    if branch_id is not None:
        query = query.filter(
            Trip.branch_id == branch_id,
        )

    return query.scalar() or 0


def get_report_data(
    db: Session,
    company_id: UUID,
    start_date: date,
    end_date: date,
    branch_id: UUID | None = None,
):
    company = get_report_company(
        db=db,
        company_id=company_id,
    )

    if not company:
        return None

    vehicles = get_report_all_vehicles(
        db=db,
        company_id=company_id,
        branch_id=branch_id,
    )

    active_vehicles = get_report_active_vehicles(
        db=db,
        company_id=company_id,
        branch_id=branch_id,
    )

    inactive_vehicles = get_report_inactive_vehicles(
        db=db,
        company_id=company_id,
        branch_id=branch_id,
    )

    drivers = get_report_drivers(
        db=db,
        company_id=company_id,
        branch_id=branch_id,
    )

    trips = get_report_trips(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
        branch_id=branch_id,
    )

    fuel_logs = get_report_fuel_logs(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
        branch_id=branch_id,
    )

    maintenance_records = get_report_maintenance_records(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
        branch_id=branch_id,
    )

    fuel_total = get_report_fuel_total(
        fuel_logs=fuel_logs,
    )

    maintenance_total = get_report_maintenance_total_by_date_range(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
        branch_id=branch_id,
    )

    return {
        "company": company,
        "period": {
            "start_date": start_date,
            "end_date": end_date,
        },
        "branch_id": branch_id,
        "vehicles": vehicles,
        "active_vehicles": active_vehicles,
        "inactive_vehicles": inactive_vehicles,
        "drivers": drivers,
        "trips": trips,
        "fuel_logs": fuel_logs,
        "maintenance_records": maintenance_records,
        "summary": {
            "total_vehicles": len(vehicles),
            "active_vehicles": len(active_vehicles),
            "inactive_vehicles": len(inactive_vehicles),
            "total_drivers": len(drivers),
            "total_trips": len(trips),
            "total_fuel_expense": fuel_total,
            "total_maintenance_expense": maintenance_total,
            "total_expense": fuel_total + maintenance_total,
        },
    }
