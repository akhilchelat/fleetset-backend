from datetime import date, timedelta
from uuid import UUID

from fastapi import status
from sqlalchemy.orm import Session

from app.models.vehicledocument import VehicleDocument

from app.reusable_functions.vehicle_reusable import (
    get_vehicle_by_id_query,
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
    get_vehicle_documents_query,
    renew_vehicle_document_query,
    get_expiring_vehicle_documents_query,
    get_expired_vehicle_documents_query,
)

from app.models.user import User


MANAGEMENT_ROLES = {
    "GLOBAL_ADMIN",
    "SUPER_ADMIN",
    "BRANCH_ADMIN",
}

VIEW_ROLES = {
    "GLOBAL_ADMIN",
    "SUPER_ADMIN",
    "BRANCH_ADMIN",
    "DRIVER",
}


def _get_role_name(current_user: User) -> str:
    if not current_user.role:
        return ""

    return current_user.role.name


def _check_view_access(
    current_user: User,
    company_id: UUID,
    branch_id: UUID | None = None,
):
    role_name = _get_role_name(current_user)

    if role_name not in VIEW_ROLES:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "ROLE_NOT_ALLOWED",
            "message": "You do not have permission to access vehicle documents",
            "data": None,
        }

    if role_name == "GLOBAL_ADMIN":
        return None

    if current_user.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_ACCESS_DENIED",
            "message": "You do not have access to this company",
            "data": None,
        }

    if branch_id is not None:
        if current_user.branch_id != branch_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "BRANCH_ACCESS_DENIED",
                "message": "You do not have access to this branch",
                "data": None,
            }

    return None


def _check_management_access(
    current_user: User,
    company_id: UUID,
    branch_id: UUID | None = None,
):
    role_name = _get_role_name(current_user)

    if role_name not in MANAGEMENT_ROLES:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "MANAGEMENT_ACCESS_REQUIRED",
            "message": "Only management users can manage vehicle documents",
            "data": None,
        }

    access_result = _check_view_access(
        current_user=current_user,
        company_id=company_id,
        branch_id=branch_id,
    )

    return access_result


def _validate_dates(
    issue_date: date | None,
    expiry_date: date | None,
):
    if (
        issue_date is not None
        and expiry_date is not None
        and expiry_date < issue_date
    ):
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DOCUMENT_DATES",
            "message": "Expiry date cannot be earlier than issue date",
            "data": None,
        }

    return None


def _validate_document_number(document_number: str | None):
    if document_number is not None and not document_number.strip():
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DOCUMENT_NUMBER",
            "message": "Document number cannot be empty",
            "data": None,
        }

    return None


def _validate_file_url(file_url: str | None):
    if file_url is not None and not file_url.strip():
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_FILE_URL",
            "message": "File URL cannot be empty",
            "data": None,
        }

    return None


def _get_vehicle_for_company(
    db: Session,
    vehicle_id: UUID,
    company_id: UUID,
    branch_id: UUID | None = None,
):
    vehicle = get_vehicle_by_id_query(
        db=db,
        company_id=company_id,
        vehicle_id=vehicle_id,
        branch_id=branch_id,
    )

    if not vehicle:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "VEHICLE_NOT_FOUND",
            "message": "Vehicle not found in this company or branch",
            "data": None,
        }

    if not vehicle.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "VEHICLE_INACTIVE",
            "message": "Vehicle is inactive",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "VEHICLE_FOUND",
        "message": "Vehicle found",
        "data": vehicle,
    }

def _validate_vehicle_branch(
    vehicle,
    current_user: User,
):
    role_name = _get_role_name(current_user)

    if role_name == "GLOBAL_ADMIN":
        return None

    if vehicle.branch_id != current_user.branch_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "BRANCH_ACCESS_DENIED",
            "message": "Vehicle does not belong to your branch",
            "data": None,
        }

    return None


