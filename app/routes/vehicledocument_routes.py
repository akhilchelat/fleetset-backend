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
)


router = APIRouter(
    prefix="/vehicle-documents",
    tags=["Vehicle Documents"]
)


@router.post(
    "/{company_id}",
    response_model=VehicleDocumentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_vehicle_document_route(
    company_id: UUID,
    document_data: VehicleDocumentCreate,
    db: Session = Depends(get_db)
):
    result = create_vehicle_document_service(
        db=db,
        company_id=company_id,
        vehicle_id=document_data.vehicle_id,
        uploaded_by=document_data.uploaded_by,
        document_type=document_data.document_type,
        document_number=document_data.document_number,
        issue_date=document_data.issue_date,
        expiry_date=document_data.expiry_date,
        file_url=document_data.file_url,
        remarks=document_data.remarks
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


@router.get(
    "/{company_id}/active",
    response_model=list[VehicleDocumentResponse],
    status_code=status.HTTP_200_OK
)
def get_active_vehicle_documents_route(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    result = get_active_vehicle_documents_service(
        db=db,
        company_id=company_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


@router.get(
    "/{company_id}/inactive",
    response_model=list[VehicleDocumentResponse],
    status_code=status.HTTP_200_OK
)
def get_inactive_vehicle_documents_route(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    result = get_inactive_vehicle_documents_service(
        db=db,
        company_id=company_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


@router.get(
    "/{company_id}/expiring",
    response_model=list[VehicleDocumentResponse],
    status_code=status.HTTP_200_OK
)
def get_expiring_vehicle_documents_route(
    company_id: UUID,
    days: int = Query(default=30),
    db: Session = Depends(get_db)
):
    result = get_expiring_vehicle_documents_service(
        db=db,
        company_id=company_id,
        days=days
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


@router.get(
    "/{company_id}/expired",
    response_model=list[VehicleDocumentResponse],
    status_code=status.HTTP_200_OK
)
def get_expired_vehicle_documents_route(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    result = get_expired_vehicle_documents_service(
        db=db,
        company_id=company_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


@router.get(
    "/{company_id}/type/{document_type}",
    response_model=list[VehicleDocumentResponse],
    status_code=status.HTTP_200_OK
)
def get_company_documents_by_type_route(
    company_id: UUID,
    document_type: str,
    db: Session = Depends(get_db)
):
    result = get_company_documents_by_type_service(
        db=db,
        company_id=company_id,
        document_type=document_type
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


@router.post(
    "/{company_id}/bulk",
    response_model=list[VehicleDocumentResponse],
    status_code=status.HTTP_200_OK
)
def get_vehicle_documents_route(
    company_id: UUID,
    document_data: VehicleDocumentBulkRequest,
    db: Session = Depends(get_db)
):
    result = get_vehicle_documents_service(
        db=db,
        company_id=company_id,
        document_ids=document_data.document_ids
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


@router.put(
    "/{company_id}/{document_id}",
    response_model=VehicleDocumentResponse,
    status_code=status.HTTP_200_OK
)
def update_vehicle_document_route(
    company_id: UUID,
    document_id: UUID,
    document_data: VehicleDocumentUpdate,
    db: Session = Depends(get_db)
):
    result = update_vehicle_document_service(
        db=db,
        company_id=company_id,
        document_id=document_id,
        document_type=document_data.document_type,
        document_number=document_data.document_number,
        issue_date=document_data.issue_date,
        expiry_date=document_data.expiry_date,
        file_url=document_data.file_url,
        remarks=document_data.remarks
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


@router.patch(
    "/{company_id}/{document_id}/deactivate",
    response_model=VehicleDocumentResponse,
    status_code=status.HTTP_200_OK
)
def deactivate_vehicle_document_route(
    company_id: UUID,
    document_id: UUID,
    db: Session = Depends(get_db)
):
    result = deactivate_vehicle_document_service(
        db=db,
        company_id=company_id,
        document_id=document_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


@router.post(
    "/{company_id}/{document_id}/renew",
    response_model=VehicleDocumentResponse,
    status_code=status.HTTP_201_CREATED
)
def renew_vehicle_document_route(
    company_id: UUID,
    document_id: UUID,
    document_data: VehicleDocumentRenew,
    db: Session = Depends(get_db)
):
    result = renew_vehicle_document_service(
        db=db,
        company_id=company_id,
        document_id=document_id,
        uploaded_by=document_data.uploaded_by,
        document_number=document_data.document_number,
        issue_date=document_data.issue_date,
        expiry_date=document_data.expiry_date,
        file_url=document_data.file_url,
        remarks=document_data.remarks
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]


@router.get(
    "/{company_id}/{document_id}",
    response_model=VehicleDocumentResponse,
    status_code=status.HTTP_200_OK
)
def get_vehicle_document_route(
    company_id: UUID,
    document_id: UUID,
    db: Session = Depends(get_db)
):
    result = get_vehicle_document_service(
        db=db,
        company_id=company_id,
        document_id=document_id
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"]
        )

    return result["data"]

