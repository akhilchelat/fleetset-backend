from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.services.report_service import (
    generate_daily_report_data,
    generate_weekly_report_data,
    generate_monthly_report_data,
    generate_yearly_report_data,
    generate_date_range_report_data,
)

from app.services.pdf_service import generate_fleet_report_pdf
from app.services.email_service import send_report_email

from app.schemas.report_schema import (
    ReportRequest,
    ReportEmailRequest,
)

from app.security.authorization import get_current_user


router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


def verify_company_access(
    company_id: UUID,
    current_user,
):
    if current_user.company_id != company_id:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to access this company report",
        )


# ============================================================
# DAILY REPORT
# ============================================================

@router.get("/{company_id}/daily")
def get_daily_report(
    company_id: UUID,
    report_date: date,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    verify_company_access(
        company_id=company_id,
        current_user=current_user,
    )

    return generate_daily_report_data(
        db=db,
        company_id=company_id,
        report_date=report_date,
    )


# ============================================================
# WEEKLY REPORT
# ============================================================

@router.get("/{company_id}/weekly")
def get_weekly_report(
    company_id: UUID,
    week_start: date,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    verify_company_access(
        company_id=company_id,
        current_user=current_user,
    )

    return generate_weekly_report_data(
        db=db,
        company_id=company_id,
        week_start=week_start,
    )


# ============================================================
# MONTHLY REPORT
# ============================================================

@router.get("/{company_id}/monthly")
def get_monthly_report(
    company_id: UUID,
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    verify_company_access(
        company_id=company_id,
        current_user=current_user,
    )

    return generate_monthly_report_data(
        db=db,
        company_id=company_id,
        year=year,
        month=month,
    )


# ============================================================
# YEARLY REPORT
# ============================================================

@router.get("/{company_id}/yearly")
def get_yearly_report(
    company_id: UUID,
    year: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    verify_company_access(
        company_id=company_id,
        current_user=current_user,
    )

    return generate_yearly_report_data(
        db=db,
        company_id=company_id,
        year=year,
    )


# ============================================================
# CUSTOM DATE RANGE REPORT
# ============================================================

@router.post("/{company_id}/custom")
def get_custom_report(
    company_id: UUID,
    request: ReportRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    verify_company_access(
        company_id=company_id,
        current_user=current_user,
    )

    return generate_date_range_report_data(
        db=db,
        company_id=company_id,
        start_date=request.start_date,
        end_date=request.end_date,
    )


# ============================================================
# CUSTOM REPORT PDF
# ============================================================

@router.post("/{company_id}/custom/pdf")
def generate_custom_report_pdf(
    company_id: UUID,
    request: ReportRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    verify_company_access(
        company_id=company_id,
        current_user=current_user,
    )

    result = generate_date_range_report_data(
        db=db,
        company_id=company_id,
        start_date=request.start_date,
        end_date=request.end_date,
    )

    if not result["success"]:
        return result

    report_data = result["data"]

    report_data["start_date"] = request.start_date
    report_data["end_date"] = request.end_date

    pdf_path = generate_fleet_report_pdf(
        report_data=report_data,
        report_type="FleetSet Fleet Report",
    )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=pdf_path.name,
    )


# ============================================================
# CUSTOM REPORT EMAIL
# ============================================================

@router.post("/{company_id}/custom/email")
def send_custom_report_email(
    company_id: UUID,
    request: ReportEmailRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    verify_company_access(
        company_id=company_id,
        current_user=current_user,
    )

    if request.start_date > request.end_date:
        return {
            "success": False,
            "message": "Start date cannot be after end date",
        }

    result = generate_date_range_report_data(
        db=db,
        company_id=company_id,
        start_date=request.start_date,
        end_date=request.end_date,
    )

    if not result["success"]:
        return result

    report_data = result["data"]

    report_data["start_date"] = request.start_date
    report_data["end_date"] = request.end_date

    pdf_path = generate_fleet_report_pdf(
        report_data=report_data,
        report_type="FleetSet Fleet Report",
    )

    recipient_email = (
        request.recipient_email
        if request.recipient_email
        else current_user.email
    )

    subject = (
        f"FleetSet Report - "
        f"{request.start_date} to {request.end_date}"
    )

    body = (
        f"Hello {current_user.first_name},\n\n"
        f"Please find attached your FleetSet fleet report.\n\n"
        f"Report period: "
        f"{request.start_date} to {request.end_date}\n\n"
        f"Regards,\n"
        f"FleetSet"
    )

    email_result = send_report_email(
        recipient_email=str(recipient_email),
        pdf_path=pdf_path,
        subject=subject,
        body=body,
    )

    if not email_result["success"]:
        return email_result

    return {
        "success": True,
        "message": "FleetSet report sent successfully by email",
        "recipient_email": recipient_email,
        "file_name": pdf_path.name,
    }