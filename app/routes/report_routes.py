from datetime import date
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.security.authorization import get_current_user

from app.services.report_service import (
    generate_daily_report_data,
    generate_date_range_report_data,
    generate_weekly_report_data,
    generate_monthly_report_data,
    generate_yearly_report_data,
)

from app.services.pdf_service import (
    generate_fleet_report_pdf,
)

from app.services.email_service import (
    send_report_email,
)


router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


# ============================================================
# REQUEST SCHEMAS
# ============================================================


class ReportPdfRequest(BaseModel):
    start_date: date
    end_date: date
    branch_id: UUID | None = None
    report_type: str = "Fleet Report"


class ReportEmailRequest(BaseModel):
    start_date: date
    end_date: date
    recipient_email: str
    branch_id: UUID | None = None
    report_type: str = "Fleet Report"


# ============================================================
# DAILY REPORT
# ============================================================


@router.get(
    "/{company_id}/daily",
)
def generate_daily_report(
    company_id: UUID,
    report_date: date = Query(...),
    branch_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = generate_daily_report_data(
        db=db,
        company_id=company_id,
        report_date=report_date,
        current_user=current_user,
        branch_id=branch_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result


# ============================================================
# DATE RANGE REPORT
# ============================================================


@router.get(
    "/{company_id}/date-range",
)
def generate_date_range_report(
    company_id: UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    branch_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = generate_date_range_report_data(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
        current_user=current_user,
        branch_id=branch_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result


# ============================================================
# WEEKLY REPORT
# ============================================================


@router.get(
    "/{company_id}/weekly",
)
def generate_weekly_report(
    company_id: UUID,
    week_start: date = Query(...),
    branch_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = generate_weekly_report_data(
        db=db,
        company_id=company_id,
        week_start=week_start,
        current_user=current_user,
        branch_id=branch_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result


# ============================================================
# MONTHLY REPORT
# ============================================================


@router.get(
    "/{company_id}/monthly",
)
def generate_monthly_report(
    company_id: UUID,
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    branch_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = generate_monthly_report_data(
        db=db,
        company_id=company_id,
        year=year,
        month=month,
        current_user=current_user,
        branch_id=branch_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result


# ============================================================
# YEARLY REPORT
# ============================================================


@router.get(
    "/{company_id}/yearly",
)
def generate_yearly_report(
    company_id: UUID,
    year: int = Query(..., ge=2000, le=2100),
    branch_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = generate_yearly_report_data(
        db=db,
        company_id=company_id,
        year=year,
        current_user=current_user,
        branch_id=branch_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    return result


# ============================================================
# DOWNLOAD PDF REPORT
# ============================================================


@router.post(
    "/{company_id}/custom/pdf",
)
def download_custom_pdf_report(
    company_id: UUID,
    payload: ReportPdfRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Generate the same report data used by the Reports page.
    result = generate_date_range_report_data(
        db=db,
        company_id=company_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        current_user=current_user,
        branch_id=payload.branch_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    report_data = result["data"]

    # Generate the PDF using the existing PDF service.
    pdf_path = generate_fleet_report_pdf(
        report_data=report_data,
        report_type=payload.report_type,
    )

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Report PDF was not generated",
        )

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=pdf_path.name,
        headers={
            "Content-Disposition": (
                f'attachment; filename="{pdf_path.name}"'
            )
        },
    )


# ============================================================
# SEND REPORT BY EMAIL
# ============================================================


@router.post(
    "/{company_id}/custom/email",
)
def email_custom_report(
    company_id: UUID,
    payload: ReportEmailRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Generate the same report data used by the Reports page.
    result = generate_date_range_report_data(
        db=db,
        company_id=company_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        current_user=current_user,
        branch_id=payload.branch_id,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["message"],
        )

    report_data = result["data"]

    # Generate the PDF using the existing PDF service.
    pdf_path = generate_fleet_report_pdf(
        report_data=report_data,
        report_type=payload.report_type,
    )

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Report PDF was not generated",
        )

    # Send the generated PDF using the existing email service.
    email_result = send_report_email(
        recipient_email=payload.recipient_email,
        pdf_path=pdf_path,
        subject=(
            f"FleetSet Report - "
            f"{payload.start_date.strftime('%d %b %Y')} to "
            f"{payload.end_date.strftime('%d %b %Y')}"
        ),
        body=(
            "Hello,\n\n"
            "Please find your FleetSet report attached.\n\n"
            f"Report Period: "
            f"{payload.start_date.strftime('%d %b %Y')} - "
            f"{payload.end_date.strftime('%d %b %Y')}\n\n"
            "This report was generated by FleetSet.\n\n"
            "Regards,\n"
            "FleetSet"
        ),
    )

    if not email_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=email_result["message"],
        )

    return {
        "success": True,
        "status_code": 200,
        "code": "REPORT_EMAIL_SENT",
        "message": "Report email sent successfully",
        "data": {
            "recipient_email": payload.recipient_email,
            "filename": pdf_path.name,
        },
    }