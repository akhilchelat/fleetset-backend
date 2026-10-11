from datetime import date, timedelta
from uuid import UUID

from fastapi import status
from sqlalchemy.orm import Session

from app.reusable_functions.report_reusable import get_report_data


MANAGEMENT_ROLES = {
    "GLOBAL_ADMIN",
    "SUPER_ADMIN",
    "BRANCH_ADMIN",
}


def _get_role_name(current_user) -> str | None:
    if not current_user or not current_user.role:
        return None

    return current_user.role.name


def _check_report_access(
    current_user,
    company_id: UUID,
    branch_id: UUID | None = None,
):
    role_name = _get_role_name(current_user)

    if role_name is None:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "ROLE_NOT_FOUND",
            "message": "User role not found",
            "data": None,
        }

    if role_name not in MANAGEMENT_ROLES:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "REPORT_ACCESS_DENIED",
            "message": "You do not have permission to generate reports",
            "data": None,
        }

    if role_name == "GLOBAL_ADMIN":
        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "REPORT_ACCESS_GRANTED",
            "message": "Report access granted",
            "data": None,
        }

    if current_user.company_id != company_id:
        return {
            "success": False,
            "status_code": status.HTTP_403_FORBIDDEN,
            "code": "COMPANY_ACCESS_DENIED",
            "message": "You do not have access to this company",
            "data": None,
        }

    if role_name == "SUPER_ADMIN":
        if branch_id is not None:
            if current_user.branch_id is not None:
                return {
                    "success": False,
                    "status_code": status.HTTP_403_FORBIDDEN,
                    "code": "BRANCH_ACCESS_DENIED",
                    "message": "You do not have permission to access this branch",
                    "data": None,
                }

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "REPORT_ACCESS_GRANTED",
            "message": "Report access granted",
            "data": None,
        }

    if role_name == "BRANCH_ADMIN":
        if current_user.branch_id is None:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "BRANCH_NOT_ASSIGNED",
                "message": "Branch admin is not assigned to a branch",
                "data": None,
            }

        if branch_id is not None and branch_id != current_user.branch_id:
            return {
                "success": False,
                "status_code": status.HTTP_403_FORBIDDEN,
                "code": "BRANCH_ACCESS_DENIED",
                "message": "You can only generate reports for your own branch",
                "data": None,
            }

        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "code": "REPORT_ACCESS_GRANTED",
            "message": "Report access granted",
            "data": None,
        }

    return {
        "success": False,
        "status_code": status.HTTP_403_FORBIDDEN,
        "code": "REPORT_ACCESS_DENIED",
        "message": "You do not have permission to generate reports",
        "data": None,
    }


def _resolve_branch_id(
    current_user,
    branch_id: UUID | None,
) -> UUID | None:
    role_name = _get_role_name(current_user)

    if role_name == "BRANCH_ADMIN":
        return current_user.branch_id

    return branch_id


def generate_daily_report_data(
    db: Session,
    company_id: UUID,
    report_date: date,
    current_user,
    branch_id: UUID | None = None,
):
    resolved_branch_id = _resolve_branch_id(
        current_user=current_user,
        branch_id=branch_id,
    )

    access = _check_report_access(
        current_user=current_user,
        company_id=company_id,
        branch_id=resolved_branch_id,
    )

    if not access["success"]:
        return access

    report = get_report_data(
        db=db,
        company_id=company_id,
        start_date=report_date,
        end_date=report_date,
        branch_id=resolved_branch_id,
    )

    if report is None:
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
        "code": "DAILY_REPORT_GENERATED",
        "message": "Daily report data generated successfully",
        "data": report,
    }


def generate_date_range_report_data(
    db: Session,
    company_id: UUID,
    start_date: date,
    end_date: date,
    current_user,
    branch_id: UUID | None = None,
):
    if start_date > end_date:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_DATE_RANGE",
            "message": "Start date cannot be after end date",
            "data": None,
        }

    resolved_branch_id = _resolve_branch_id(
        current_user=current_user,
        branch_id=branch_id,
    )

    access = _check_report_access(
        current_user=current_user,
        company_id=company_id,
        branch_id=resolved_branch_id,
    )

    if not access["success"]:
        return access

    report = get_report_data(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
        branch_id=resolved_branch_id,
    )

    if report is None:
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
        "code": "REPORT_GENERATED",
        "message": "Report data generated successfully",
        "data": report,
    }


def generate_weekly_report_data(
    db: Session,
    company_id: UUID,
    week_start: date,
    current_user,
    branch_id: UUID | None = None,
):
    week_end = week_start + timedelta(days=6)

    return generate_date_range_report_data(
        db=db,
        company_id=company_id,
        start_date=week_start,
        end_date=week_end,
        current_user=current_user,
        branch_id=branch_id,
    )


def generate_monthly_report_data(
    db: Session,
    company_id: UUID,
    year: int,
    month: int,
    current_user,
    branch_id: UUID | None = None,
):
    if month < 1 or month > 12:
        return {
            "success": False,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "code": "INVALID_MONTH",
            "message": "Month must be between 1 and 12",
            "data": None,
        }

    start_date = date(
        year,
        month,
        1,
    )

    if month == 12:
        next_month = date(
            year + 1,
            1,
            1,
        )
    else:
        next_month = date(
            year,
            month + 1,
            1,
        )

    end_date = next_month - timedelta(days=1)

    return generate_date_range_report_data(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
        current_user=current_user,
        branch_id=branch_id,
    )


def generate_yearly_report_data(
    db: Session,
    company_id: UUID,
    year: int,
    current_user,
    branch_id: UUID | None = None,
):
    start_date = date(
        year,
        1,
        1,
    )

    end_date = date(
        year,
        12,
        31,
    )

    return generate_date_range_report_data(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
        current_user=current_user,
        branch_id=branch_id,
    )