def create_vehicle_document_service(
    db: Session,
    company_id: UUID,
    vehicle_id: UUID,
    current_user: User,
    document_type: str,
    document_number: str,
    issue_date: date,
    expiry_date: date,
    file_url: str,
    remarks: str | None = None,
):
    role_name = _get_role_name(current_user)
    
    access_result = _check_management_access(
        current_user=current_user,
        company_id=company_id,)
    
    if access_result:
        return access_result
    
    vehicle_check = _get_vehicle_for_company(
        db=db,
        vehicle_id=vehicle_id,
        company_id=company_id,
        branch_id=(
            None
            if role_name == "GLOBAL_ADMIN"
            else current_user.branch_id),)
    
    if not vehicle_check["success"]:
        return vehicle_check
    
    vehicle = vehicle_check["data"]
    
    access_result = _check_management_access(
        
        current_user=current_user,
        company_id=company_id,
        branch_id=vehicle.branch_id,)
    
    if access_result:
        return access_result
    
    if access_result:
        return access_result

    date_result = _validate_dates(
        issue_date=issue_date,
        expiry_date=expiry_date,
    )

    if date_result:
        return date_result

    number_result = _validate_document_number(document_number)

    if number_result:
        return number_result

    file_result = _validate_file_url(file_url)

    if file_result:
        return file_result

    existing_document = get_active_document_by_type_query(
        db=db,
        vehicle_id=vehicle_id,
        document_type=document_type,
        company_id=company_id,
        branch_id=vehicle.branch_id,
    )

    if existing_document:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "DOCUMENT_ALREADY_EXISTS",
            "message": (
                f"An active {document_type} document "
                "already exists for this vehicle"
            ),
            "data": None,
        }

    document = VehicleDocument(
        company_id=company_id,
        branch_id=vehicle.branch_id,
        vehicle_id=vehicle_id,
        uploaded_by=current_user.id,
        document_type=document_type,
        document_number=document_number.strip(),
        issue_date=issue_date,
        expiry_date=expiry_date,
        file_url=file_url.strip(),
        remarks=remarks.strip() if remarks else None,
    )

    document = create_vehicle_document_query(
        db=db,
        document=document,
    )

    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "code": "DOCUMENT_CREATED",
        "message": "Vehicle document created successfully",
        "data": document,
    }



def update_vehicle_document_service(
    db: Session,
    company_id: UUID,
    document_id: UUID,
    current_user: User,
    document_type: str | None = None,
    document_number: str | None = None,
    issue_date: date | None = None,
    expiry_date: date | None = None,
    file_url: str | None = None,
    remarks: str | None = None,
):
    # 1. Find the document within the requested company.
    document = get_vehicle_document_by_id_query(
        db=db,
        document_id=document_id,
        company_id=company_id,
    )

    if not document:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DOCUMENT_NOT_FOUND",
            "message": "Vehicle document not found",
            "data": None,
        }

    # 2. Check the user's company and branch permissions.
    access_result = _check_management_access(
        current_user=current_user,
        company_id=company_id,
        branch_id=document.branch_id,
    )

    if access_result:
        return access_result

    # 3. Verify the vehicle using the document's company
    #    and branch context.
    vehicle_check = _get_vehicle_for_company(
        db=db,
        vehicle_id=document.vehicle_id,
        company_id=company_id,
        branch_id=document.branch_id,
    )

    if not vehicle_check["success"]:
        return vehicle_check

    vehicle = vehicle_check["data"]

    # 4. Validate the effective dates, including existing
    #    values when the request omits a date.
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

    date_result = _validate_dates(
        issue_date=effective_issue_date,
        expiry_date=effective_expiry_date,
    )

    if date_result:
        return date_result

    # 5. Validate the supplied document number and file URL.
    number_result = _validate_document_number(document_number)

    if number_result:
        return number_result

    file_result = _validate_file_url(file_url)

    if file_result:
        return file_result

    # 6. Prevent duplicate active documents if the document
    #    type is being changed.
    if (
        document_type is not None
        and document_type != document.document_type
    ):
        existing_document = get_active_document_by_type_query(
            db=db,
            vehicle_id=document.vehicle_id,
            document_type=document_type,
            company_id=company_id,
            branch_id=document.branch_id,
        )

        if (
            existing_document
            and existing_document.id != document.id
        ):
            return {
                "success": False,
                "status_code": status.HTTP_409_CONFLICT,
                "code": "DOCUMENT_ALREADY_EXISTS",
                "message": (
                    f"An active {document_type} document "
                    "already exists for this vehicle"
                ),
                "data": None,
            }

    # 7. Update only the fields supplied by the request.
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
        document.remarks = remarks.strip() or None

    # 8. Persist the changes.
    document = update_vehicle_document_query(
        db=db,
        document=document,
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DOCUMENT_UPDATED",
        "message": "Vehicle document updated successfully",
        "data": document,
    }

def deactivate_vehicle_document_service(
    db: Session,
    company_id: UUID,
    document_id: UUID,
    current_user: User,
):
    document = get_vehicle_document_by_id_query(
        db=db,
        document_id=document_id,
        company_id=company_id,
    )

    if not document:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DOCUMENT_NOT_FOUND",
            "message": "Vehicle document not found",
            "data": None,
        }

    access_result = _check_management_access(
        current_user=current_user,
        company_id=company_id,
        branch_id=document.branch_id,
    )

    if access_result:
        return access_result

    if not document.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "DOCUMENT_ALREADY_INACTIVE",
            "message": "Vehicle document is already inactive",
            "data": None,
        }

    document = deactivate_vehicle_document_query(
        db=db,
        document=document,
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DOCUMENT_DEACTIVATED",
        "message": "Vehicle document deactivated successfully",
        "data": document,
    }


