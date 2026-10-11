from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.security.authorization import (
    get_current_user,
    require_roles,
)

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


MANAGEMENT_ROLES = [
    "GLOBAL_ADMIN",
    "SUPER_ADMIN",
    "BRANCH_ADMIN",
]

OPERATIONAL_ROLES = [
    "GLOBAL_ADMIN",
    "SUPER_ADMIN",
    "BRANCH_ADMIN",
    "DRIVER",
]


def _get_company_id(
    current_user,
    company_id: UUID | None = None,
) -> UUID:
    user_company_id = getattr(
        current_user,
        "company_id",
        None,
    )

    if user_company_id is not None:
        if (
            company_id is not None
            and company_id != user_company_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this company",
            )

        return user_company_id

    if company_id is not None:
        return company_id

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="company_id is required for this user",
    )


def _handle_service_result(result):
    if not isinstance(result, dict):
        return result

    if result.get("success") is False:
        raise HTTPException(
            status_code=result.get(
                "status_code",
                status.HTTP_400_BAD_REQUEST,
            ),
            detail=result.get(
                "message",
                "Trip operation failed",
            ),
        )

    return result.get("data")


@router.post(
    "/",
    response_model=TripResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_roles(
                *MANAGEMENT_ROLES
            )
        )
    ],
)
def create_trip_route(
    trip_data: TripCreate,
    company_id: UUID | None = Query(
        default=None
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    resolved_company_id = _get_company_id(
        current_user=current_user,
        company_id=company_id,
    )

    result = create_trip(
        db=db,
        current_user=current_user,
        company_id=resolved_company_id,
        vehicle_id=trip_data.vehicle_id,
        driver_id=trip_data.driver_id,
        origin=trip_data.origin,
        destination=trip_data.destination,
        cargo_description=trip_data.cargo_description,
        remarks=trip_data.remarks,
    )

    return _handle_service_result(result)


@router.get(
    "/company",
    response_model=list[TripListResponse],
)
def get_company_trips_route(
    company_id: UUID | None = Query(
        default=None
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    resolved_company_id = _get_company_id(
        current_user=current_user,
        company_id=company_id,
    )

    result = get_company_trips(
        db=db,
        current_user=current_user,
        company_id=resolved_company_id,
    )

    return _handle_service_result(result)


@router.get(
    "/vehicle/{vehicle_id}",
    response_model=list[TripListResponse],
)
def get_vehicle_trips_route(
    vehicle_id: UUID,
    company_id: UUID | None = Query(
        default=None
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    resolved_company_id = _get_company_id(
        current_user=current_user,
        company_id=company_id,
    )

    result = get_vehicle_trips(
        db=db,
        current_user=current_user,
        company_id=resolved_company_id,
        vehicle_id=vehicle_id,
    )

    return _handle_service_result(result)


@router.get(
    "/driver/{driver_id}",
    response_model=list[TripListResponse],
)
def get_driver_trips_route(
    driver_id: UUID,
    company_id: UUID | None = Query(
        default=None
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    resolved_company_id = _get_company_id(
        current_user=current_user,
        company_id=company_id,
    )

    result = get_driver_trips(
        db=db,
        current_user=current_user,
        company_id=resolved_company_id,
        driver_id=driver_id,
    )

    return _handle_service_result(result)


@router.get(
    "/status/{trip_status}",
    response_model=list[TripListResponse],
)
def get_trips_status_route(
    trip_status: str,
    company_id: UUID | None = Query(
        default=None
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    resolved_company_id = _get_company_id(
        current_user=current_user,
        company_id=company_id,
    )

    result = get_trips_by_status(
        db=db,
        current_user=current_user,
        company_id=resolved_company_id,
        status_value=trip_status,
    )

    return _handle_service_result(result)


@router.get(
    "/date-range",
    response_model=list[TripListResponse],
)
def get_trips_date_range_route(
    start_date: date = Query(...),
    end_date: date = Query(...),
    company_id: UUID | None = Query(
        default=None
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be greater than end_date",
        )

    resolved_company_id = _get_company_id(
        current_user=current_user,
        company_id=company_id,
    )

    result = get_trips_by_date_range(
        db=db,
        current_user=current_user,
        company_id=resolved_company_id,
        start_date=start_date,
        end_date=end_date,
    )

    return _handle_service_result(result)


@router.get(
    "/{trip_id}",
    response_model=TripResponse,
)
def get_trip_route(
    trip_id: UUID,
    company_id: UUID | None = Query(
        default=None
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    resolved_company_id = _get_company_id(
        current_user=current_user,
        company_id=company_id,
    )

    result = get_trip(
        db=db,
        current_user=current_user,
        company_id=resolved_company_id,
        trip_id=trip_id,
    )

    return _handle_service_result(result)


@router.put(
    "/{trip_id}",
    response_model=TripResponse,
    dependencies=[
        Depends(
            require_roles(
                *MANAGEMENT_ROLES
            )
        )
    ],
)
def update_trip_route(
    trip_id: UUID,
    trip_data: TripUpdate,
    company_id: UUID | None = Query(
        default=None
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    resolved_company_id = _get_company_id(
        current_user=current_user,
        company_id=company_id,
    )

    result = update_trip(
        db=db,
        current_user=current_user,
        company_id=resolved_company_id,
        trip_id=trip_id,
        origin=trip_data.origin,
        destination=trip_data.destination,
        cargo_description=trip_data.cargo_description,
        remarks=trip_data.remarks,
    )

    return _handle_service_result(result)


@router.patch(
    "/{trip_id}/start",
    response_model=TripResponse,
    dependencies=[
        Depends(
            require_roles(
                *OPERATIONAL_ROLES
            )
        )
    ],
)
def start_trip_route(
    trip_id: UUID,
    company_id: UUID | None = Query(
        default=None
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    resolved_company_id = _get_company_id(
        current_user=current_user,
        company_id=company_id,
    )

    result = start_trip(
        db=db,
        current_user=current_user,
        company_id=resolved_company_id,
        trip_id=trip_id,
    )

    return _handle_service_result(result)


@router.patch(
    "/{trip_id}/complete",
    response_model=TripResponse,
    dependencies=[
        Depends(
            require_roles(
                *OPERATIONAL_ROLES
            )
        )
    ],
)
def complete_trip_route(
    trip_id: UUID,
    company_id: UUID | None = Query(
        default=None
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    resolved_company_id = _get_company_id(
        current_user=current_user,
        company_id=company_id,
    )

    result = complete_trip(
        db=db,
        current_user=current_user,
        company_id=resolved_company_id,
        trip_id=trip_id,
    )

    return _handle_service_result(result)


@router.patch(
    "/{trip_id}/cancel",
    response_model=TripResponse,
    dependencies=[
        Depends(
            require_roles(
                *OPERATIONAL_ROLES
            )
        )
    ],
)
def cancel_trip_route(
    trip_id: UUID,
    company_id: UUID | None = Query(
        default=None
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    resolved_company_id = _get_company_id(
        current_user=current_user,
        company_id=company_id,
    )

    result = cancel_trip(
        db=db,
        current_user=current_user,
        company_id=resolved_company_id,
        trip_id=trip_id,
    )

    return _handle_service_result(result)


@router.delete(
    "/{trip_id}",
    response_model=TripResponse,
    dependencies=[
        Depends(
            require_roles(
                *MANAGEMENT_ROLES
            )
        )
    ],
)
def delete_trip_route(
    trip_id: UUID,
    company_id: UUID | None = Query(
        default=None
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    ),
):
    resolved_company_id = _get_company_id(
        current_user=current_user,
        company_id=company_id,
    )

    result = delete_trip(
        db=db,
        current_user=current_user,
        company_id=resolved_company_id,
        trip_id=trip_id,
    )

    return _handle_service_result(result)