from datetime import date, timedelta
from uuid import UUID
from fastapi import status
from sqlalchemy.orm import Session
from app.models.vehicledocument import VehicleDocument, VehicleDocumentType
from app.reusable_functions.vehicle_reusable import (
    get_vehicle_by_id_query
)
from app.reusable_functions.vehicledocument_resusable import (
    get_vehicle_document_by_id_query,
    get_active_document_by_type_query,
    create_vehicle_document_query,
    update_vehicle_document_query,
    deactivate_vehicle_document_query,
    get_vehicle_documents_by_ids_query,
    get_company_documents_by_type_query,
    get_all_active_vehicle_documents_query,
    get_all_inactive_vehicle_documents_query,
    renew_vehicle_document_query,
    get_expiring_vehicle_documents_query,
    get_expired_vehicle_documents_query
)
from app.reusable_functions.company_reusable import (
    get_company_by_id_query
)
from app.reusable_functions.user_reusable import (
    get_user_by_id_query
)


def create_vehicle_document_service(
    db: Session,
    company_id: UUID,
    vehicle_id: UUID,
    uploaded_by: UUID,
    document_type: VehicleDocumentType,
    document_number: str,
    issue_date: date,
    expiry_date: date,
    file_url: str,
    remarks: str | None = None
):
    company = get_company_by_id_query(
        db,
        company_id
    )

    if not company or not company.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": None
        }

    vehicle = get_vehicle_by_id_query(
        db,
        vehicle_id
    )

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found",
            "data": None
        }

    if vehicle.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "VEHICLE_COMPANY_MISMATCH",
            "message": "Vehicle does not belong to this company",
            "data": None
        }

    if not vehicle.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "VEHICLE_INACTIVE",
            "message": "Vehicle is inactive",
            "data": None
        }

    user = get_user_by_id_query(
        db,
        uploaded_by
    )

    if not user:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "USER_NOT_FOUND",
            "message": "Uploader not found",
            "data": None
        }

    if user.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "USER_COMPANY_MISMATCH",
            "message": "Uploader does not belong to this company",
            "data": None
        }

    if not document_number or not document_number.strip():
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DOCUMENT_NUMBER",
            "message": "Document number cannot be empty",
            "data": None
        }

    if issue_date and expiry_date and expiry_date <= issue_date:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DOCUMENT_DATES",
            "message": "Expiry date must be later than issue date",
            "data": None
        }

    if not file_url or not file_url.strip():
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_FILE_URL",
            "message": "File URL cannot be empty",
            "data": None
        }

    existing_document = get_active_document_by_type_query(
        db,
        vehicle_id,
        document_type
    )

    if existing_document:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "DOCUMENT_ALREADY_EXISTS",
            "message": (
                f"An active {document_type} document "
                f"already exists for this vehicle."
            ),
            "data": None
        }

    document = VehicleDocument(
        company_id=company_id,
        vehicle_id=vehicle_id,
        uploaded_by=uploaded_by,
        document_type=document_type,
        document_number=document_number.strip(),
        issue_date=issue_date,
        expiry_date=expiry_date,
        file_url=file_url.strip(),
        remarks=remarks
    )

    document = create_vehicle_document_query(
        db,
        document
    )

    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "code": "DOCUMENT_CREATED",
        "message": "Vehicle document created successfully",
        "data": document
    }


