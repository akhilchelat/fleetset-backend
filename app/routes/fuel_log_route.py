from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.security.authorization import get_current_user, require_roles

from app.schemas.fuel_log_schema import (
    FuelLogCreate,
    FuelLogUpdate,
    FuelLogResponse,
    FuelExpenseResponse,
    DailyFuelExpenseResponse,
)

from app.services.fuel_log_service import (
    create_fuel_log,
    get_fuel_log,
    get_company_fuel_logs,
    get_vehicle_fuel_logs,
    get_driver_fuel_logs,
    get_fuel_logs_by_date_range,
    get_vehicle_fuel_logs_by_date_range,
    get_driver_fuel_logs_by_date_range,
    update_fuel_log,
    delete_fuel_log,
    get_total_fuel_expense,
    get_daily_fuel_expense,
    get_seven_day_fuel_expense,
    get_thirty_day_fuel_expense,
    get_inactive_company_fuel_logs,
)


router = APIRouter(
    prefix="/fuel-logs",
    tags=["Fuel Logs"],
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


@router.post(
    "/{company_id}",
    response_model=FuelLogResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*OPERATIONAL_ROLES))],
)
def create_fuel_log_route(
    company_id: UUID,
    fuel_data: FuelLogCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.company_id != company_id and current_user.role.name != "GLOBAL_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this company",
        )

    result = create_fuel_log(
        db=db,
        current_user=current_user,
        vehicle_id=fuel_data.vehicle_id,
        driver_id=fuel_data.driver_id,
        fuel_date=fuel_data.fuel_date,
        fuel_cost=fuel_data.fuel_cost,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/all",
    response_model=list[FuelLogResponse],
    status_code=status.HTTP_200_OK,
)
def get_company_fuel_logs_route(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.company_id != company_id and current_user.role.name != "GLOBAL_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this company",
        )

    result = get_company_fuel_logs(
        db=db,
        current_user=current_user,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/inactive",
    response_model=list[FuelLogResponse],
    status_code=status.HTTP_200_OK,
)
def get_inactive_company_fuel_logs_route(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.company_id != company_id and current_user.role.name != "GLOBAL_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this company",
        )

    result = get_inactive_company_fuel_logs(
        db=db,
        current_user=current_user,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/vehicle/{vehicle_id}",
    response_model=list[FuelLogResponse],
    status_code=status.HTTP_200_OK,
)
def get_vehicle_fuel_logs_route(
    company_id: UUID,
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.company_id != company_id and current_user.role.name != "GLOBAL_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this company",
        )

    result = get_vehicle_fuel_logs(
        db=db,
        vehicle_id=vehicle_id,
        current_user=current_user,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/driver/{driver_id}",
    response_model=list[FuelLogResponse],
    status_code=status.HTTP_200_OK,
)
def get_driver_fuel_logs_route(
    company_id: UUID,
    driver_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.company_id != company_id and current_user.role.name != "GLOBAL_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this company",
        )

    result = get_driver_fuel_logs(
        db=db,
        driver_id=driver_id,
        current_user=current_user,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/date-range",
    response_model=list[FuelLogResponse],
    status_code=status.HTTP_200_OK,
)
def get_fuel_logs_by_date_range_route(
    company_id: UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.company_id != company_id and current_user.role.name != "GLOBAL_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this company",
        )

    result = get_fuel_logs_by_date_range(
        db=db,
        current_user=current_user,
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
    response_model=list[FuelLogResponse],
    status_code=status.HTTP_200_OK,
)
def get_vehicle_fuel_logs_by_date_range_route(
    company_id: UUID,
    vehicle_id: UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.company_id != company_id and current_user.role.name != "GLOBAL_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this company",
        )

    result = get_vehicle_fuel_logs_by_date_range(
        db=db,
        vehicle_id=vehicle_id,
        current_user=current_user,
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
    response_model=list[FuelLogResponse],
    status_code=status.HTTP_200_OK,
)
def get_driver_fuel_logs_by_date_range_route(
    company_id: UUID,
    driver_id: UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.company_id != company_id and current_user.role.name != "GLOBAL_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this company",
        )

    result = get_driver_fuel_logs_by_date_range(
        db=db,
        driver_id=driver_id,
        current_user=current_user,
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
    "/{company_id}/expense/total",
    response_model=FuelExpenseResponse,
    status_code=status.HTTP_200_OK,
)
def get_total_fuel_expense_route(
    company_id: UUID,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.company_id != company_id and current_user.role.name != "GLOBAL_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this company",
        )

    if start_date is None:
        start_date = date.min

    if end_date is None:
        end_date = date.today()

    result = get_total_fuel_expense(
        db=db,
        current_user=current_user,
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
    "/{company_id}/expense/daily",
    response_model=DailyFuelExpenseResponse,
    status_code=status.HTTP_200_OK,
)
def get_daily_fuel_expense_route(
    company_id: UUID,
    target_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.company_id != company_id and current_user.role.name != "GLOBAL_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this company",
        )

    result = get_daily_fuel_expense(
        db=db,
        current_user=current_user,
        target_date=target_date,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/expense/7-day",
    response_model=FuelExpenseResponse,
    status_code=status.HTTP_200_OK,
)
def get_7_day_fuel_expense_route(
    company_id: UUID,
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.company_id != company_id and current_user.role.name != "GLOBAL_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this company",
        )

    result = get_seven_day_fuel_expense(
        db=db,
        current_user=current_user,
        target_date=end_date,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/expense/30-day",
    response_model=FuelExpenseResponse,
    status_code=status.HTTP_200_OK,
)
def get_30_day_fuel_expense_route(
    company_id: UUID,
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.company_id != company_id and current_user.role.name != "GLOBAL_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this company",
        )

    result = get_thirty_day_fuel_expense(
        db=db,
        current_user=current_user,
        target_date=end_date,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/{fuel_log_id}",
    response_model=FuelLogResponse,
    status_code=status.HTTP_200_OK,
)
def get_fuel_log_route(
    company_id: UUID,
    fuel_log_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.company_id != company_id and current_user.role.name != "GLOBAL_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this company",
        )

    result = get_fuel_log(
        db=db,
        fuel_log_id=fuel_log_id,
        current_user=current_user,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.put(
    "/{company_id}/{fuel_log_id}",
    response_model=FuelLogResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles(*MANAGEMENT_ROLES))],
)
def update_fuel_log_route(
    company_id: UUID,
    fuel_log_id: UUID,
    fuel_data: FuelLogUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.company_id != company_id and current_user.role.name != "GLOBAL_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this company",
        )

    result = update_fuel_log(
        db=db,
        current_user=current_user,
        fuel_log_id=fuel_log_id,
        fuel_date=fuel_data.fuel_date,
        fuel_cost=fuel_data.fuel_cost,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.delete(
    "/{company_id}/{fuel_log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(*MANAGEMENT_ROLES))],
)
def delete_fuel_log_route(
    company_id: UUID,
    fuel_log_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.company_id != company_id and current_user.role.name != "GLOBAL_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this company",
        )

    result = delete_fuel_log(
        db=db,
        current_user=current_user,
        fuel_log_id=fuel_log_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return None