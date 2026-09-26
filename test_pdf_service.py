from datetime import date
from uuid import UUID

from app.db.session import SessionLocal
from app.reusable_functions.report_reusable import get_report_data
from app.services.pdf_service import generate_fleet_report_pdf


db = SessionLocal()

try:
    company_id = UUID("71e5af84-5611-4514-8413-69f12bbe8cd4")

    start_date = date(2026, 9, 1)
    end_date = date(2026, 9, 9)

    report_data = get_report_data(
        db=db,
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
    )

    if report_data is None:
        print("❌ Company not found")

    else:
        # Add report period information for the PDF generator
        report_data["start_date"] = start_date
        report_data["end_date"] = end_date

        print("Report data loaded successfully.")

        print(
            "Vehicles:",
            len(report_data.get("vehicles", []))
        )

        print(
            "Drivers:",
            len(report_data.get("drivers", []))
        )

        print(
            "Trips:",
            len(report_data.get("trips", []))
        )

        print(
            "Fuel logs:",
            len(report_data.get("fuel_logs", []))
        )

        print(
            "Maintenance records:",
            len(report_data.get("maintenance_records", []))
        )

        pdf_path = generate_fleet_report_pdf(
            report_data=report_data,
            report_type="FleetSet Fleet Report",
        )

        print("\n========== PDF GENERATED ==========")
        print("PDF:", pdf_path)
        print("===================================\n")

finally:
    db.close()