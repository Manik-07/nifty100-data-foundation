"""
portfolio_summary.py

Sprint 5 - Day 35
Portfolio Summary PDF

Creates one page per company in alphabetical ticker order.

Each page contains:
- Company name
- Ticker
- Sector
- Six latest-year KPIs
- Trend arrows comparing latest year with previous year

Trend:
    ↑ = improved
    ↓ = declined
    → = flat within 2%
"""

from pathlib import Path
import sqlite3
import math

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
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


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DB_PATH = ROOT / "db" / "nifty100.db"

OUTPUT_DIR = ROOT / "reports" / "portfolio"
OUTPUT_PATH = OUTPUT_DIR / "portfolio_summary.pdf"


# ============================================================
# CONFIGURATION
# ============================================================

KPI_COLUMNS = {
    "ROE": "return_on_equity_pct",
    "ROCE": "roce_percentage",
    "OPM": "operating_profit_margin_pct",
    "D/E": "debt_to_equity",
    "FCF": "free_cash_flow_cr",
    "EPS": "earnings_per_share",
}


# ============================================================
# HELPERS
# ============================================================

def clean_value(value):
    """Convert SQLite/Pandas values into safe numeric values."""

    if value is None:
        return None

    try:
        value = float(value)

        if math.isnan(value):
            return None

        return value

    except (TypeError, ValueError):
        return None


def format_value(kpi, value):
    """Format KPI values for display."""

    value = clean_value(value)

    if value is None:
        return "N/A"

    if kpi in {"ROE", "ROCE", "OPM"}:
        return f"{value:.2f}%"

    if kpi == "D/E":
        return f"{value:.2f}x"

    if kpi == "FCF":
        return f"{value:,.0f} Cr"

    if kpi == "EPS":
        return f"{value:,.2f}"

    return f"{value:.2f}"


def trend_arrow(current, previous):
    """
    Determine trend.

    Flat means change is within +/-2%.

    For most KPIs:
        higher = improvement
        lower  = decline

    For D/E:
        lower = improvement
        higher = decline
    """

    current = clean_value(current)
    previous = clean_value(previous)

    if current is None or previous is None:
        return "→"

    # Special handling for D/E
    if previous == 0:
        if current == 0:
            return "→"

        if current < 0:
            return "↑"

        return "↓"

    change_pct = ((current - previous) / abs(previous)) * 100

    if abs(change_pct) <= 2:
        return "→"

    if current > previous:
        return "↓" if False else "↑"

    return "↓"


