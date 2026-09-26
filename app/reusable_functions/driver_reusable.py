from sqlalchemy.orm import Session
from app.models.driver import Driver
from uuid import UUID

def get_driver_by_license_number_query(db: Session, company_id: UUID, license_number: str):

    return (db.query(Driver).filter(Driver.company_id == company_id, Driver.license_number == license_number, Driver.is_active.is_(True)).first())


def get_driver_by_license_number_admin_query(db: Session, license_number: str):

    return (db.query(Driver).filter(Driver.license_number == license_number, Driver.is_active.is_(True)).first())


def get_driver_by_id_query(db: Session, company_id: UUID, driver_id: UUID):

    return (db.query(Driver).filter(Driver.company_id == company_id, Driver.id == driver_id, Driver.is_active.is_(True)).first())


def get_active_driver_by_id_admin_query(db: Session, driver_id: UUID):

    return (db.query(Driver).filter(Driver.id == driver_id, Driver.is_active.is_(True)).first())


def get_driver_by_id_admin_query(db: Session, driver_id: UUID):

    return (db.query(Driver).filter(Driver.id == driver_id).first())


def get_all_drivers_query(db: Session, company_id: UUID):

    return (
        db.query(Driver)
        .filter(
            Driver.company_id == company_id
        )
        .all()
    )


def get_all_drivers_admin_query(db: Session):

    return (db.query(Driver).all())


def get_drivers_by_ids_query(db: Session, driver_ids: list[UUID]):

    return (db.query(Driver).filter(Driver.id.in_(driver_ids)).all())


def get_driver_by_phone_query(db: Session,phone: str):

    return (db.query(Driver).filter(Driver.phone == phone, Driver.is_active.is_(True)).first())