from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date, datetime, timezone
from app.models.trip import Trip, TripStatus
from app.reusable_functions.trip_reusable import (
    create_record, get_by_id, get_by_company, get_by_vehicle, get_by_driver, get_by_status,
    get_by_date_range, get_by_vehicle_and_date_range, get_by_driver_and_date_range, update_record, delete_record
)

from app.reusable_functions.company_reusable import (
    get_company_by_id_query,
)

from app.reusable_functions.vehicle_reusable import (
    get_vehicle_by_id_query,
)

from app.reusable_functions.driver_reusable import (
    get_driver_by_id_query,
)

from app.reusable_functions.user_reusable import (
    get_user_by_id_query,
)

from app.reusable_functions.drivervehicleassignment_reusable import (
    get_active_assignment_by_vehicle_id_query,
)

def create_trip(
    db: Session,
    company_id: UUID,
    vehicle_id: UUID,
    driver_id: UUID,
    created_by: UUID,
    origin: str,
    destination: str,
    cargo_description: str | None = None,
    remarks: str | None = None,
):

    company = get_company_by_id_query(
        db=db,
        company_id=company_id,
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": None
        }

    vehicle = get_vehicle_by_id_query(
        db=db,
        company_id=company_id,
        vehicle_id=vehicle_id,
    )

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found, inactive, or does not belong to this company",
            "data": None
        }

    driver = get_driver_by_id_query(
        db=db,
        company_id=company_id,
        driver_id=driver_id,
    )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found, inactive, or does not belong to this company",
            "data": None
        }

    # ---------------------------------------------------------
    # CHECK ACTIVE DRIVER-VEHICLE ASSIGNMENT
    # ---------------------------------------------------------

    active_assignment = get_active_assignment_by_vehicle_id_query(
        db=db,
        vehicle_id=vehicle_id,
    )

    # Vehicle has no active driver
    if not active_assignment:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "VEHICLE_HAS_NO_DRIVER",
            "message": "This vehicle does not have an active driver assigned.",
            "data": None
        }

    # Selected driver is not the driver assigned to this vehicle
    if active_assignment.driver_id != driver_id:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "DRIVER_NOT_ASSIGNED_TO_VEHICLE",
            "message": "The selected driver is not assigned to this vehicle.",
            "data": None
        }

    # ---------------------------------------------------------
    # CHECK USER
    # ---------------------------------------------------------

    user = get_user_by_id_query(
        db=db,
        user_id=created_by,
    )

    if not user:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "USER_NOT_FOUND",
            "message": "User not found or inactive",
            "data": None
        }

    if user.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "USER_COMPANY_MISMATCH",
            "message": "User does not belong to this company",
            "data": None
        }

    # ---------------------------------------------------------
    # CREATE TRIP
    # ---------------------------------------------------------

    trip = Trip(
        company_id=company_id,
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        created_by=created_by,
        origin=origin,
        destination=destination,
        cargo_description=cargo_description,
        remarks=remarks,
        status=TripStatus.CREATED,
    )

    try:
        trip = create_record(
            db=db,
            trip=trip,
        )

        return {
            "success": True,
            "status_code": status.HTTP_201_CREATED,
            "code": "TRIP_CREATED",
            "message": "Trip created successfully",
            "data": trip
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "TRIP_CREATION_FAILED",
            "message": "Trip could not be created",
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


def get_trip(
    db: Session,
    company_id: UUID,
    trip_id: UUID,
):

    company = get_company_by_id_query(
        db=db,
        company_id=company_id,
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": None
        }

    trip = get_by_id(
        db=db,
        trip_id=trip_id,
    )

    if not trip:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "TRIP_NOT_FOUND",
            "message": "Trip not found",
            "data": None
        }

    if trip.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "TRIP_COMPANY_MISMATCH",
            "message": "Trip does not belong to this company",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "TRIP_FOUND",
        "message": "Trip found successfully",
        "data": trip
    }



def get_company_trips(
    db: Session,
    company_id: UUID,
):

    company = get_company_by_id_query(
        db=db,
        company_id=company_id,
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": None
        }

    trips = get_by_company(
        db=db,
        company_id=company_id,
    )

    if not trips:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_TRIPS_FOUND",
            "message": "No trips found for this company",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "TRIPS_FOUND",
        "message": "Company trips retrieved successfully",
        "data": trips
    }



def get_vehicle_trips(
    db: Session,
    company_id: UUID,
    vehicle_id: UUID,
):

    company = get_company_by_id_query(
        db=db,
        company_id=company_id,
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": None
        }

    vehicle = get_vehicle_by_id_query(
        db=db,
        company_id=company_id,
        vehicle_id=vehicle_id,
    )

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found, inactive, or does not belong to this company",
            "data": None
        }

    trips = get_by_vehicle(
        db=db,
        vehicle_id=vehicle_id,
    )

    if not trips:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_TRIPS_FOUND",
            "message": "No trips found for this vehicle",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "VEHICLE_TRIPS_FOUND",
        "message": "Vehicle trips retrieved successfully",
        "data": trips
    }


