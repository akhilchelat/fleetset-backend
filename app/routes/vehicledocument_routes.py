from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.vehicledocument_schema import (
    VehicleDocumentCreate,
    VehicleDocumentUpdate,
    VehicleDocumentRenew,
    VehicleDocumentResponse,
    VehicleDocumentBulkRequest,
)

from app.services.vehicledocument_service import (
    create_vehicle_document_service,
    update_vehicle_document_service,
    deactivate_vehicle_document_service,
    renew_vehicle_document_service,
    get_vehicle_document_service,
    get_vehicle_documents_service,
    get_company_documents_by_type_service,
    get_active_vehicle_documents_service,
    get_inactive_vehicle_documents_service,
    get_expiring_vehicle_documents_service,
    get_expired_vehicle_documents_service,
    get_vehicle_documents_for_vehicle_service,
)

from app.security.authorization import get_current_user


router = APIRouter(
    prefix="/vehicle-documents",
    tags=["Vehicle Documents"],
)


@router.post(
    "/{company_id}",
    response_model=VehicleDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_vehicle_document(
    company_id: UUID,
    document_data: VehicleDocumentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = create_vehicle_document_service(
        db=db,
        company_id=company_id,
        vehicle_id=document_data.vehicle_id,
        current_user=current_user,
        document_type=document_data.document_type,
        document_number=document_data.document_number,
        issue_date=document_data.issue_date,
        expiry_date=document_data.expiry_date,
        file_url=document_data.file_url,
        remarks=document_data.remarks,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/all",
    response_model=list[VehicleDocumentResponse],
)
def get_all_active_vehicle_documents(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = get_active_vehicle_documents_service(
        db=db,
        company_id=company_id,
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
    response_model=list[VehicleDocumentResponse],
)
def get_all_inactive_vehicle_documents(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = get_inactive_vehicle_documents_service(
        db=db,
        company_id=company_id,
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
    response_model=list[VehicleDocumentResponse],
)
def get_vehicle_documents(
    company_id: UUID,
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = get_vehicle_documents_for_vehicle_service(
        db=db,
        company_id=company_id,
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
    "/{company_id}/type/{document_type}",
    response_model=list[VehicleDocumentResponse],
)
def get_documents_by_type(
    company_id: UUID,
    document_type: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = get_company_documents_by_type_service(
        db=db,
        company_id=company_id,
        document_type=document_type,
        current_user=current_user,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/expiring",
    response_model=list[VehicleDocumentResponse],
)
def get_expiring_documents(
    company_id: UUID,
    days: int = Query(default=30, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = get_expiring_vehicle_documents_service(
        db=db,
        company_id=company_id,
        current_user=current_user,
        days=days,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/expired",
    response_model=list[VehicleDocumentResponse],
)
def get_expired_documents(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = get_expired_vehicle_documents_service(
        db=db,
        company_id=company_id,
        current_user=current_user,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.post(
    "/{company_id}/bulk",
    response_model=list[VehicleDocumentResponse],
)
def get_vehicle_documents_bulk(
    company_id: UUID,
    request_data: VehicleDocumentBulkRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = get_vehicle_documents_service(
        db=db,
        company_id=company_id,
        document_ids=request_data.document_ids,
        current_user=current_user,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}/{document_id}",
    response_model=VehicleDocumentResponse,
)
def get_vehicle_document(
    company_id: UUID,
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = get_vehicle_document_service(
        db=db,
        company_id=company_id,
        document_id=document_id,
        current_user=current_user,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.put(
    "/{company_id}/{document_id}",
    response_model=VehicleDocumentResponse,
)
def update_vehicle_document(
    company_id: UUID,
    document_id: UUID,
    document_data: VehicleDocumentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = update_vehicle_document_service(
        db=db,
        company_id=company_id,
        document_id=document_id,
        current_user=current_user,
        document_type=document_data.document_type,
        document_number=document_data.document_number,
        issue_date=document_data.issue_date,
        expiry_date=document_data.expiry_date,
        file_url=document_data.file_url,
        remarks=document_data.remarks,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.delete(
    "/{company_id}/{document_id}",
    response_model=VehicleDocumentResponse,
)
def deactivate_vehicle_document(
    company_id: UUID,
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = deactivate_vehicle_document_service(
        db=db,
        company_id=company_id,
        document_id=document_id,
        current_user=current_user,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.post(
    "/{company_id}/{document_id}/renew",
    response_model=VehicleDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def renew_vehicle_document(
    company_id: UUID,
    document_id: UUID,
    document_data: VehicleDocumentRenew,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    print("RENEW ROUTE HIT", flush=True)
    result = renew_vehicle_document_service(
        db=db,
        company_id=company_id,
        document_id=document_id,
        current_user=current_user,
        document_number=document_data.document_number,
        issue_date=document_data.issue_date,
        expiry_date=document_data.expiry_date,
        file_url=document_data.file_url,
        remarks=document_data.remarks,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]