def renew_vehicle_document_service(
    db: Session,
    company_id: UUID,
    document_id: UUID,
    current_user: User,
    document_number: str,
    issue_date: date,
    expiry_date: date,
    file_url: str,
    remarks: str | None = None,
):
    old_document = get_vehicle_document_by_id_query(
        db=db,
        document_id=document_id,
        company_id=company_id,
    )

    if not old_document:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DOCUMENT_NOT_FOUND",
            "message": "Vehicle document not found",
            "data": None,
        }

    access_result = _check_management_access(
        current_user=current_user,
        company_id=company_id,
        branch_id=old_document.branch_id,
    )

    if access_result:
        return access_result

    if not old_document.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "DOCUMENT_ALREADY_INACTIVE",
            "message": "Vehicle document is already inactive",
            "data": None,
        }

        

    vehicle_check = _get_vehicle_for_company(
    db=db,
    vehicle_id=old_document.vehicle_id,
    company_id=company_id,
    branch_id=old_document.branch_id,
)

    if not vehicle_check["success"]:
        return vehicle_check

    date_result = _validate_dates(
        issue_date=issue_date,
        expiry_date=expiry_date,
    )

    if date_result:
        return date_result

    number_result = _validate_document_number(
        document_number
    )

    if number_result:
        return number_result

    file_result = _validate_file_url(
        file_url
    )

    if file_result:
        return file_result

    existing_document = get_active_document_by_type_query(
        db=db,
        vehicle_id=old_document.vehicle_id,
        document_type=old_document.document_type,
        company_id=company_id,
        branch_id=old_document.branch_id,
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
                f"An active {old_document.document_type} "
                "document already exists for this vehicle"
            ),
            "data": None,
        }

    new_document = VehicleDocument(
        company_id=old_document.company_id,
        branch_id=old_document.branch_id,
        vehicle_id=old_document.vehicle_id,
        uploaded_by=current_user.id,
        document_type=old_document.document_type,
        document_number=document_number.strip(),
        issue_date=issue_date,
        expiry_date=expiry_date,
        file_url=file_url.strip(),
        remarks=remarks.strip() if remarks else None,
    )

    new_document = renew_vehicle_document_query(
        db=db,
        old_document=old_document,
        new_document=new_document,
    )

    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "code": "DOCUMENT_RENEWED",
        "message": "Vehicle document renewed successfully",
        "data": new_document,
    }


def get_vehicle_document_service(
    db: Session,
    company_id: UUID,
    document_id: UUID,
    current_user: User,
):
    document = get_vehicle_document_by_id_query(
        db=db,
        document_id=document_id,
        company_id=company_id,
    )

    if not document:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DOCUMENT_NOT_FOUND",
            "message": "Vehicle document not found",
            "data": None,
        }

    access_result = _check_view_access(
        current_user=current_user,
        company_id=company_id,
        branch_id=document.branch_id,
    )

    if access_result:
        return access_result

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DOCUMENT_FOUND",
        "message": "Vehicle document found successfully",
        "data": document,
    }


def get_vehicle_documents_service(
    db: Session,
    company_id: UUID,
    document_ids: list[UUID],
    current_user: User,
):
    if not document_ids:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "EMPTY_DOCUMENT_IDS",
            "message": "Document IDs cannot be empty",
            "data": [],
        }

    role_name = _get_role_name(current_user)

    if role_name == "GLOBAL_ADMIN":
        documents = get_vehicle_documents_by_ids_query(
            db=db,
            company_id=company_id,
            document_ids=document_ids,
        )
    else:
        if current_user.company_id != company_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "COMPANY_ACCESS_DENIED",
                "message": "You do not have access to this company",
                "data": [],
            }

        documents = get_vehicle_documents_by_ids_query(
            db=db,
            company_id=company_id,
            document_ids=document_ids,
            branch_id=current_user.branch_id,
        )

    if not documents:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DOCUMENTS_NOT_FOUND",
            "message": "No active vehicle documents found",
            "data": [],
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DOCUMENTS_FOUND",
        "message": "Vehicle documents retrieved successfully",
        "data": documents,
    }


