from datetime import date
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.driver import Driver
from app.reusable_functions.company_reusable import(get_company_by_id_query)
from app.reusable_functions.driver_reusable import(get_driver_by_license_number_query,
                                                   get_driver_by_id_query,
                                                   get_all_drivers_query,
                                                   get_all_drivers_admin_query,
                                                   get_driver_by_license_number_admin_query,
                                                   get_active_driver_by_id_admin_query,
                                                   get_driver_by_phone_query,
                                                   get_driver_by_id_admin_query,
                                                   get_drivers_by_ids_query)

def create_driver(
    db: Session,
    company_id: UUID,
    first_name: str,
    last_name: str | None,
    phone: str,
    address: str | None,
    license_number: str,
    license_expiry: date | None,
    experience_years: int | None,
    emergency_contact: str | None
):

    company = get_company_by_id_query(
        db,
        company_id
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found",
            "data": None
        }

    driver = get_driver_by_license_number_admin_query(
        db,
        license_number
    )

    if driver:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "LICENSE_NUMBER_ALREADY_EXISTS",
            "message": "License number already exists",
            "data": None
        }

    phone_exists = get_driver_by_phone_query(
        db,
        phone
    )

    if phone_exists:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "PHONE_ALREADY_EXISTS",
            "message": "Phone number already exists",
            "data": None
        }

    new_driver = Driver(
        company_id=company.id,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        address=address,
        license_number=license_number,
        license_expiry=license_expiry,
        experience_years=experience_years,
        emergency_contact=emergency_contact
    )

    db.add(new_driver)

    try:
        db.commit()
        db.refresh(new_driver)

        return {
            "success": True,
            "status_code": status.HTTP_201_CREATED,
            "code": "DRIVER_CREATED",
            "message": "Driver created successfully",
            "data": new_driver
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "DRIVER_ALREADY_EXISTS",
            "message": "Driver already exists",
            "data": None
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None
        }
    

def find_driver_by_id(
    db: Session,
    company_id: UUID,
    driver_id: UUID
):

    company = get_company_by_id_query(
        db,
        company_id
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found",
            "data": None
        }

    driver = get_driver_by_id_query(
        db,
        company_id,
        driver_id
    )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DRIVER_FOUND",
        "message": "Driver found successfully",
        "data": driver
    }

# global admin 
def find_active_driver_by_id( 
    db: Session,
    driver_id: UUID
):

    driver = get_active_driver_by_id_admin_query(
        db,
        driver_id
    )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DRIVER_FOUND",
        "message": "Driver found successfully",
        "data": driver
    }


def find_driver_by_license_number(
    db: Session,
    company_id: UUID,
    license_number: str
):

    company = get_company_by_id_query(
        db,
        company_id
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found",
            "data": None
        }

    driver = get_driver_by_license_number_query(
        db,
        company_id,
        license_number
    )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DRIVER_FOUND",
        "message": "Driver found successfully",
        "data": driver
    }


# global admin
def find_driver_by_license_number_admin(
    db: Session,
    license_number: str
):

    driver = get_driver_by_license_number_admin_query(
        db,
        license_number
    )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DRIVER_FOUND",
        "message": "Driver found successfully",
        "data": driver
    }


def get_all_drivers(
    db: Session,
    company_id: UUID
):

    company = get_company_by_id_query(
        db,
        company_id
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found",
            "data": None
        }

    drivers = get_all_drivers_query(
        db,
        company_id
    )

    if not drivers:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_DRIVERS_FOUND",
            "message": "No drivers found",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DRIVERS_FOUND",
        "message": "Drivers retrieved successfully",
        "data": drivers
    }


# global admin
def get_all_drivers_admin(
    db: Session
):

    drivers = get_all_drivers_admin_query(
        db
    )

    if not drivers:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_DRIVERS_FOUND",
            "message": "No drivers found",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DRIVERS_FOUND",
        "message": "Drivers retrieved successfully",
        "data": drivers
    }