def update_vehicle_document_service(
    db: Session,
    company_id: UUID,
    document_id: UUID,
    document_type: VehicleDocumentType | None = None,
    document_number: str | None = None,
    issue_date: date | None = None,
    expiry_date: date | None = None,
    file_url: str | None = None,
    remarks: str | None = None
):
    company = get_company_by_id_query(
        db,
        company_id
    )

    if not company or not company.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": None
        }

    document = get_vehicle_document_by_id_query(
        db,
        document_id
    )

    if not document:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DOCUMENT_NOT_FOUND",
            "message": "Vehicle document not found",
            "data": None
        }

    if document.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "DOCUMENT_COMPANY_MISMATCH",
            "message": "Document does not belong to this company",
            "data": None
        }

    vehicle = get_vehicle_by_id_query(
        db,
        document.vehicle_id
    )

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found",
            "data": None
        }

    if not vehicle.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "VEHICLE_INACTIVE",
            "message": "Vehicle is inactive",
            "data": None
        }

    if document_number is not None:
        if not document_number.strip():
            return {
                "success": False,
                "status_code": status.HTTP_400_BAD_REQUEST,
                "code": "INVALID_DOCUMENT_NUMBER",
                "message": "Document number cannot be empty",
                "data": None
            }

    effective_issue_date = (
        issue_date
        if issue_date is not None
        else document.issue_date
    )

    effective_expiry_date = (
        expiry_date
        if expiry_date is not None
        else document.expiry_date
    )

    if (
        effective_issue_date
        and effective_expiry_date
        and effective_expiry_date <= effective_issue_date
    ):
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DOCUMENT_DATES",
            "message": "Expiry date must be later than issue date",
            "data": None
        }

    if file_url is not None:
        if not file_url.strip():
            return {
                "success": False,
                "status_code": status.HTTP_400_BAD_REQUEST,
                "code": "INVALID_FILE_URL",
                "message": "File URL cannot be empty",
                "data": None
            }

    if document_type is not None and document_type != document.document_type:
        existing_document = get_active_document_by_type_query(
            db,
            document.vehicle_id,
            document_type
        )

        if existing_document and existing_document.id != document.id:
            return {
                "success": False,
                "status_code": status.HTTP_409_CONFLICT,
                "code": "DOCUMENT_ALREADY_EXISTS",
                "message": (
                    f"An active {document_type} document "
                    f"already exists for this vehicle."
                ),
                "data": None
            }

    if document_type is not None:
        document.document_type = document_type

    if document_number is not None:
        document.document_number = document_number.strip()

    if issue_date is not None:
        document.issue_date = issue_date

    if expiry_date is not None:
        document.expiry_date = expiry_date

    if file_url is not None:
        document.file_url = file_url.strip()

    if remarks is not None:
        document.remarks = remarks

    document = update_vehicle_document_query(
        db,
        document
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DOCUMENT_UPDATED",
        "message": "Vehicle document updated successfully",
        "data": document
    }


def deactivate_vehicle_document_service(
    db: Session,
    company_id: UUID,
    document_id: UUID
):
    company = get_company_by_id_query(
        db,
        company_id
    )

    if not company or not company.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": None
        }

    document = get_vehicle_document_by_id_query(
        db,
        document_id
    )

    if not document:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DOCUMENT_NOT_FOUND",
            "message": "Vehicle document not found",
            "data": None
        }

    if document.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "DOCUMENT_COMPANY_MISMATCH",
            "message": "Document does not belong to this company",
            "data": None
        }

    vehicle = get_vehicle_by_id_query(
        db,
        document.vehicle_id
    )

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found",
            "data": None
        }

    if not vehicle.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "VEHICLE_INACTIVE",
            "message": "Vehicle is inactive",
            "data": None
        }

    if not document.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "DOCUMENT_ALREADY_INACTIVE",
            "message": "Vehicle document is already inactive",
            "data": None
        }

    document = deactivate_vehicle_document_query(
        db,
        document
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DOCUMENT_DEACTIVATED",
        "message": "Vehicle document deactivated successfully",
        "data": document
    }


def renew_vehicle_document_service(
    db: Session,
    company_id: UUID,
    document_id: UUID,
    uploaded_by: UUID,
    document_number: str,
    issue_date: date,
    expiry_date: date,
    file_url: str,
    remarks: str | None = None
):
    company = get_company_by_id_query(
        db,
        company_id
    )

    if not company or not company.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": None
        }

    old_document = get_vehicle_document_by_id_query(
        db,
        document_id
    )

    if not old_document:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DOCUMENT_NOT_FOUND",
            "message": "Vehicle document not found",
            "data": None
        }

    if old_document.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "DOCUMENT_COMPANY_MISMATCH",
            "message": "Document does not belong to this company",
            "data": None
        }

    vehicle = get_vehicle_by_id_query(
        db,
        old_document.vehicle_id
    )

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found",
            "data": None
        }

    if not vehicle.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "VEHICLE_INACTIVE",
            "message": "Vehicle is inactive",
            "data": None
        }

    user = get_user_by_id_query(
        db,
        uploaded_by
    )

    if not user:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "USER_NOT_FOUND",
            "message": "Uploader not found",
            "data": None
        }

    if user.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "USER_COMPANY_MISMATCH",
            "message": "Uploader does not belong to this company",
            "data": None
        }

    if not document_number or not document_number.strip():
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DOCUMENT_NUMBER",
            "message": "Document number cannot be empty",
            "data": None
        }

    if expiry_date <= issue_date:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DOCUMENT_DATES",
            "message": "Expiry date must be later than issue date",
            "data": None
        }

    if not file_url or not file_url.strip():
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_FILE_URL",
            "message": "File URL cannot be empty",
            "data": None
        }

    if not old_document.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "DOCUMENT_ALREADY_INACTIVE",
            "message": "Vehicle document is already inactive",
            "data": None
        }

    existing_document = get_active_document_by_type_query(
        db,
        old_document.vehicle_id,
        old_document.document_type
    )

    if (
        existing_document
        and existing_document.id != old_document.id
    ):
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "DOCUMENT_ALREADY_EXISTS",
            "message": (
                f"An active {old_document.document_type} document "
                f"already exists for this vehicle."
            ),
            "data": None
        }

    new_document = VehicleDocument(
        company_id=company_id,
        vehicle_id=old_document.vehicle_id,
        uploaded_by=uploaded_by,
        document_type=old_document.document_type,
        document_number=document_number.strip(),
        issue_date=issue_date,
        expiry_date=expiry_date,
        file_url=file_url.strip(),
        remarks=remarks
    )

    new_document = renew_vehicle_document_query(
        db,
        old_document,
        new_document
    )

    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "code": "DOCUMENT_RENEWED",
        "message": "Vehicle document renewed successfully",
        "data": new_document
    }


