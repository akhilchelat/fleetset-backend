from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.reusable_functions.report_reusable import get_report_data


def generate_daily_report_data(
    db: Session,
    company_id: UUID,
    report_date: date,
):
    """
    Generate report data for a single day.
    """

    report = get_report_data(
        db=db,
        company_id=company_id,
        start_date=report_date,
        end_date=report_date,
    )

    if report is None:
        return {
            "success": False,
            "message": "Company not found",
            "data": None,
        }

    return {
        "success": True,
        "message": "Daily report data generated successfully",
        "data": report,
    }


def generate_date_range_report_data(
    db: Session,
    company_id: UUID,
    start_date: date,
    end_date: date,
):
    """
    Generate report data for a date range.
    """

    if start_date > end_date:
        return {
            "success": False,
            "message": "Start date cannot be after end date",
            "data": None,
        }

    report = get_report_data(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
    )

    if report is None:
        return {
            "success": False,
            "message": "Company not found",
            "data": None,
        }

    return {
        "success": True,
        "message": "Report data generated successfully",
        "data": report,
    }


def generate_weekly_report_data(
    db: Session,
    company_id: UUID,
    week_start: date,
):
    """
    Generate report data for a complete week.

    The week starts on the supplied date and covers
    seven consecutive days.
    """

    week_end = week_start + timedelta(days=6)

    return generate_date_range_report_data(
        db=db,
        company_id=company_id,
        start_date=week_start,
        end_date=week_end,
    )


def generate_monthly_report_data(
    db: Session,
    company_id: UUID,
    year: int,
    month: int,
):
    """
    Generate report data for a complete calendar month.
    """

    if month < 1 or month > 12:
        return {
            "success": False,
            "message": "Month must be between 1 and 12",
            "data": None,
        }

    start_date = date(year, month, 1)

    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)

    end_date = next_month - timedelta(days=1)

    return generate_date_range_report_data(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
    )


def generate_yearly_report_data(
    db: Session,
    company_id: UUID,
    year: int,
):
    """
    Generate report data for a complete calendar year.
    """

    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    return generate_date_range_report_data(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
    )