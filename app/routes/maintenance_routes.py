from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.maintenance_schema import (
    MaintenanceCreate,
    MaintenanceUpdate,
    MaintenanceResponse,
    MaintenanceCostResponse,
    MaintenanceDateRangeCostResponse,
    MaintenanceDailyCostResponse,
    MaintenanceVehicleCostResponse,
)
from app.services.maintenancerecord_service import (
    create_maintenance_record,
    get_maintenance_record,
    get_company_maintenance_records,
    get_vehicle_maintenance_records,
    get_maintenance_records_by_date_range,
    get_vehicle_maintenance_records_by_date_range,
    get_maintenance_records_by_type,
    get_total_maintenance_cost,
    get_vehicle_maintenance_cost,
    get_maintenance_cost_by_date_range,
    get_daily_maintenance_cost,
    get_weekly_maintenance_cost,
    get_monthly_maintenance_cost,
    get_vehicle_maintenance_cost_by_date_range,
    update_maintenance_record,
    delete_maintenance_record,
    get_upcoming_maintenance,
    get_due_maintenance,
)


router = APIRouter(
    prefix="/maintenance",
    tags=["Maintenance"]
)



@router.post(
    "/{company_id}",
    response_model=MaintenanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_maintenance(
    company_id: UUID,
    maintenance_data: MaintenanceCreate,
    db: Session = Depends(get_db),
):

    result = create_maintenance_record(
        db=db,
        company_id=company_id,
        vehicle_id=maintenance_data.vehicle_id,
        recorded_by=maintenance_data.recorded_by,
        maintenance_type=maintenance_data.maintenance_type,
        description=maintenance_data.description,
        garage_name=maintenance_data.garage_name,
        invoice_number=maintenance_data.invoice_number,
        cost=maintenance_data.cost,
        service_date=maintenance_data.service_date,
        next_service_date=maintenance_data.next_service_date,
        odometer_reading=maintenance_data.odometer_reading,
        remarks=maintenance_data.remarks,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/all",
    response_model=list[MaintenanceResponse],
)
def get_all_company_maintenance(
    company_id: UUID,
    db: Session = Depends(get_db),
):

    result = get_company_maintenance_records(
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
    response_model=list[MaintenanceResponse],
)
def get_vehicle_maintenance(
    company_id: UUID,
    vehicle_id: UUID,
    db: Session = Depends(get_db),
):

    result = get_vehicle_maintenance_records(
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
    "/{company_id}/date-range",
    response_model=list[MaintenanceResponse],
)
def get_maintenance_date_range(
    company_id: UUID,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
):

    result = get_maintenance_records_by_date_range(
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
    response_model=list[MaintenanceResponse],
)
def get_vehicle_maintenance_date_range(
    company_id: UUID,
    vehicle_id: UUID,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
):

    result = get_vehicle_maintenance_records_by_date_range(
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
    "/{company_id}/type/{maintenance_type}",
    response_model=list[MaintenanceResponse],
)
def get_maintenance_by_type(
    company_id: UUID,
    maintenance_type: str,
    db: Session = Depends(get_db),
):

    result = get_maintenance_records_by_type(
        db=db,
        company_id=company_id,
        maintenance_type=maintenance_type,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/cost",
    response_model=MaintenanceCostResponse,
)
def get_total_cost(
    company_id: UUID,
    db: Session = Depends(get_db),
):

    result = get_total_maintenance_cost(
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
    "/{company_id}/vehicle/{vehicle_id}/cost",
    response_model=MaintenanceCostResponse,
)
def get_vehicle_total_cost(
    company_id: UUID,
    vehicle_id: UUID,
    db: Session = Depends(get_db),
):

    result = get_vehicle_maintenance_cost(
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
    "/{company_id}/cost/date-range",
    response_model=MaintenanceDateRangeCostResponse,
)
def get_cost_date_range(
    company_id: UUID,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
):

    result = get_maintenance_cost_by_date_range(
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
    "/{company_id}/cost/daily",
    response_model=MaintenanceDailyCostResponse,
)
def get_daily_cost(
    company_id: UUID,
    target_date: date,
    db: Session = Depends(get_db),
):

    result = get_daily_maintenance_cost(
        db=db,
        company_id=company_id,
        target_date=target_date,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/cost/weekly",
    response_model=MaintenanceDateRangeCostResponse,
)
def get_weekly_cost(
    company_id: UUID,
    end_date: date,
    db: Session = Depends(get_db),
):

    result = get_weekly_maintenance_cost(
        db=db,
        company_id=company_id,
        end_date=end_date,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/cost/monthly",
    response_model=MaintenanceDateRangeCostResponse,
)
def get_monthly_cost(
    company_id: UUID,
    end_date: date,
    db: Session = Depends(get_db),
):

    result = get_monthly_maintenance_cost(
        db=db,
        company_id=company_id,
        end_date=end_date,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/vehicle/{vehicle_id}/cost/date-range",
    response_model=MaintenanceVehicleCostResponse,
)
def get_vehicle_cost_date_range(
    company_id: UUID,
    vehicle_id: UUID,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
):

    result = get_vehicle_maintenance_cost_by_date_range(
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
    "/{company_id}/upcoming",
    response_model=list[MaintenanceResponse],
)
def get_upcoming(
    company_id: UUID,
    target_date: date,
    db: Session = Depends(get_db),
):

    result = get_upcoming_maintenance(
        db=db,
        company_id=company_id,
        target_date=target_date,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/due",
    response_model=list[MaintenanceResponse],
)
def get_due(
    company_id: UUID,
    target_date: date,
    db: Session = Depends(get_db),
):

    result = get_due_maintenance(
        db=db,
        company_id=company_id,
        target_date=target_date,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/{maintenance_id}",
    response_model=MaintenanceResponse,
)
def get_single_maintenance(
    company_id: UUID,
    maintenance_id: UUID,
    db: Session = Depends(get_db),
):

    result = get_maintenance_record(
        db=db,
        company_id=company_id,
        maintenance_id=maintenance_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.put(
    "/{company_id}/{maintenance_id}",
    response_model=MaintenanceResponse,
)
def update_maintenance(
    company_id: UUID,
    maintenance_id: UUID,
    maintenance_data: MaintenanceUpdate,
    db: Session = Depends(get_db),
):

    result = update_maintenance_record(
        db=db,
        company_id=company_id,
        maintenance_id=maintenance_id,
        maintenance_type=maintenance_data.maintenance_type,
        description=maintenance_data.description,
        garage_name=maintenance_data.garage_name,
        invoice_number=maintenance_data.invoice_number,
        cost=maintenance_data.cost,
        service_date=maintenance_data.service_date,
        next_service_date=maintenance_data.next_service_date,
        odometer_reading=maintenance_data.odometer_reading,
        remarks=maintenance_data.remarks,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.delete(
    "/{company_id}/{maintenance_id}",
    status_code=status.HTTP_200_OK,
)
def delete_maintenance(
    company_id: UUID,
    maintenance_id: UUID,
    db: Session = Depends(get_db),
):

    result = delete_maintenance_record(
        db=db,
        company_id=company_id,
        maintenance_id=maintenance_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]