def get_company_documents_by_type_service(
    db: Session,
    company_id: UUID,
    document_type: str,
    current_user: User,
):
    role_name = _get_role_name(current_user)

    if role_name != "GLOBAL_ADMIN":
        if current_user.company_id != company_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "COMPANY_ACCESS_DENIED",
                "message": "You do not have access to this company",
                "data": [],
            }

        branch_id = current_user.branch_id
    else:
        branch_id = None

    documents = get_company_documents_by_type_query(
        db=db,
        company_id=company_id,
        document_type=document_type,
        branch_id=branch_id,
    )

    if not documents:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "DOCUMENTS_NOT_FOUND",
            "message": (
                f"No active {document_type} documents found"
            ),
            "data": [],
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "DOCUMENTS_FOUND",
        "message": "Company documents retrieved successfully",
        "data": documents,
    }


def get_active_vehicle_documents_service(
    db: Session,
    company_id: UUID,
    current_user: User,
):
    role_name = _get_role_name(current_user)

    if role_name != "GLOBAL_ADMIN":
        if current_user.company_id != company_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "COMPANY_ACCESS_DENIED",
                "message": "You do not have access to this company",
                "data": [],
            }

        branch_id = current_user.branch_id
    else:
        branch_id = None

    documents = get_all_active_vehicle_documents_query(
        db=db,
        company_id=company_id,
        branch_id=branch_id,
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "ACTIVE_DOCUMENTS_FOUND",
        "message": "Active vehicle documents retrieved successfully",
        "data": documents,
    }


def get_inactive_vehicle_documents_service(
    db: Session,
    company_id: UUID,
    current_user: User,
):
    role_name = _get_role_name(current_user)

    if role_name != "GLOBAL_ADMIN":
        if current_user.company_id != company_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "COMPANY_ACCESS_DENIED",
                "message": "You do not have access to this company",
                "data": [],
            }

        branch_id = current_user.branch_id
    else:
        branch_id = None

    documents = get_all_inactive_vehicle_documents_query(
        db=db,
        company_id=company_id,
        branch_id=branch_id,
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "INACTIVE_DOCUMENTS_FOUND",
        "message": "Inactive vehicle documents retrieved successfully",
        "data": documents,
    }


def get_expiring_vehicle_documents_service(
    db: Session,
    company_id: UUID,
    current_user: User,
    days: int = 30,
):
    if days < 0:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DAYS",
            "message": "Days cannot be negative",
            "data": [],
        }

    role_name = _get_role_name(current_user)

    if role_name != "GLOBAL_ADMIN":
        if current_user.company_id != company_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "COMPANY_ACCESS_DENIED",
                "message": "You do not have access to this company",
                "data": [],
            }

        branch_id = current_user.branch_id
    else:
        branch_id = None

    today = date.today()
    end_date = today + timedelta(days=days)

    documents = get_expiring_vehicle_documents_query(
        db=db,
        company_id=company_id,
        start_date=today,
        end_date=end_date,
        branch_id=branch_id,
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "EXPIRING_DOCUMENTS_FOUND",
        "message": "Expiring vehicle documents retrieved successfully",
        "data": documents,
    }


def get_expired_vehicle_documents_service(
    db: Session,
    company_id: UUID,
    current_user: User,
):
    role_name = _get_role_name(current_user)

    if role_name != "GLOBAL_ADMIN":
        if current_user.company_id != company_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "COMPANY_ACCESS_DENIED",
                "message": "You do not have access to this company",
                "data": [],
            }

        branch_id = current_user.branch_id
    else:
        branch_id = None

    today = date.today()

    documents = get_expired_vehicle_documents_query(
        db=db,
        company_id=company_id,
        today=today,
        branch_id=branch_id,
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "EXPIRED_DOCUMENTS_FOUND",
        "message": "Expired vehicle documents retrieved successfully",
        "data": documents,
    }


def get_vehicle_documents_for_vehicle_service(
    db: Session,
    company_id: UUID,
    vehicle_id: UUID,
    current_user: User,
):
    vehicle_check = _get_vehicle_for_company(
        db=db,
        vehicle_id=vehicle_id,
        company_id=company_id,
    )

    if not vehicle_check["success"]:
        return {
            "success": False,
            "status_code": vehicle_check["status_code"],
            "code": vehicle_check["code"],
            "message": vehicle_check["message"],
            "data": [],
        }

    vehicle = vehicle_check["data"]

    access_result = _check_view_access(
        current_user=current_user,
        company_id=company_id,
        branch_id=vehicle.branch_id,
    )

    if access_result:
        return {
            "success": False,
            "status_code": access_result["status_code"],
            "code": access_result["code"],
            "message": access_result["message"],
            "data": [],
        }

    documents = get_vehicle_documents_query(
        db=db,
        vehicle_id=vehicle_id,
        company_id=company_id,
        branch_id=vehicle.branch_id,
        active_only=True,
    )

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "VEHICLE_DOCUMENTS_FOUND",
        "message": "Vehicle documents retrieved successfully",
        "data": documents,
    }