def get_sorted_years(df):
    """Sort financial years chronologically."""

    if df.empty:
        return []

    temp = df.copy()

    # Extract numeric year from strings such as:
    # Mar 2024
    # Dec 2023
    # Sep 2022
    temp["_year_num"] = (
        temp["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0]
        .astype(float)
    )

    temp = temp.sort_values(
        by=["_year_num", "year"],
        ascending=True
    )

    return temp["year"].tolist()


# ============================================================
# DATABASE
# ============================================================

def load_company_data():
    """Load companies, sectors and financial ratios."""

    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql_query(
        """
        SELECT
            id AS company_id,
            company_name,
            roe_percentage
        FROM companies
        ORDER BY id
        """,
        conn,
    )

    sectors = pd.read_sql_query(
        """
        SELECT
            company_id,
            broad_sector
        FROM sectors
        """,
        conn,
    )

    ratios = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            operating_profit_margin_pct,
            return_on_equity_pct,
            debt_to_equity,
            free_cash_flow_cr,
            earnings_per_share
        FROM financial_ratios
        """,
        conn,
    )

    conn.close()

    # --------------------------------------------------------
    # ROCE is stored in companies table, while the remaining
    # KPIs are available in financial_ratios.
    # --------------------------------------------------------

    companies["roce_percentage"] = companies["company_id"].map(
        dict(
            pd.read_sql_query(
                """
                SELECT id, roce_percentage
                FROM companies
                """,
                sqlite3.connect(DB_PATH),
            ).values
        )
    )

    sectors = (
        sectors
        .drop_duplicates("company_id")
        .copy()
    )

    companies = companies.merge(
        sectors,
        on="company_id",
        how="left",
    )

    return companies, ratios


# ============================================================
# PDF PAGE
# ============================================================

def add_header(canvas, doc):
    """Draw page header/footer."""

    width, height = A4

    canvas.saveState()

    # Header
    canvas.setFillColor(HexColor("#172554"))
    canvas.rect(
        0,
        height - 12 * mm,
        width,
        12 * mm,
        fill=1,
        stroke=0,
    )

    # Footer
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)

    canvas.drawCentredString(
        width / 2,
        7 * mm,
        f"Portfolio Summary | Page {doc.page}",
    )

    canvas.restoreState()


def create_company_page(
    story,
    company,
    company_ratios,
):
    """Create one company page."""

    ticker = company["company_id"]

    company_name = company["company_name"]

    sector = company.get("broad_sector")

    if pd.isna(sector) or not sector:
        sector = "Unknown"

    # --------------------------------------------------------
    # Sort years
    # --------------------------------------------------------

    years = get_sorted_years(company_ratios)

    if not years:
        latest_year = "N/A"
        previous_year = None
        latest = pd.Series(dtype=object)
        previous = pd.Series(dtype=object)

    else:
        latest_year = years[-1]

        previous_year = (
            years[-2]
            if len(years) >= 2
            else None
        )

        latest = (
            company_ratios[
                company_ratios["year"] == latest_year
            ]
            .iloc[-1]
        )

        if previous_year:
            previous = (
                company_ratios[
                    company_ratios["year"] == previous_year
                ]
                .iloc[-1]
            )

        else:
            previous = pd.Series(dtype=object)

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    title_style = ParagraphStyle(
        "CompanyTitle",
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=HexColor("#172554"),
        spaceAfter=4 * mm,
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.grey,
    )

    story.append(
        Spacer(1, 8 * mm)
    )

    story.append(
        Paragraph(
            f"{company_name}",
            title_style,
        )
    )

    story.append(
        Paragraph(
            f"<b>Ticker:</b> {ticker} &nbsp;&nbsp;&nbsp; "
            f"<b>Sector:</b> {sector} &nbsp;&nbsp;&nbsp; "
            f"<b>Latest Year:</b> {latest_year}",
            subtitle_style,
        )
    )

    story.append(
        Spacer(1, 8 * mm)
    )

    # --------------------------------------------------------
    # KPI values
    # --------------------------------------------------------

    kpi_data = []

    for label, column in KPI_COLUMNS.items():

        if label == "ROCE":
            current = company.get("roce_percentage")
            previous_value = None

        elif label == "ROE":
            current = latest.get(
                "return_on_equity_pct"
            )

            previous_value = (
                previous.get(
                    "return_on_equity_pct"
                )
                if not previous.empty
                else None
            )

        else:
            current = latest.get(column)

            previous_value = (
                previous.get(column)
                if not previous.empty
                else None
            )

        arrow = trend_arrow(
            current,
            previous_value,
        )

        kpi_data.append(
            [
                Paragraph(
                    f"<b>{label}</b>",
                    ParagraphStyle(
                        "KPIHeader",
                        fontSize=10,
                        alignment=TA_CENTER,
                        textColor=HexColor("#172554"),
                    ),
                ),
                Paragraph(
                    format_value(
                        label,
                        current,
                    ),
                    ParagraphStyle(
                        "KPIValue",
                        fontSize=15,
                        leading=18,
                        alignment=TA_CENTER,
                        textColor=colors.black,
                    ),
                ),
                Paragraph(
                    arrow,
                    ParagraphStyle(
                        "KPIArrow",
                        fontSize=18,
                        leading=20,
                        alignment=TA_CENTER,
                        textColor=colors.black,
                    ),
                ),
            ]
        )

    # 6 KPI tiles in 2 rows x 3
    row1 = []
    row2 = []

    for i, tile in enumerate(kpi_data):

        tile_table = Table(
            [
                [tile[0]],
                [tile[1]],
                [tile[2]],
            ],
            colWidths=[48 * mm],
            rowHeights=[
                7 * mm,
                10 * mm,
                7 * mm,
            ],
        )

        tile_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        HexColor("#F1F5F9"),
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.8,
                        HexColor("#CBD5E1"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                ]
            )
        )

        if i < 3:
            row1.append(tile_table)
        else:
            row2.append(tile_table)

    kpi_table = Table(
        [
            row1,
            row2,
        ],
        colWidths=[
            52 * mm,
            52 * mm,
            52 * mm,
        ],
        hAlign="CENTER",
    )

    kpi_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
            ]
        )
    )

    story.append(kpi_table)

    story.append(
        Spacer(1, 10 * mm)
    )

    # --------------------------------------------------------
    # Latest-year summary
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "Latest-Year Financial Snapshot",
            ParagraphStyle(
                "SectionTitle",
                fontName="Helvetica-Bold",
                fontSize=14,
                textColor=HexColor("#172554"),
                spaceAfter=4 * mm,
            ),
        )
    )

    snapshot = [
        [
            "Metric",
            "Latest",
            "Previous",
            "Trend",
        ]
    ]

    for label, column in KPI_COLUMNS.items():

        if label == "ROCE":
            current = company.get("roce_percentage")
            previous_value = None
        else:
            current = latest.get(column)

            previous_value = (
                previous.get(column)
                if not previous.empty
                else None
            )

        snapshot.append(
            [
                label,
                format_value(label, current),
                format_value(label, previous_value),
                trend_arrow(
                    current,
                    previous_value,
                ),
            ]
        )

    snapshot_table = Table(
        snapshot,
        colWidths=[
            45 * mm,
            38 * mm,
            38 * mm,
            25 * mm,
        ],
        repeatRows=1,
    )

    snapshot_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    HexColor("#172554"),
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
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    HexColor("#CBD5E1"),
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        HexColor("#F8FAFC"),
                    ],
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

    story.append(snapshot_table)

    story.append(
        Spacer(1, 8 * mm)
    )

    # --------------------------------------------------------
    # Trend explanation
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "<b>Trend:</b> ↑ improved &nbsp;&nbsp; "
            "↓ declined &nbsp;&nbsp; "
            "→ flat within 2%",
            ParagraphStyle(
                "TrendLegend",
                fontSize=9,
                textColor=colors.grey,
            ),
        )
    )

    # --------------------------------------------------------
    # Footer information
    # --------------------------------------------------------

    story.append(
        Spacer(1, 15 * mm)
    )

    story.append(
        Paragraph(
            "Sprint 5 — Nifty 100 Data Foundation",
            ParagraphStyle(
                "FooterText",
                fontSize=9,
                textColor=colors.grey,
                alignment=TA_CENTER,
            ),
        )
    )

    story.append(PageBreak())


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("DAY 35 - PORTFOLIO SUMMARY PDF")
    print("=" * 60)

    print(f"\nDatabase: {DB_PATH}")
    print(f"Output:   {OUTPUT_PATH}")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    companies, ratios = load_company_data()

    print(
        f"\nCompanies loaded: {len(companies)}"
    )

    print(
        f"Ratio rows loaded: {len(ratios)}"
    )

    # --------------------------------------------------------
    # Sort companies alphabetically by ticker
    # --------------------------------------------------------

    companies = companies.sort_values(
        "company_id"
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # PDF
    # --------------------------------------------------------

    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title="Nifty 100 Portfolio Summary",
        author="Nifty 100 Data Foundation",
    )

    story = []

    processed = 0
    missing_data = []

    for _, company in companies.iterrows():

        ticker = company["company_id"]

        company_ratios = ratios[
            ratios["company_id"] == ticker
        ].copy()

        if company_ratios.empty:
            missing_data.append(ticker)

        create_company_page(
            story,
            company,
            company_ratios,
        )

        processed += 1

    # Remove final PageBreak
    if story and isinstance(story[-1], PageBreak):
        story.pop()

    doc.build(
        story,
        onFirstPage=add_header,
        onLaterPages=add_header,
    )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    size_kb = (
        OUTPUT_PATH.stat().st_size / 1024
    )

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)

    print(
        f"\nCompanies processed : {processed}"
    )

    print(
        f"Expected companies  : 92"
    )

    print(
        f"Missing ratio data  : {len(missing_data)}"
    )

    if missing_data:
        print(
            "\nCompanies without ratio data:"
        )

        for ticker in missing_data:
            print(f"- {ticker}")

    print(
        f"\nPASS - {OUTPUT_PATH}"
    )

    print(
        f"Size: {size_kb:.1f} KB"
    )

    print(
        "\nDAY 35 PORTFOLIO SUMMARY GENERATION: PASS"
    )


if __name__ == "__main__":
    main()