def get_driver_trips(
    db: Session,
    company_id: UUID,
    driver_id: UUID,
):

    company = get_company_by_id_query(
        db=db,
        company_id=company_id,
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": None
        }

    driver = get_driver_by_id_query(
        db=db,
        company_id=company_id,
        driver_id=driver_id,
    )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found, inactive, or does not belong to this company",
            "data": None
        }

    trips = get_by_driver(
        db=db,
        driver_id=driver_id,
    )

    if not trips:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_TRIPS_FOUND",
            "message": "No trips found for this driver",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DRIVER_TRIPS_FOUND",
        "message": "Driver trips retrieved successfully",
        "data": trips
    }


def get_trips_by_status(
    db: Session,
    company_id: UUID,
    status_value: str,
):

    company = get_company_by_id_query(
        db=db,
        company_id=company_id,
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": None
        }

    valid_statuses = {
        TripStatus.CREATED,
        TripStatus.STARTED,
        TripStatus.COMPLETED,
        TripStatus.CANCELLED,
    }

    if status_value not in valid_statuses:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_TRIP_STATUS",
            "message": "Invalid trip status",
            "data": None
        }

    trips = get_by_status(
        db=db,
        company_id=company_id,
        status=status_value,
    )

    if not trips:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_TRIPS_FOUND",
            "message": "No trips found with the specified status",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "TRIPS_FOUND",
        "message": "Trips retrieved successfully",
        "data": trips
    }


def get_trips_by_date_range(
    db: Session,
    company_id: UUID,
    start_date: date,
    end_date: date,
):

    company = get_company_by_id_query(
        db=db,
        company_id=company_id,
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": None
        }

    if start_date > end_date:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DATE_RANGE",
            "message": "Start date cannot be later than end date",
            "data": None
        }

    trips = get_by_date_range(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
    )

    if not trips:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_TRIPS_FOUND",
            "message": "No trips found for the specified date range",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "TRIPS_FOUND",
        "message": "Trips retrieved successfully",
        "data": trips
    }


def get_vehicle_trips_by_date_range(
    db: Session,
    company_id: UUID,
    vehicle_id: UUID,
    start_date: date,
    end_date: date,
):

    company = get_company_by_id_query(
        db=db,
        company_id=company_id,
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": None
        }

    vehicle = get_vehicle_by_id_query(
        db=db,
        company_id=company_id,
        vehicle_id=vehicle_id,
    )

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found, inactive, or does not belong to this company",
            "data": None
        }

    if start_date > end_date:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DATE_RANGE",
            "message": "Start date cannot be later than end date",
            "data": None
        }

    trips = get_by_vehicle_and_date_range(
        db=db,
        vehicle_id=vehicle_id,
        start_date=start_date,
        end_date=end_date,
    )

    if not trips:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_TRIPS_FOUND",
            "message": "No trips found for this vehicle in the specified date range",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "VEHICLE_TRIPS_FOUND",
        "message": "Vehicle trips retrieved successfully",
        "data": trips
    }


def get_driver_trips_by_date_range(
    db: Session,
    company_id: UUID,
    driver_id: UUID,
    start_date: date,
    end_date: date,
):

    company = get_company_by_id_query(
        db=db,
        company_id=company_id,
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": None
        }

    driver = get_driver_by_id_query(
        db=db,
        company_id=company_id,
        driver_id=driver_id,
    )

    if not driver:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DRIVER_NOT_FOUND",
            "message": "Driver not found, inactive, or does not belong to this company",
            "data": None
        }

    if start_date > end_date:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DATE_RANGE",
            "message": "Start date cannot be later than end date",
            "data": None
        }

    trips = get_by_driver_and_date_range(
        db=db,
        driver_id=driver_id,
        start_date=start_date,
        end_date=end_date,
    )

    if not trips:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_TRIPS_FOUND",
            "message": "No trips found for this driver in the specified date range",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DRIVER_TRIPS_FOUND",
        "message": "Driver trips retrieved successfully",
        "data": trips
    }


def update_trip(
    db: Session,
    company_id: UUID,
    trip_id: UUID,
    origin: str | None = None,
    destination: str | None = None,
    cargo_description: str | None = None,
    remarks: str | None = None,
):

    company = get_company_by_id_query(
        db=db,
        company_id=company_id,
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": None
        }

    trip = get_by_id(
        db=db,
        trip_id=trip_id,
    )

    if not trip:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "TRIP_NOT_FOUND",
            "message": "Trip not found",
            "data": None
        }

    if trip.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "TRIP_COMPANY_MISMATCH",
            "message": "Trip does not belong to this company",
            "data": None
        }

    if trip.status != TripStatus.CREATED:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "TRIP_UPDATE_NOT_ALLOWED",
            "message": "Only trips with CREATED status can be updated",
            "data": None
        }

    if origin is not None:
        trip.origin = origin

    if destination is not None:
        trip.destination = destination

    if cargo_description is not None:
        trip.cargo_description = cargo_description

    if remarks is not None:
        trip.remarks = remarks

    try:
        trip = update_record(
            db=db,
            trip=trip,
        )

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "TRIP_UPDATED",
            "message": "Trip updated successfully",
            "data": trip
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "TRIP_UPDATE_FAILED",
            "message": "Trip could not be updated",
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


