from datetime import date
from uuid import UUID

from app.db.session import SessionLocal
from app.reusable_functions.report_reusable import get_report_data


db = SessionLocal()

try:
    # Replace this with your actual FleetSet Test Company UUID
    company_id = UUID("71e5af84-5611-4514-8413-69f12bbe8cd4")

    report = get_report_data(
        db=db,
        company_id=company_id,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 9),
    )

    if report is None:
        print("❌ Company not found")

    else:
        print("\n========== REPORT TEST ==========")

        print("Company:", report["company"].name)

        print(
            "Total Vehicles:",
            report["summary"]["total_vehicles"]
        )

        print(
            "Active Vehicles:",
            report["summary"]["active_vehicles"]
        )

        print(
            "Inactive Vehicles:",
            report["summary"]["inactive_vehicles"]
        )

        print(
            "Total Drivers:",
            report["summary"]["total_drivers"]
        )

        print(
            "Total Trips:",
            report["summary"]["total_trips"]
        )

        print(
            "Fuel Expense:",
            report["summary"]["total_fuel_expense"]
        )

        print(
            "Maintenance Expense:",
            report["summary"]["total_maintenance_expense"]
        )

        print(
            "Total Expense:",
            report["summary"]["total_expense"]
        )

        print("=================================\n")

finally:
    db.close()