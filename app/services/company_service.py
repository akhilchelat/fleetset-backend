# company service layer

# create_company()
# get_company_by_id()
# get_all_companies()
# update_company()
# deactivate_company()

# company_service.py

from sqlalchemy.orm import Session
from fastapi import status
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from app.models.company import Company
from app.reusable_functions.company_reusable import (get_company_by_id_query, 
                                                     get_company_by_email_query,
                                                     get_all_active_companies_query,
                                                     get_all_companies_query,
                                                     get_company_by_id_admin_query,
                                                     get_companies_by_ids_query)



def create_company(
    db: Session,
    name: str,
    email: str,
    phone: str,
    address: str,
    gst_number: str,
):

    existing_company = get_company_by_email_query(
        db=db,
        email=email,
    )

    if existing_company is not None:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "COMPANY_EMAIL_ALREADY_EXISTS",
            "message": "A company already exists with this email.",
            "data": None,
        }

    new_company = Company(
        name=name,
        email=email,
        phone=phone,
        address=address,
        gst_number=gst_number,
        is_active=True,
    )

    try:
        db.add(new_company)
        db.commit()
        db.refresh(new_company)

        return {
            "success": True,
            "status_code": status.HTTP_201_CREATED,
            "code": "COMPANY_CREATED",
            "message": "Company created successfully.",
            "data": new_company,
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "COMPANY_EMAIL_ALREADY_EXISTS",
            "message": "A company already exists with this email.",
            "data": None,
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong while creating the company.",
            "data": None,
        }
        

def find_company_by_id(
    db: Session,
    company_id: UUID,
):
    company = get_company_by_id_query(
        db=db,
        company_id=company_id,
    )

    if company is None:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found.",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "COMPANY_FOUND",
        "message": "Company found successfully.",
        "data": company,
    }


def find_company_by_email(
    db: Session,
    email: str,
):

    company = get_company_by_email_query(
        db=db,
        email=email,
    )

    if company is None:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found.",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "COMPANY_FOUND",
        "message": "Company found successfully.",
        "data": company,
    }


def get_all_active_companies(
    db: Session,
):
    companies = get_all_active_companies_query(
        db=db,
    )

    if not companies:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_ACTIVE_COMPANIES_FOUND",
            "message": "No active companies found.",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "ACTIVE_COMPANIES_FOUND",
        "message": "Active companies retrieved successfully.",
        "data": companies,
    }


def update_company(
    db: Session,
    company_id: UUID,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    address: str | None = None,
    gst_number: str | None = None,
):

    company = get_company_by_id_query(
        db=db,
        company_id=company_id,
    )

    if company is None:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found.",
            "data": None,
        }

    # Check email uniqueness
    if email is not None and email != company.email:

        existing_company = get_company_by_email_query(
            db=db,
            email=email,
        )

        if existing_company is not None:
            return {
                "success": False,
                "status_code": status.HTTP_409_CONFLICT,
                "code": "COMPANY_EMAIL_ALREADY_EXISTS",
                "message": "A company already exists with this email.",
                "data": None,
            }

        company.email = email

    if name is not None:
        company.name = name

    if phone is not None:
        company.phone = phone

    if address is not None:
        company.address = address

    if gst_number is not None:
        company.gst_number = gst_number

    try:
        db.commit()
        db.refresh(company)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "COMPANY_UPDATED",
            "message": "Company updated successfully.",
            "data": company,
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "COMPANY_EMAIL_ALREADY_EXISTS",
            "message": "A company already exists with this email.",
            "data": None,
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong while updating the company.",
            "data": None,
        }
            

def deactivate_company(
    db: Session,
    company_id: UUID,
):

    company = get_company_by_id_query(
        db=db,
        company_id=company_id,
    )

    if company is None:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found.",
            "data": None,
        }

    company.is_active = False

    try:
        db.commit()
        db.refresh(company)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "COMPANY_DEACTIVATED",
            "message": "Company deactivated successfully.",
            "data": company,
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong while deactivating the company.",
            "data": None,
        }
            

def get_all_companies(
    db: Session,
):

    companies = get_all_companies_query(
        db=db,
    )

    if not companies:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_COMPANIES_FOUND",
            "message": "No companies found.",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "COMPANIES_FOUND",
        "message": "Companies retrieved successfully.",
        "data": companies,
    }


def activate_company(
    db: Session,
    company_id: UUID,
):

    company = get_company_by_id_admin_query(
        db=db,
        company_id=company_id,
    )

    if company is None:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found.",
            "data": None,
        }

    if company.is_active:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "COMPANY_ALREADY_ACTIVE",
            "message": "Company already active.",
            "data": None,
        }

    company.is_active = True

    try:
        db.commit()
        db.refresh(company)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "COMPANY_ACTIVATED",
            "message": "Company activated successfully.",
            "data": company,
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong while activating the company.",
            "data": None,
        }
        

def bulk_activate_companies(
    db: Session,
    company_ids: list[UUID],
):

    companies = get_companies_by_ids_query(
        db=db,
        company_ids=company_ids,
    )

    if not companies:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_COMPANIES_FOUND",
            "message": "No companies found.",
            "data": None,
        }

    already_active_companies = []
    activated_companies = []

    for company in companies:

        if company.is_active:
            already_active_companies.append(
                {
                    "id": str(company.id),
                    "name": company.name,
                }
            )
            continue

        company.is_active = True

        activated_companies.append(
            {
                "id": str(company.id),
                "name": company.name,
            }
        )

    if len(already_active_companies) == len(companies):
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "ALL_COMPANIES_ALREADY_ACTIVE",
            "message": "All companies are already active.",
            "data": {
                "companies": already_active_companies,
            },
        }

    try:
        db.commit()

        for company in companies:
            db.refresh(company)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "COMPANIES_ACTIVATED",
            "message": "Companies activated successfully.",
            "data": {
                "activated_companies": activated_companies,
                "already_active_companies": already_active_companies,
            },
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong while activating companies.",
            "data": None,
        }    

def bulk_deactivate_companies(
    db: Session,
    company_ids: list[UUID],
):

    companies = get_companies_by_ids_query(
        db=db,
        company_ids=company_ids,
    )

    if not companies:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "NO_COMPANIES_FOUND",
            "message": "No companies found.",
            "data": None,
        }

    already_inactive_companies = []
    deactivated_companies = []

    for company in companies:

        if not company.is_active:
            already_inactive_companies.append(
                {
                    "id": str(company.id),
                    "name": company.name,
                }
            )
            continue

        company.is_active = False

        deactivated_companies.append(
            {
                "id": str(company.id),
                "name": company.name,
            }
        )

    if len(already_inactive_companies) == len(companies):
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "ALL_COMPANIES_ALREADY_INACTIVE",
            "message": "All companies are already inactive.",
            "data": {
                "companies": already_inactive_companies,
            },
        }

    try:
        db.commit()

        for company in companies:
            db.refresh(company)

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "COMPANIES_DEACTIVATED",
            "message": "Companies deactivated successfully.",
            "data": {
                "deactivated_companies": deactivated_companies,
                "already_inactive_companies": already_inactive_companies,
            },
        }

    except Exception:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong while deactivating companies.",
            "data": None,
        }
    