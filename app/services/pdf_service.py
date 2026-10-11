from datetime import datetime
from decimal import Decimal
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


REPORTS_DIR = Path("generated_reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _money(value):
    if value is None:
        value = Decimal("0.00")

    return f"₹ {Decimal(value):,.2f}"


def _safe(value):
    if value is None:
        return "-"

    return str(value)


def _get_period(report_data):
    period = report_data.get("period")

    if isinstance(period, dict):
        return (
            period.get("start_date"),
            period.get("end_date"),
        )

    return (
        report_data.get("start_date"),
        report_data.get("end_date"),
    )


def _get_driver_name(driver):
    if not driver:
        return "-"

    user = getattr(driver, "user", None)

    if user:
        first_name = getattr(user, "first_name", "") or ""
        last_name = getattr(user, "last_name", "") or ""

        full_name = f"{first_name} {last_name}".strip()

        if full_name:
            return full_name

    first_name = getattr(driver, "first_name", "") or ""
    last_name = getattr(driver, "last_name", "") or ""

    full_name = f"{first_name} {last_name}".strip()

    return full_name or "-"


def _get_vehicle_number(vehicle):
    if not vehicle:
        return "-"

    return _safe(
        getattr(vehicle, "registration_number", None)
    )


def _safe_filename(value):
    value = str(value or "Company")

    allowed = []

    for character in value:
        if character.isalnum() or character in (" ", "-", "_"):
            allowed.append(character)

    cleaned = "".join(allowed).strip()

    return cleaned.replace(" ", "_") or "Company"


def _add_page_number(canvas, document):
    canvas.saveState()

    canvas.setFont("Helvetica", 8)

    canvas.drawRightString(
        A4[0] - 15 * mm,
        8 * mm,
        f"Page {document.page}",
    )

    canvas.restoreState()


def generate_fleet_report_pdf(
    report_data: dict,
    report_type: str = "Fleet Report",
):
    company = report_data["company"]
    summary = report_data["summary"]

    start_date, end_date = _get_period(report_data)

    branch_id = report_data.get("branch_id")

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    company_name = _safe_filename(
        getattr(company, "name", "Company")
    )

    if branch_id:
        file_name = (
            f"FleetSet_{company_name}_"
            f"Branch_{str(branch_id)[:8]}_"
            f"{start_date}_{end_date}_"
            f"{timestamp}.pdf"
        )
    else:
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

    story = []

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

    report_scope = (
        "Branch Report"
        if branch_id
        else "Company-wide Report"
    )

    company_info = [
        [
            "Company",
            _safe(getattr(company, "name", None)),
        ],
        [
            "Email",
            _safe(getattr(company, "email", None)),
        ],
        [
            "Phone",
            _safe(getattr(company, "phone", None)),
        ],
        [
            "Report",
            _safe(report_type),
        ],
        [
            "Scope",
            report_scope,
        ],
        [
            "Branch ID",
            _safe(branch_id) if branch_id else "All Branches",
        ],
        [
            "Period",
            f"{_safe(start_date)} to {_safe(end_date)}",
        ],
    ]

    company_table = Table(
        company_info,
        colWidths=[35 * mm, 145 * mm],
    )

    company_table.setStyle(
        TableStyle(
            [
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, -1),
                    "Helvetica",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.lightgrey,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(company_table)
    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "1. Fleet Summary",
            heading_style,
        )
    )

    summary_data = [
        ["Metric", "Value"],
        [
            "Total Vehicles",
            summary["total_vehicles"],
        ],
        [
            "Active Vehicles",
            summary["active_vehicles"],
        ],
        [
            "Inactive Vehicles",
            summary["inactive_vehicles"],
        ],
        [
            "Total Drivers",
            summary["total_drivers"],
        ],
        [
            "Total Trips",
            summary["total_trips"],
        ],
        [
            "Fuel Expense",
            _money(summary["total_fuel_expense"]),
        ],
        [
            "Maintenance Expense",
            _money(
                summary["total_maintenance_expense"]
            ),
        ],
        [
            "Total Expense",
            _money(summary["total_expense"]),
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[110 * mm, 70 * mm],
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1f2937"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (0, -1),
                    (-1, -1),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "ALIGN",
                    (1, 1),
                    (1, -1),
                    "RIGHT",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(summary_table)
    story.append(Spacer(1, 12))

    vehicles = report_data.get(
        "vehicles",
        [],
    )

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
                _safe(
                    getattr(
                        vehicle,
                        "registration_number",
                        None,
                    )
                ),
                _safe(
                    getattr(
                        vehicle,
                        "manufacturer",
                        None,
                    )
                ),
                _safe(
                    getattr(
                        vehicle,
                        "model",
                        None,
                    )
                ),
                _safe(
                    getattr(
                        vehicle,
                        "vehicle_type",
                        None,
                    )
                ),
                _safe(
                    getattr(
                        vehicle,
                        "status",
                        None,
                    )
                ),
            ]
        )

    if len(vehicle_rows) == 1:
        vehicle_rows.append(
            [
                "No vehicle data",
                "-",
                "-",
                "-",
                "-",
            ]
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
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1f2937"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(vehicle_table)
    story.append(Spacer(1, 12))

    trips = report_data.get(
        "trips",
        [],
    )

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
        trip_vehicle = getattr(
            trip,
            "vehicle",
            None,
        )

        trip_driver = getattr(
            trip,
            "driver",
            None,
        )

        trip_rows.append(
            [
                _safe(
                    getattr(
                        trip,
                        "origin",
                        None,
                    )
                ),
                _safe(
                    getattr(
                        trip,
                        "destination",
                        None,
                    )
                ),
                _get_vehicle_number(
                    trip_vehicle
                ),
                _get_driver_name(
                    trip_driver
                ),
                _safe(
                    getattr(
                        trip,
                        "status",
                        None,
                    )
                ),
            ]
        )

    if len(trip_rows) == 1:
        trip_rows.append(
            [
                "No trips",
                "-",
                "-",
                "-",
                "-",
            ]
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
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1f2937"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(trip_table)
    story.append(Spacer(1, 12))

    fuel_logs = report_data.get(
        "fuel_logs",
        [],
    )

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
        fuel_vehicle = getattr(
            fuel,
            "vehicle",
            None,
        )

        fuel_driver = getattr(
            fuel,
            "driver",
            None,
        )

        fuel_rows.append(
            [
                _safe(
                    getattr(
                        fuel,
                        "fuel_date",
                        None,
                    )
                ),
                _get_vehicle_number(
                    fuel_vehicle
                ),
                _get_driver_name(
                    fuel_driver
                ),
                _money(
                    getattr(
                        fuel,
                        "fuel_cost",
                        None,
                    )
                ),
            ]
        )

    if len(fuel_rows) == 1:
        fuel_rows.append(
            [
                "No fuel records",
                "-",
                "-",
                _money(0),
            ]
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
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1f2937"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "ALIGN",
                    (-1, 1),
                    (-1, -1),
                    "RIGHT",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(fuel_table)
    story.append(Spacer(1, 12))

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
        maintenance_vehicle = getattr(
            maintenance,
            "vehicle",
            None,
        )

        maintenance_rows.append(
            [
                _safe(
                    getattr(
                        maintenance,
                        "service_date",
                        None,
                    )
                ),
                _get_vehicle_number(
                    maintenance_vehicle
                ),
                _safe(
                    getattr(
                        maintenance,
                        "maintenance_type",
                        None,
                    )
                ),
                _safe(
                    getattr(
                        maintenance,
                        "garage_name",
                        None,
                    )
                ),
                _money(
                    getattr(
                        maintenance,
                        "cost",
                        None,
                    )
                ),
            ]
        )

    if len(maintenance_rows) == 1:
        maintenance_rows.append(
            [
                "No maintenance records",
                "-",
                "-",
                "-",
                _money(0),
            ]
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
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1f2937"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "ALIGN",
                    (-1, 1),
                    (-1, -1),
                    "RIGHT",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(maintenance_table)
    story.append(Spacer(1, 15))

    generated_at = datetime.now().strftime(
        "%d-%m-%Y %I:%M %p"
    )

    story.append(
        Paragraph(
            f"Generated by FleetSet on {generated_at}",
            subtitle_style,
        )
    )

    document.build(
        story,
        onFirstPage=_add_page_number,
        onLaterPages=_add_page_number,
    )

    return file_path