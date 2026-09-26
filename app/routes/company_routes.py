from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.company_schema import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyListResponse,
    CompanyBulkAction,
    CompanyBulkActionResponse,
)

from app.services.company_service import (
    create_company,
    find_company_by_id,
    find_company_by_email,
    get_all_active_companies,
    update_company,
    deactivate_company,
    get_all_companies,
    activate_company,
    bulk_activate_companies,
    bulk_deactivate_companies,
)


router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)


@router.post(
    "/",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_company_route(
    company: CompanyCreate,
    db: Session = Depends(get_db),
):
    result = create_company(
        db=db,
        name=company.name,
        email=company.email,
        phone=company.phone,
        address=company.address,
        gst_number=company.gst_number,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/",
    response_model=list[CompanyListResponse],
    status_code=status.HTTP_200_OK,
)
def get_all_companies_route(
    db: Session = Depends(get_db),
):
    result = get_all_companies(
        db=db,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/active",
    response_model=list[CompanyListResponse],
    status_code=status.HTTP_200_OK,
)
def get_all_active_companies_route(
    db: Session = Depends(get_db),
):
    result = get_all_active_companies(
        db=db,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/email/{email}",
    response_model=CompanyResponse,
    status_code=status.HTTP_200_OK,
)
def get_company_by_email_route(
    email: str,
    db: Session = Depends(get_db),
):
    result = find_company_by_email(
        db=db,
        email=email,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.patch(
    "/bulk/activate",
    response_model=CompanyBulkActionResponse,
    status_code=status.HTTP_200_OK,
)
def bulk_activate_companies_route(
    company_data: CompanyBulkAction,
    db: Session = Depends(get_db),
):
    result = bulk_activate_companies(
        db=db,
        company_ids=company_data.company_ids,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.patch(
    "/bulk/deactivate",
    response_model=CompanyBulkActionResponse,
    status_code=status.HTTP_200_OK,
)
def bulk_deactivate_companies_route(
    company_data: CompanyBulkAction,
    db: Session = Depends(get_db),
):
    result = bulk_deactivate_companies(
        db=db,
        company_ids=company_data.company_ids,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    status_code=status.HTTP_200_OK,
)
def get_company_by_id_route(
    company_id: UUID,
    db: Session = Depends(get_db),
):
    result = find_company_by_id(
        db=db,
        company_id=company_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"] 


@router.put(
    "/{company_id}",
    response_model=CompanyResponse,
    status_code=status.HTTP_200_OK,
)
def update_company_route(
    company_id: UUID,
    company: CompanyUpdate,
    db: Session = Depends(get_db),
):
    result = update_company(
        db=db,
        company_id=company_id,
        name=company.name,
        email=company.email,
        phone=company.phone,
        address=company.address,
        gst_number=company.gst_number,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.patch(
    "/{company_id}/activate",
    response_model=CompanyResponse,
    status_code=status.HTTP_200_OK,
)
def activate_company_route(
    company_id: UUID,
    db: Session = Depends(get_db),
):
    result = activate_company(
        db=db,
        company_id=company_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]


@router.patch(
    "/{company_id}/deactivate",
    response_model=CompanyResponse,
    status_code=status.HTTP_200_OK,
)
def deactivate_company_route(
    company_id: UUID,
    db: Session = Depends(get_db),
):
    result = deactivate_company(
        db=db,
        company_id=company_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result["data"]