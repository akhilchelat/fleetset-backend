from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.trip_schema import (
    TripCreate,
    TripUpdate,
    TripResponse,
    TripListResponse,
)
from app.services.trip_service import (
    create_trip,
    get_trip,
    get_company_trips,
    get_vehicle_trips,
    get_driver_trips,
    get_trips_by_status,
    get_trips_by_date_range,
    get_vehicle_trips_by_date_range,
    get_driver_trips_by_date_range,
    update_trip,
    start_trip,
    complete_trip,
    cancel_trip,
    delete_trip,
)


router = APIRouter(
    prefix="/trips",
    tags=["Trips"],
)


@router.post(
    "/{company_id}",
    response_model=TripResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_trip_route(
    company_id: UUID,
    trip: TripCreate,
    db: Session = Depends(get_db),
):
    result = create_trip(
        db=db,
        company_id=company_id,
        vehicle_id=trip.vehicle_id,
        driver_id=trip.driver_id,
        created_by=trip.created_by,
        origin=trip.origin,
        destination=trip.destination,
        cargo_description=trip.cargo_description,
        remarks=trip.remarks,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/all",
    response_model=list[TripListResponse],
    status_code=status.HTTP_200_OK,
)
def get_company_trips_route(
    company_id: UUID,
    db: Session = Depends(get_db),
):
    result = get_company_trips(
        db=db,
        company_id=company_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/vehicle/{vehicle_id}",
    response_model=list[TripListResponse],
    status_code=status.HTTP_200_OK,
)
def get_vehicle_trips_route(
    company_id: UUID,
    vehicle_id: UUID,
    db: Session = Depends(get_db),
):
    result = get_vehicle_trips(
        db=db,
        company_id=company_id,
        vehicle_id=vehicle_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/driver/{driver_id}",
    response_model=list[TripListResponse],
    status_code=status.HTTP_200_OK,
)
def get_driver_trips_route(
    company_id: UUID,
    driver_id: UUID,
    db: Session = Depends(get_db),
):
    result = get_driver_trips(
        db=db,
        company_id=company_id,
        driver_id=driver_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/status/{status_value}",
    response_model=list[TripListResponse],
    status_code=status.HTTP_200_OK,
)
def get_trips_by_status_route(
    company_id: UUID,
    status_value: str,
    db: Session = Depends(get_db),
):
    result = get_trips_by_status(
        db=db,
        company_id=company_id,
        status_value=status_value,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/date-range",
    response_model=list[TripListResponse],
    status_code=status.HTTP_200_OK,
)
def get_trips_by_date_range_route(
    company_id: UUID,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
):
    result = get_trips_by_date_range(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/vehicle/{vehicle_id}/date-range",
    response_model=list[TripListResponse],
    status_code=status.HTTP_200_OK,
)
def get_vehicle_trips_by_date_range_route(
    company_id: UUID,
    vehicle_id: UUID,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
):
    result = get_vehicle_trips_by_date_range(
        db=db,
        company_id=company_id,
        vehicle_id=vehicle_id,
        start_date=start_date,
        end_date=end_date,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/driver/{driver_id}/date-range",
    response_model=list[TripListResponse],
    status_code=status.HTTP_200_OK,
)
def get_driver_trips_by_date_range_route(
    company_id: UUID,
    driver_id: UUID,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
):
    result = get_driver_trips_by_date_range(
        db=db,
        company_id=company_id,
        driver_id=driver_id,
        start_date=start_date,
        end_date=end_date,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/{trip_id}",
    response_model=TripResponse,
    status_code=status.HTTP_200_OK,
)
def get_trip_route(
    company_id: UUID,
    trip_id: UUID,
    db: Session = Depends(get_db),
):
    result = get_trip(
        db=db,
        company_id=company_id,
        trip_id=trip_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.put(
    "/{company_id}/{trip_id}",
    response_model=TripResponse,
    status_code=status.HTTP_200_OK,
)
def update_trip_route(
    company_id: UUID,
    trip_id: UUID,
    trip: TripUpdate,
    db: Session = Depends(get_db),
):
    result = update_trip(
        db=db,
        company_id=company_id,
        trip_id=trip_id,
        origin=trip.origin,
        destination=trip.destination,
        cargo_description=trip.cargo_description,
        remarks=trip.remarks,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.patch(
    "/{company_id}/{trip_id}/start",
    response_model=TripResponse,
    status_code=status.HTTP_200_OK,
)
def start_trip_route(
    company_id: UUID,
    trip_id: UUID,
    db: Session = Depends(get_db),
):
    result = start_trip(
        db=db,
        company_id=company_id,
        trip_id=trip_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.patch(
    "/{company_id}/{trip_id}/complete",
    response_model=TripResponse,
    status_code=status.HTTP_200_OK,
)
def complete_trip_route(
    company_id: UUID,
    trip_id: UUID,
    db: Session = Depends(get_db),
):
    result = complete_trip(
        db=db,
        company_id=company_id,
        trip_id=trip_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.patch(
    "/{company_id}/{trip_id}/cancel",
    response_model=TripResponse,
    status_code=status.HTTP_200_OK,
)
def cancel_trip_route(
    company_id: UUID,
    trip_id: UUID,
    db: Session = Depends(get_db),
):
    result = cancel_trip(
        db=db,
        company_id=company_id,
        trip_id=trip_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.delete(
    "/{company_id}/{trip_id}",
    status_code=status.HTTP_200_OK,
)
def delete_trip_route(
    company_id: UUID,
    trip_id: UUID,
    db: Session = Depends(get_db),
):
    result = delete_trip(
        db=db,
        company_id=company_id,
        trip_id=trip_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return {
        "message": result["message"]
    }

