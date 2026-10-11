from uuid import UUID

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.user import User

from app.reusable_functions.company_reusable import (
    get_company_by_email,
    get_company_by_email_query,
    get_company_by_id_query,
    get_company_by_id_admin_query,
    get_company_for_user_query,
    get_all_active_companies_query,
    get_all_companies_query,
    get_companies_by_ids_query,
)


def create_company(
    db: Session,
    current_user: User,
    name: str,
    email: str,
    phone: str | None = None,
    address: str | None = None,
    gst_number: str | None = None,
):
    if current_user.role.name != "GLOBAL_ADMIN":
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_CREATE_FORBIDDEN",
            "message": "Only GLOBAL_ADMIN can create companies",
            "data": None,
        }

    existing_company = get_company_by_email(db, email)

    if existing_company:
        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "COMPANY_EMAIL_EXISTS",
            "message": "A company with this email already exists",
            "data": None,
        }

    company = Company(
        name=name,
        email=email,
        phone=phone,
        address=address,
        gst_number=gst_number,
        is_active=True,
    )

    db.add(company)

    try:
        db.commit()
        db.refresh(company)
    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "COMPANY_ALREADY_EXISTS",
            "message": "Company information already exists",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "code": "COMPANY_CREATED",
        "message": "Company created successfully",
        "data": company,
    }


def find_company_by_id(
    db: Session,
    company_id: UUID,
    current_user: User,
):
    company = get_company_for_user_query(
        db=db,
        company_id=company_id,
        current_user=current_user,
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found",
            "data": None,
        }  

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "COMPANY_FOUND",
        "message": "Company retrieved successfully",
        "data": company,
    }


def find_company_by_email(
    db: Session,
    email: str,
    current_user: User,
):
    if current_user.role.name != "GLOBAL_ADMIN":
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_EMAIL_LOOKUP_FORBIDDEN",
            "message": "You do not have permission to search companies by email",
            "data": None,
        }

    company = get_company_by_email_query(
        db=db,
        email=email,
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "COMPANY_FOUND",
        "message": "Company retrieved successfully",
        "data": company,
    }


def get_all_active_companies(
    db: Session,
    current_user: User,
):
    if current_user.role.name != "GLOBAL_ADMIN":
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_LIST_FORBIDDEN",
            "message": "Only GLOBAL_ADMIN can access all companies",
            "data": None,
        }

    companies = get_all_active_companies_query(db)

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "COMPANIES_FOUND",
        "message": "Active companies retrieved successfully",
        "data": companies,
    }


def get_all_companies(
    db: Session,
    current_user: User,
):
    if current_user.role.name != "GLOBAL_ADMIN":
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_LIST_FORBIDDEN",
            "message": "Only GLOBAL_ADMIN can access all companies",
            "data": None,
        }

    companies = get_all_companies_query(db)

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "COMPANIES_FOUND",
        "message": "Companies retrieved successfully",
        "data": companies,
    }


def update_company(
    db: Session,
    company_id: UUID,
    current_user: User,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    address: str | None = None,
    gst_number: str | None = None,
):
    if current_user.role.name not in {
        "GLOBAL_ADMIN",
        "SUPER_ADMIN",
    }:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_UPDATE_FORBIDDEN",
            "message": "You do not have permission to update company information",
            "data": None,
        }

    company = get_company_for_user_query(
        db=db,
        company_id=company_id,
        current_user=current_user,
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found",
            "data": None,
        }

    if email is not None and email != company.email:
        existing_company = get_company_by_email(db, email)

        if existing_company and existing_company.id != company.id:
            return {
                "success": False,
                "status_code": status.HTTP_409_CONFLICT,
                "code": "COMPANY_EMAIL_EXISTS",
                "message": "A company with this email already exists",
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
    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "status_code": status.HTTP_409_CONFLICT,
            "code": "COMPANY_UPDATE_CONFLICT",
            "message": "Company information conflicts with existing data",
            "data": None,
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "COMPANY_UPDATED",
        "message": "Company updated successfully",
        "data": company,
    }


def deactivate_company(
    db: Session,
    company_id: UUID,
    current_user: User,
):
    if current_user.role.name != "GLOBAL_ADMIN":
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_DEACTIVATE_FORBIDDEN",
            "message": "Only GLOBAL_ADMIN can deactivate companies",
            "data": None,
        }

    company = get_company_by_id_admin_query(
        db=db,
        company_id=company_id,
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found",
            "data": None,
        }

    company.is_active = False

    db.commit()
    db.refresh(company)

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "COMPANY_DEACTIVATED",
        "message": "Company deactivated successfully",
        "data": company,
    }


def activate_company(
    db: Session,
    company_id: UUID,
    current_user: User,
):
    if current_user.role.name != "GLOBAL_ADMIN":
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_ACTIVATE_FORBIDDEN",
            "message": "Only GLOBAL_ADMIN can activate companies",
            "data": None,
        }

    company = get_company_by_id_admin_query(
        db=db,
        company_id=company_id,
    )

    if not company:
        return {
            "success": False,
            "status_code": status.HTTP_404_NOT_FOUND,
            "code": "COMPANY_NOT_FOUND",
            "message": "Company not found",
            "data": None,
        }

    company.is_active = True

    db.commit()
    db.refresh(company)

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "COMPANY_ACTIVATED",
        "message": "Company activated successfully",
        "data": company,
    }


def bulk_activate_companies(
    db: Session,
    company_ids: list[UUID],
    current_user: User,
):
    if current_user.role.name != "GLOBAL_ADMIN":
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_BULK_ACTION_FORBIDDEN",
            "message": "Only GLOBAL_ADMIN can perform bulk company actions",
            "data": None,
        }

    companies = get_companies_by_ids_query(
        db=db,
        company_ids=company_ids,
    )

    for company in companies:
        company.is_active = True

    db.commit()

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "COMPANIES_ACTIVATED",
        "message": "Companies activated successfully",
        "data": companies,
    }


def bulk_deactivate_companies(
    db: Session,
    company_ids: list[UUID],
    current_user: User,
):
    if current_user.role.name != "GLOBAL_ADMIN":
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_BULK_ACTION_FORBIDDEN",
            "message": "Only GLOBAL_ADMIN can perform bulk company actions",
            "data": None,
        }

    companies = get_companies_by_ids_query(
        db=db,
        company_ids=company_ids,
    )

    for company in companies:
        company.is_active = False

    db.commit()

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "code": "COMPANIES_DEACTIVATED",
        "message": "Companies deactivated successfully",
        "data": companies,
    }