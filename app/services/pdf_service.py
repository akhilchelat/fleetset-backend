from datetime import datetime
from decimal import Decimal
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


REPORTS_DIR = Path("generated_reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _money(value):
    """Format Decimal/number as Indian Rupee amount."""
    if value is None:
        value = Decimal("0.00")

    return f"₹ {Decimal(value):,.2f}"


def _safe(value):
    """Convert None to a printable value."""
    return "-" if value is None else str(value)


def generate_fleet_report_pdf(report_data: dict, report_type: str = "Fleet Report"):
    """
    Generate a FleetSet PDF report from already prepared report data.

    Parameters:
        report_data: Dictionary returned by get_report_data()
        report_type: Name displayed in the PDF

    Returns:
        Path to generated PDF
    """

    company = report_data["company"]
    summary = report_data["summary"]

    start_date = report_data["start_date"]
    end_date = report_data["end_date"]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    company_name = company.name.replace(" ", "_")

    file_name = (
        f"FleetSet_{company_name}_"
        f"{start_date}_{end_date}_"
        f"{timestamp}.pdf"
    )

    file_path = REPORTS_DIR / file_name

    document = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "FleetSetTitle",
        parent=styles["Title"],
        fontSize=22,
        leading=26,
        alignment=TA_CENTER,
        spaceAfter=5,
    )

    subtitle_style = ParagraphStyle(
        "FleetSetSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        spaceAfter=12,
    )

    heading_style = ParagraphStyle(
        "FleetSetHeading",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        spaceBefore=10,
        spaceAfter=8,
    )

    normal_style = ParagraphStyle(
        "FleetSetNormal",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
    )

    right_style = ParagraphStyle(
        "FleetSetRight",
        parent=normal_style,
        alignment=TA_RIGHT,
    )

    story = []

    # ==========================================================
    # HEADER
    # ==========================================================

    story.append(
        Paragraph(
            "FLEETSET",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "Fleet Management & Reporting",
            subtitle_style,
        )
    )

    company_info = [
        ["Company", _safe(company.name)],
        ["Email", _safe(company.email)],
        ["Phone", _safe(company.phone)],
        ["Report", _safe(report_type)],
        ["Period", f"{start_date} to {end_date}"],
    ]

    company_table = Table(
        company_info,
        colWidths=[35 * mm, 145 * mm],
    )

    company_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(company_table)
    story.append(Spacer(1, 12))

    # ==========================================================
    # SUMMARY
    # ==========================================================

    story.append(
        Paragraph(
            "1. Fleet Summary",
            heading_style,
        )
    )

    summary_data = [
        ["Metric", "Value"],
        ["Total Vehicles", summary["total_vehicles"]],
        ["Active Vehicles", summary["active_vehicles"]],
        ["Inactive Vehicles", summary["inactive_vehicles"]],
        ["Total Drivers", summary["total_drivers"]],
        ["Total Trips", summary["total_trips"]],
        ["Fuel Expense", _money(summary["total_fuel_expense"])],
        [
            "Maintenance Expense",
            _money(summary["total_maintenance_expense"]),
        ],
        ["Total Expense", _money(summary["total_expense"])],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[110 * mm, 70 * mm],
    )

    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(summary_table)
    story.append(Spacer(1, 12))

    # ==========================================================
    # VEHICLES
    # ==========================================================

    vehicles = report_data.get("vehicles", [])

    story.append(
        Paragraph(
            "2. Vehicle Overview",
            heading_style,
        )
    )

    vehicle_rows = [
        [
            "Registration",
            "Manufacturer",
            "Model",
            "Type",
            "Status",
        ]
    ]

    for vehicle in vehicles:
        vehicle_rows.append(
            [
                _safe(vehicle.registration_number),
                _safe(vehicle.manufacturer),
                _safe(vehicle.model),
                _safe(vehicle.vehicle_type),
                _safe(vehicle.status),
            ]
        )

    if len(vehicle_rows) == 1:
        vehicle_rows.append(
            ["No vehicle data", "-", "-", "-", "-"]
        )

    vehicle_table = Table(
        vehicle_rows,
        colWidths=[
            35 * mm,
            35 * mm,
            35 * mm,
            35 * mm,
            40 * mm,
        ],
        repeatRows=1,
    )

    vehicle_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    story.append(vehicle_table)
    story.append(Spacer(1, 12))

    # ==========================================================
    # TRIPS
    # ==========================================================

    trips = report_data.get("trips", [])

    story.append(
        Paragraph(
            "3. Trip Activity",
            heading_style,
        )
    )

    trip_rows = [
        [
            "Origin",
            "Destination",
            "Vehicle",
            "Driver",
            "Status",
        ]
    ]

    for trip in trips:
        vehicle_number = (
            trip.vehicle.registration_number
            if trip.vehicle
            else "-"
        )

        driver_name = "-"

        if trip.driver:
            driver_name = (
                f"{trip.driver.first_name} "
                f"{trip.driver.last_name or ''}"
            ).strip()

        trip_rows.append(
            [
                _safe(trip.origin),
                _safe(trip.destination),
                vehicle_number,
                driver_name,
                _safe(trip.status),
            ]
        )

    if len(trip_rows) == 1:
        trip_rows.append(
            ["No trips", "-", "-", "-", "-"]
        )

    trip_table = Table(
        trip_rows,
        colWidths=[
            35 * mm,
            35 * mm,
            35 * mm,
            40 * mm,
            35 * mm,
        ],
        repeatRows=1,
    )

    trip_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    story.append(trip_table)
    story.append(Spacer(1, 12))

    # ==========================================================
    # FUEL
    # ==========================================================

    fuel_logs = report_data.get("fuel_logs", [])

    story.append(
        Paragraph(
            "4. Fuel Expenses",
            heading_style,
        )
    )

    fuel_rows = [
        [
            "Date",
            "Vehicle",
            "Driver",
            "Fuel Cost",
        ]
    ]

    for fuel in fuel_logs:
        vehicle_number = (
            fuel.vehicle.registration_number
            if fuel.vehicle
            else "-"
        )

        driver_name = "-"

        if fuel.driver:
            driver_name = (
                f"{fuel.driver.first_name} "
                f"{fuel.driver.last_name or ''}"
            ).strip()

        fuel_rows.append(
            [
                _safe(fuel.fuel_date),
                vehicle_number,
                driver_name,
                _money(fuel.fuel_cost),
            ]
        )

    if len(fuel_rows) == 1:
        fuel_rows.append(
            ["No fuel records", "-", "-", _money(0)]
        )

    fuel_table = Table(
        fuel_rows,
        colWidths=[
            35 * mm,
            50 * mm,
            50 * mm,
            45 * mm,
        ],
        repeatRows=1,
    )

    fuel_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    story.append(fuel_table)
    story.append(Spacer(1, 12))

    # ==========================================================
    # MAINTENANCE
    # ==========================================================

    maintenance_records = report_data.get(
        "maintenance_records",
        [],
    )

    story.append(
        Paragraph(
            "5. Maintenance Expenses",
            heading_style,
        )
    )

    maintenance_rows = [
        [
            "Date",
            "Vehicle",
            "Type",
            "Garage",
            "Cost",
        ]
    ]

    for maintenance in maintenance_records:
        vehicle_number = (
            maintenance.vehicle.registration_number
            if maintenance.vehicle
            else "-"
        )

        maintenance_rows.append(
            [
                _safe(maintenance.service_date),
                vehicle_number,
                _safe(maintenance.maintenance_type),
                _safe(maintenance.garage_name),
                _money(maintenance.cost),
            ]
        )

    if len(maintenance_rows) == 1:
        maintenance_rows.append(
            ["No maintenance records", "-", "-", "-", _money(0)]
        )

    maintenance_table = Table(
        maintenance_rows,
        colWidths=[
            30 * mm,
            40 * mm,
            40 * mm,
            40 * mm,
            30 * mm,
        ],
        repeatRows=1,
    )

    maintenance_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    story.append(maintenance_table)
    story.append(Spacer(1, 15))

    # ==========================================================
    # FOOTER INFORMATION
    # ==========================================================

    generated_at = datetime.now().strftime(
        "%d-%m-%Y %I:%M %p"
    )

    story.append(
        Paragraph(
            f"Generated by FleetSet on {generated_at}",
            subtitle_style,
        )
    )

    document.build(story)

    return file_path