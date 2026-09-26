from datetime import date
from uuid import UUID

from app.db.session import SessionLocal
from app.services.report_service import (
    generate_daily_report_data,
    generate_date_range_report_data,
    generate_monthly_report_data,
)


db = SessionLocal()

try:
    company_id = UUID("71e5af84-5611-4514-8413-69f12bbe8cd4")

    print("\n========== DAILY REPORT SERVICE ==========")

    daily_report = generate_daily_report_data(
        db=db,
        company_id=company_id,
        report_date=date(2026, 9, 9),
    )

    print("Success:", daily_report["success"])
    print("Message:", daily_report["message"])

    if daily_report["data"]:
        print(
            "Total Vehicles:",
            daily_report["data"]["summary"]["total_vehicles"],
        )

        print(
            "Total Drivers:",
            daily_report["data"]["summary"]["total_drivers"],
        )

        print(
            "Total Trips:",
            daily_report["data"]["summary"]["total_trips"],
        )

        print(
            "Total Expense:",
            daily_report["data"]["summary"]["total_expense"],
        )

    print("\n========== DATE RANGE REPORT SERVICE ==========")

    range_report = generate_date_range_report_data(
        db=db,
        company_id=company_id,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 9),
    )

    print("Success:", range_report["success"])
    print("Message:", range_report["message"])

    print("\n========== MONTHLY REPORT SERVICE ==========")

    monthly_report = generate_monthly_report_data(
        db=db,
        company_id=company_id,
        year=2026,
        month=9,
    )

    print("Success:", monthly_report["success"])
    print("Message:", monthly_report["message"])

    if monthly_report["data"]:
        print(
            "Total Vehicles:",
            monthly_report["data"]["summary"]["total_vehicles"],
        )

        print(
            "Total Drivers:",
            monthly_report["data"]["summary"]["total_drivers"],
        )

        print(
            "Total Trips:",
            monthly_report["data"]["summary"]["total_trips"],
        )

        print(
            "Fuel Expense:",
            monthly_report["data"]["summary"]["total_fuel_expense"],
        )

        print(
            "Maintenance Expense:",
            monthly_report["data"]["summary"]["total_maintenance_expense"],
        )

        print(
            "Total Expense:",
            monthly_report["data"]["summary"]["total_expense"],
        )

    print("\n============================================")

finally:
    db.close()