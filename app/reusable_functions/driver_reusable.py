from uuid import UUID

from sqlalchemy.orm import Session

from app.models.driver import Driver
from app.models.user import User


def get_driver_by_license_number_query(
    db: Session,
    company_id: UUID,
    license_number: str,
    branch_id: UUID | None = None,
):
    query = db.query(Driver).filter(
        Driver.company_id == company_id,
        Driver.license_number == license_number,
        Driver.is_active.is_(True),
    )

    if branch_id is not None:
        query = query.filter(
            Driver.branch_id == branch_id
        )

    return query.first()


def get_driver_by_license_number_admin_query(
    db: Session,
    license_number: str,
):
    return (
        db.query(Driver)
        .filter(
            Driver.license_number == license_number,
            Driver.is_active.is_(True),
        )
        .first()
    )


def get_driver_by_id_query(
    db: Session,
    company_id: UUID,
    driver_id: UUID,
    branch_id: UUID | None = None,
):
    query = db.query(Driver).filter(
        Driver.company_id == company_id,
        Driver.id == driver_id,
        Driver.is_active.is_(True),
    )

    if branch_id is not None:
        query = query.filter(
            Driver.branch_id == branch_id
        )

    return query.first()


def get_active_driver_by_id_admin_query(
    db: Session,
    driver_id: UUID,
):
    return (
        db.query(Driver)
        .filter(
            Driver.id == driver_id,
            Driver.is_active.is_(True),
        )
        .first()
    )


def get_driver_by_id_admin_query(
    db: Session,
    driver_id: UUID,
):
    return (
        db.query(Driver)
        .filter(
            Driver.id == driver_id,
        )
        .first()
    )


def get_all_drivers_query(
    db: Session,
    company_id: UUID,
    branch_id: UUID | None = None,
):
    query = db.query(Driver).filter(
        Driver.company_id == company_id,
    )

    if branch_id is not None:
        query = query.filter(
            Driver.branch_id == branch_id,
        )

    return query.all()


def get_all_drivers_admin_query(
    db: Session,
):
    return db.query(Driver).all()


def get_drivers_by_ids_query(
    db: Session,
    driver_ids: list[UUID],
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
):
    query = db.query(Driver).filter(
        Driver.id.in_(driver_ids),
    )

    if company_id is not None:
        query = query.filter(
            Driver.company_id == company_id,
        )

    if branch_id is not None:
        query = query.filter(
            Driver.branch_id == branch_id,
        )

    return query.all()


def get_driver_by_phone_query(
    db: Session,
    phone: str,
    company_id: UUID | None = None,
    branch_id: UUID | None = None,
):
    query = (
        db.query(Driver)
        .join(
            User,
            Driver.user_id == User.id,
        )
        .filter(
            User.phone == phone,
            User.is_active.is_(True),
            Driver.is_active.is_(True),
        )
    )

    if company_id is not None:
        query = query.filter(
            Driver.company_id == company_id,
        )

    if branch_id is not None:
        query = query.filter(
            Driver.branch_id == branch_id,
        )

    return query.first()