def get_vehicle_document_service(
    db: Session,
    company_id: UUID,
    document_id: UUID
):
    company = get_company_by_id_query(
        db,
        company_id
    )

    if not company or not company.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": None
        }

    document = get_vehicle_document_by_id_query(
        db,
        document_id
    )

    if not document:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DOCUMENT_NOT_FOUND",
            "message": "Vehicle document not found",
            "data": None
        }

    if document.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "DOCUMENT_COMPANY_MISMATCH",
            "message": "Document does not belong to this company",
            "data": None
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DOCUMENT_FOUND",
        "message": "Vehicle document found successfully",
        "data": document
    }


def get_vehicle_documents_service(
    db: Session,
    company_id: UUID,
    document_ids: list[UUID]
):
    company = get_company_by_id_query(
        db,
        company_id
    )

    if not company or not company.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": []
        }

    if not document_ids:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "EMPTY_DOCUMENT_IDS",
            "message": "Document IDs cannot be empty",
            "data": []
        }

    documents = get_vehicle_documents_by_ids_query(
        db,
        company_id,
        document_ids
    )

    if not documents:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DOCUMENTS_NOT_FOUND",
            "message": "No active vehicle documents found",
            "data": []
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DOCUMENTS_FOUND",
        "message": "Vehicle documents retrieved successfully",
        "data": documents
    }


def get_company_documents_by_type_service(
    db: Session,
    company_id: UUID,
    document_type: VehicleDocumentType
):
    company = get_company_by_id_query(
        db,
        company_id
    )

    if not company or not company.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": []
        }

    documents = get_company_documents_by_type_query(
        db,
        company_id,
        document_type
    )

    if not documents:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DOCUMENTS_NOT_FOUND",
            "message": (
                f"No active {document_type} documents found "
                f"for this company."
            ),
            "data": []
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DOCUMENTS_FOUND",
        "message": "Company documents retrieved successfully",
        "data": documents
    }


def get_active_vehicle_documents_service(
    db: Session,
    company_id: UUID
):
    company = get_company_by_id_query(
        db,
        company_id
    )

    if not company or not company.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": []
        }

    documents = get_all_active_vehicle_documents_query(
        db,
        company_id
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "ACTIVE_DOCUMENTS_FOUND",
        "message": "Active vehicle documents retrieved successfully",
        "data": documents
    }


def get_inactive_vehicle_documents_service(
    db: Session,
    company_id: UUID
):
    company = get_company_by_id_query(
        db,
        company_id
    )

    if not company or not company.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": []
        }

    documents = get_all_inactive_vehicle_documents_query(
        db,
        company_id
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "INACTIVE_DOCUMENTS_FOUND",
        "message": "Inactive vehicle documents retrieved successfully",
        "data": documents
    }


def get_expiring_vehicle_documents_service(
    db: Session,
    company_id: UUID,
    days: int = 30
):
    company = get_company_by_id_query(
        db,
        company_id
    )

    if not company or not company.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": []
        }

    if days < 0:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DAYS",
            "message": "Days cannot be negative",
            "data": []
        }

    today = date.today()
    end_date = today + timedelta(days=days)

    documents = get_expiring_vehicle_documents_query(
        db,
        company_id,
        today,
        end_date
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "EXPIRING_DOCUMENTS_FOUND",
        "message": "Expiring vehicle documents retrieved successfully",
        "data": documents
    }


def get_expired_vehicle_documents_service(
    db: Session,
    company_id: UUID
):
    company = get_company_by_id_query(
        db,
        company_id
    )

    if not company or not company.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found or inactive",
            "data": []
        }

    today = date.today()

    documents = get_expired_vehicle_documents_query(
        db,
        company_id,
        today
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "EXPIRED_DOCUMENTS_FOUND",
        "message": "Expired vehicle documents retrieved successfully",
        "data": documents
    }