def update_driver(
    db: Session,
    company_id: UUID,
    driver_id: UUID,
    first_name: str = None,
    last_name: str = None,
    phone: str = None,
    address: str = None,
    license_number: str = None,
    license_expiry: date = None,
    experience_years: int = None,
    emergency_contact: str = None,
    driver_status: str = None
):

    company = get_company_by_id_query(
        db,
        company_id
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found",
            "data": None
        }

    driver = get_driver_by_id_query(
        db,
        company_id,
        driver_id
    )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found",
            "data": None
        }

    if license_number is not None:

        existing_driver = get_driver_by_license_number_admin_query(
            db,
            license_number
        )

        if existing_driver and existing_driver.id != driver.id:
            return {
                "success": False,
                "status_code": status.HTTP_409_CONFLICT,
                "code": "LICENSE_NUMBER_ALREADY_EXISTS",
                "message": "License number already exists",
                "data": None
            }

        driver.license_number = license_number

    if phone is not None:

        existing_driver = get_driver_by_phone_query(
            db,
            phone
        )

        if existing_driver and existing_driver.id != driver.id:
            return {
                "success": False,
                "status_code": status.HTTP_409_CONFLICT,
                "code": "PHONE_NUMBER_ALREADY_EXISTS",
                "message": "Phone number already exists",
                "data": None
            }

        driver.phone = phone

    if first_name is not None:
        driver.first_name = first_name

    if last_name is not None:
        driver.last_name = last_name

    if address is not None:
        driver.address = address

    if license_expiry is not None:
        driver.license_expiry = license_expiry

    if experience_years is not None:
        driver.experience_years = experience_years

    if emergency_contact is not None:
        driver.emergency_contact = emergency_contact

    # FIXED
    if driver_status is not None:
        driver.status = driver_status

    try:
        db.commit()
        db.refresh(driver)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "DRIVER_UPDATED",
            "message": "Driver updated successfully",
            "data": driver
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "DRIVER_UPDATE_CONFLICT",
            "message": "Driver update conflicts with existing data",
            "data": None
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None
        }
        

def activate_driver(
    db: Session,
    driver_id: UUID
):

    driver = get_driver_by_id_admin_query(
        db,
        driver_id
    )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found",
            "data": None
        }

    if driver.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "DRIVER_ALREADY_ACTIVE",
            "message": "Driver already active",
            "data": None
        }

    driver.is_active = True

    try:
        db.commit()
        db.refresh(driver)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "DRIVER_ACTIVATED",
            "message": "Driver activated successfully",
            "data": driver
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None
        } 


def deactivate_driver(
    db: Session,
    driver_id: UUID
):

    driver = get_driver_by_id_admin_query(
        db,
        driver_id
    )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found",
            "data": None
        }

    if not driver.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "DRIVER_ALREADY_INACTIVE",
            "message": "Driver already inactive",
            "data": None
        }

    driver.is_active = False

    try:
        db.commit()
        db.refresh(driver)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "DRIVER_DEACTIVATED",
            "message": "Driver deactivated successfully",
            "data": driver
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None
        }  


def bulk_activate_drivers(
    db: Session,
    driver_ids: list[UUID]
):

    drivers = get_drivers_by_ids_query(
        db,
        driver_ids
    )

    if not drivers:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_DRIVERS_FOUND",
            "message": "No drivers found",
            "data": None
        }

    already_active_drivers = []
    activated_drivers = []

    for driver in drivers:

        if driver.is_active:

            already_active_drivers.append(
                {
                    "id": str(driver.id),
                    "name": f"{driver.first_name} {driver.last_name or ''}".strip()
                }
            )

            continue

        driver.is_active = True

        activated_drivers.append(
            {
                "id": str(driver.id),
                "name": f"{driver.first_name} {driver.last_name or ''}".strip()
            }
        )

    if len(already_active_drivers) == len(drivers):
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "ALL_DRIVERS_ALREADY_ACTIVE",
            "message": "All drivers are already active",
            "data": already_active_drivers
        }

    try:
        db.commit()

        for driver in drivers:
            db.refresh(driver)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "DRIVERS_ACTIVATED",
            "message": "Drivers activated successfully",
            "data": {
                "activated_drivers": activated_drivers,
                "already_active_drivers": already_active_drivers
            }
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None
        }
    

def bulk_deactivate_drivers(
    db: Session,
    driver_ids: list[UUID]
):

    drivers = get_drivers_by_ids_query(
        db,
        driver_ids
    )

    if not drivers:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_DRIVERS_FOUND",
            "message": "No drivers found",
            "data": None
        }

    already_inactive_drivers = []
    deactivated_drivers = []

    for driver in drivers:

        if not driver.is_active:

            already_inactive_drivers.append(
                {
                    "id": str(driver.id),
                    "name": f"{driver.first_name} {driver.last_name or ''}".strip()
                }
            )

            continue

        driver.is_active = False

        deactivated_drivers.append(
            {
                "id": str(driver.id),
                "name": f"{driver.first_name} {driver.last_name or ''}".strip()
            }
        )

    if len(already_inactive_drivers) == len(drivers):
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "ALL_DRIVERS_ALREADY_INACTIVE",
            "message": "All drivers are already inactive",
            "data": already_inactive_drivers
        }

    try:
        db.commit()

        for driver in drivers:
            db.refresh(driver)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "DRIVERS_DEACTIVATED",
            "message": "Drivers deactivated successfully",
            "data": {
                "deactivated_drivers": deactivated_drivers,
                "already_inactive_drivers": already_inactive_drivers
            }
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong",
            "data": None
        }    