def start_trip(
    db: Session,
    company_id: UUID,
    trip_id: UUID,
):

    company = get_company_by_id_query(
        db=db,
        company_id=company_id,
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": None
        }

    trip = get_by_id(
        db=db,
        trip_id=trip_id,
    )

    if not trip:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "TRIP_NOT_FOUND",
            "message": "Trip not found",
            "data": None
        }

    if trip.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "TRIP_COMPANY_MISMATCH",
            "message": "Trip does not belong to this company",
            "data": None
        }

    if trip.status != TripStatus.CREATED:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "TRIP_START_NOT_ALLOWED",
            "message": "Only trips with CREATED status can be started",
            "data": None
        }

    started_trips = get_by_status(
        db=db,
        company_id=company_id,
        status=TripStatus.STARTED,
    )

    for started_trip in started_trips:

        if started_trip.vehicle_id == trip.vehicle_id:
            return {
                "success": False,
                "status_code": status.HTTP_409_CONFLICT,
                "code": "VEHICLE_ALREADY_ON_TRIP",
                "message": "Vehicle already has an active trip",
                "data": None
            }

        if started_trip.driver_id == trip.driver_id:
            return {
                "success": False,
                "status_code": status.HTTP_409_CONFLICT,
                "code": "DRIVER_ALREADY_ON_TRIP",
                "message": "Driver already has an active trip",
                "data": None
            }

    trip.status = TripStatus.STARTED
    trip.actual_start = datetime.now(timezone.utc)

    try:
        trip = update_record(
            db=db,
            trip=trip,
        )

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "TRIP_STARTED",
            "message": "Trip started successfully",
            "data": trip
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "TRIP_START_FAILED",
            "message": "Trip could not be started",
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


def complete_trip(
    db: Session,
    company_id: UUID,
    trip_id: UUID,
):

    company = get_company_by_id_query(
        db=db,
        company_id=company_id,
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": None
        }

    trip = get_by_id(
        db=db,
        trip_id=trip_id,
    )

    if not trip:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "TRIP_NOT_FOUND",
            "message": "Trip not found",
            "data": None
        }

    if trip.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "TRIP_COMPANY_MISMATCH",
            "message": "Trip does not belong to this company",
            "data": None
        }

    if trip.status != TripStatus.STARTED:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "TRIP_COMPLETION_NOT_ALLOWED",
            "message": "Only started trips can be completed",
            "data": None
        }

    trip.status = TripStatus.COMPLETED
    trip.actual_end = datetime.now(timezone.utc)
    try:
        trip = update_record(
            db=db,
            trip=trip,
        )

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "TRIP_COMPLETED",
            "message": "Trip completed successfully",
            "data": trip
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "TRIP_COMPLETION_FAILED",
            "message": "Trip could not be completed",
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


def cancel_trip(
    db: Session,
    company_id: UUID,
    trip_id: UUID,
):

    company = get_company_by_id_query(
        db=db,
        company_id=company_id,
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": None
        }

    trip = get_by_id(
        db=db,
        trip_id=trip_id,
    )

    if not trip:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "TRIP_NOT_FOUND",
            "message": "Trip not found",
            "data": None
        }

    if trip.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "TRIP_COMPANY_MISMATCH",
            "message": "Trip does not belong to this company",
            "data": None
        }

    if trip.status not in (
        TripStatus.CREATED,
        TripStatus.STARTED,
    ):
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "TRIP_CANCELLATION_NOT_ALLOWED",
            "message": "Only created or started trips can be cancelled",
            "data": None
        }

    trip.status = TripStatus.CANCELLED

    try:
        trip = update_record(
            db=db,
            trip=trip,
        )

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "TRIP_CANCELLED",
            "message": "Trip cancelled successfully",
            "data": trip
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "TRIP_CANCELLATION_FAILED",
            "message": "Trip could not be cancelled",
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



def delete_trip(
    db: Session,
    company_id: UUID,
    trip_id: UUID,
):

    company = get_company_by_id_query(
        db=db,
        company_id=company_id,
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": None
        }

    trip = get_by_id(
        db=db,
        trip_id=trip_id,
    )

    if not trip:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "TRIP_NOT_FOUND",
            "message": "Trip not found",
            "data": None
        }

    if trip.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "TRIP_COMPANY_MISMATCH",
            "message": "Trip does not belong to this company",
            "data": None
        }

    if trip.status != TripStatus.CREATED:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "TRIP_DELETE_NOT_ALLOWED",
            "message": "Only created trips can be deleted",
            "data": None
        }

    try:
        delete_record(
            db=db,
            trip=trip,
        )

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "TRIP_DELETED",
            "message": "Trip deleted successfully",
            "data": None
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "TRIP_DELETE_FAILED",
            "message": "Trip could not be deleted",
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


    