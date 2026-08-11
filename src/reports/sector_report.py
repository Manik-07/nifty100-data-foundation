"""
sector_report.py

Sprint 5 - Day 34
Sector Report Generator.

Generates one PDF report per sector.

Each sector PDF contains:
1. Sector summary
2. Median KPI values
3. Company-level table with 8 metrics

Output:
reports/sector/<sector>_report.pdf
"""

from pathlib import Path
import sqlite3
import re
import math

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DB_PATH = ROOT / "db" / "nifty100.db"

OUTPUT_DIR = ROOT / "reports" / "sector"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CONSTANTS
# ============================================================

NAVY = HexColor("#14213D")
LIGHT_BLUE = HexColor("#EAF1F8")
LIGHT_GREY = HexColor("#F3F4F6")
DARK_GREY = HexColor("#444444")
GREEN = HexColor("#1B7F3A")

PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    return sqlite3.connect(DB_PATH)


def load_sector_data():
    """
    Load company + sector + financial ratio information.
    """

    conn = get_connection()

    query = """
    SELECT
        c.id AS company_id,
        c.company_name,
        s.broad_sector AS sector,

        fr.year,
        fr.return_on_equity_pct,
        fr.operating_profit_margin_pct,
        fr.debt_to_equity,
        fr.interest_coverage,
        fr.free_cash_flow_cr,
        fr.revenue_cagr_5yr,
        fr.pat_cagr_5yr,
        fr.eps_cagr_5yr

    FROM companies c

    LEFT JOIN sectors s
        ON c.id = s.company_id

    LEFT JOIN financial_ratios fr
        ON c.id = fr.company_id

    WHERE s.broad_sector IS NOT NULL

    ORDER BY
        s.broad_sector,
        c.id,
        fr.year
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    return df


# ============================================================
# HELPERS
# ============================================================

def clean_company_name(name):
    """
    Clean newline and excessive whitespace.
    """

    if pd.isna(name):
        return ""

    name = str(name)

    name = re.sub(r"\s+", " ", name)

    return name.strip()


def safe_filename(value):
    """
    Make a Windows-safe filename.
    """

    value = str(value)

    value = re.sub(r'[<>:"/\\|?*]', "_", value)

    value = value.strip()

    return value


def fmt(value, decimals=2):
    """
    Format numeric values safely.
    """

    if value is None:
        return "N/A"

    try:

        if pd.isna(value):
            return "N/A"

        return f"{float(value):.{decimals}f}"

    except (ValueError, TypeError):

        return "N/A"


def latest_year_value(company_df, column):
    """
    Return latest non-null value for a metric.
    """

    temp = company_df[
        company_df[column].notna()
    ].copy()

    if temp.empty:
        return None

    temp["_year_sort"] = temp["year"].astype(str)

    temp = temp.sort_values("_year_sort")

    return temp.iloc[-1][column]


def median_latest_metric(sector_df, column):
    """
    Calculate the median of the latest available
    value for each company in a sector.
    """

    values = []

    for company_id, company_df in sector_df.groupby("company_id"):

        value = latest_year_value(
            company_df,
            column
        )

        if value is not None and not pd.isna(value):
            values.append(float(value))

    if not values:
        return None

    return float(pd.Series(values).median())


def get_latest_company_rows(sector_df):
    """
    Return one latest available row per company.
    """

    rows = []

    for company_id, company_df in sector_df.groupby(
        "company_id",
        sort=True
    ):

        company_df = company_df.copy()

        company_df["_year_sort"] = (
            company_df["year"]
            .fillna("")
            .astype(str)
        )

        company_df = company_df.sort_values(
            "_year_sort"
        )

        row = company_df.iloc[-1].copy()

        # For each metric, if latest row is NULL,
        # find latest non-null value.
        for column in [
            "return_on_equity_pct",
            "operating_profit_margin_pct",
            "debt_to_equity",
            "interest_coverage",
            "free_cash_flow_cr",
            "revenue_cagr_5yr",
            "pat_cagr_5yr",
            "eps_cagr_5yr",
        ]:

            value = latest_year_value(
                company_df,
                column
            )

            row[column] = value

        rows.append(row)

    return pd.DataFrame(rows)


# ============================================================
# STYLES
# ============================================================

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "SectorTitle",
    parent=styles["Title"],
    fontName="Helvetica-Bold",
    fontSize=22,
    leading=26,
    textColor=NAVY,
    alignment=TA_LEFT,
    spaceAfter=8 * mm,
)

subtitle_style = ParagraphStyle(
    "Subtitle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=10,
    leading=13,
    textColor=DARK_GREY,
)

section_style = ParagraphStyle(
    "Section",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=13,
    leading=16,
    textColor=NAVY,
    spaceBefore=5 * mm,
    spaceAfter=3 * mm,
)

small_style = ParagraphStyle(
    "Small",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=7.5,
    leading=9,
    textColor=DARK_GREY,
)

table_header_style = ParagraphStyle(
    "TableHeader",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=7.5,
    leading=9,
    textColor=colors.white,
    alignment=TA_CENTER,
)

table_cell_style = ParagraphStyle(
    "TableCell",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=7,
    leading=8.5,
    textColor=colors.black,
    alignment=TA_CENTER,
)

company_style = ParagraphStyle(
    "Company",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=7,
    leading=8.5,
    textColor=colors.black,
    alignment=TA_LEFT,
)


# ============================================================
# PAGE HEADER / FOOTER
# ============================================================

def draw_page(canvas, doc):

    canvas.saveState()

    width, height = landscape(A4)

    # Header line
    canvas.setFillColor(NAVY)

    canvas.rect(
        0,
        height - 10 * mm,
        width,
        10 * mm,
        fill=1,
        stroke=0,
    )

    canvas.setFillColor(colors.white)

    canvas.setFont(
        "Helvetica-Bold",
        8
    )

    canvas.drawString(
        10 * mm,
        height - 6.5 * mm,
        "NIFTY 100 — SECTOR REPORT"
    )

    # Footer
    canvas.setFillColor(DARK_GREY)

    canvas.setFont(
        "Helvetica",
        7
    )

    canvas.drawString(
        10 * mm,
        6 * mm,
        "Financial analysis generated from project database"
    )

    canvas.drawRightString(
        width - 10 * mm,
        6 * mm,
        f"Page {doc.page}"
    )

    canvas.restoreState()


# ============================================================
# KPI TABLE
# ============================================================

def build_kpi_table(sector_df):

    kpis = [
        (
            "Median ROE %",
            median_latest_metric(
                sector_df,
                "return_on_equity_pct"
            ),
        ),
        (
            "Median OPM %",
            median_latest_metric(
                sector_df,
                "operating_profit_margin_pct"
            ),
        ),
        (
            "Median D/E",
            median_latest_metric(
                sector_df,
                "debt_to_equity"
            ),
        ),
        (
            "Median ICR",
            median_latest_metric(
                sector_df,
                "interest_coverage"
            ),
        ),
        (
            "Median FCF",
            median_latest_metric(
                sector_df,
                "free_cash_flow_cr"
            ),
        ),
        (
            "Median Revenue CAGR %",
            median_latest_metric(
                sector_df,
                "revenue_cagr_5yr"
            ),
        ),
        (
            "Median PAT CAGR %",
            median_latest_metric(
                sector_df,
                "pat_cagr_5yr"
            ),
        ),
        (
            "Median EPS CAGR %",
            median_latest_metric(
                sector_df,
                "eps_cagr_5yr"
            ),
        ),
    ]

    data = []

    # Four KPI cards per row.
    for i in range(0, len(kpis), 4):

        row = []

        for label, value in kpis[i:i + 4]:

            text = (
                f"<b>{label}</b><br/>"
                f"<font size='14'>{fmt(value)}</font>"
            )

            row.append(
                Paragraph(
                    text,
                    ParagraphStyle(
                        "KPI",
                        parent=small_style,
                        alignment=TA_CENTER,
                        fontSize=8,
                        leading=12,
                    )
                )
            )

        data.append(row)

    table = Table(
        data,
        colWidths=[
            65 * mm,
            65 * mm,
            65 * mm,
            65 * mm,
        ],
        rowHeights=18 * mm,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    LIGHT_BLUE,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.white,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    return table


# ============================================================
# COMPANY TABLE
# ============================================================

def build_company_table(latest_df):

    headers = [
        "Ticker",
        "Company",
        "ROE %",
        "OPM %",
        "D/E",
        "ICR",
        "FCF (Cr)",
        "Rev CAGR %",
        "PAT CAGR %",
        "EPS CAGR %",
    ]

    data = [
        [
            Paragraph(
                header,
                table_header_style
            )
            for header in headers
        ]
    ]

    for _, row in latest_df.iterrows():

        company_name = clean_company_name(
            row.get("company_name", "")
        )

        data.append(
            [
                Paragraph(
                    str(row["company_id"]),
                    company_style,
                ),

                Paragraph(
                    company_name,
                    company_style,
                ),

                Paragraph(
                    fmt(
                        row.get(
                            "return_on_equity_pct"
                        )
                    ),
                    table_cell_style,
                ),

                Paragraph(
                    fmt(
                        row.get(
                            "operating_profit_margin_pct"
                        )
                    ),
                    table_cell_style,
                ),

                Paragraph(
                    fmt(
                        row.get(
                            "debt_to_equity"
                        )
                    ),
                    table_cell_style,
                ),

                Paragraph(
                    fmt(
                        row.get(
                            "interest_coverage"
                        )
                    ),
                    table_cell_style,
                ),

                Paragraph(
                    fmt(
                        row.get(
                            "free_cash_flow_cr"
                        )
                    ),
                    table_cell_style,
                ),

                Paragraph(
                    fmt(
                        row.get(
                            "revenue_cagr_5yr"
                        )
                    ),
                    table_cell_style,
                ),

                Paragraph(
                    fmt(
                        row.get(
                            "pat_cagr_5yr"
                        )
                    ),
                    table_cell_style,
                ),

                Paragraph(
                    fmt(
                        row.get(
                            "eps_cagr_5yr"
                        )
                    ),
                    table_cell_style,
                ),
            ]
        )

    table = Table(
        data,
        colWidths=[
            20 * mm,
            58 * mm,
            18 * mm,
            18 * mm,
            16 * mm,
            18 * mm,
            22 * mm,
            23 * mm,
            23 * mm,
            23 * mm,
        ],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    NAVY,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ALIGN",
                    (2, 1),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "BACKGROUND",
                    (0, 1),
                    (-1, -1),
                    colors.white,
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        LIGHT_GREY,
                    ],
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
            ]
        )
    )

    return table


# ============================================================
# SECTOR PDF
# ============================================================

def generate_sector_report(
    sector,
    sector_df,
):

    latest_df = get_latest_company_rows(
        sector_df
    )

    filename = (
        safe_filename(sector)
        + "_report.pdf"
    )

    output_path = OUTPUT_DIR / filename

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=15 * mm,
        bottomMargin=12 * mm,
        title=f"{sector} Sector Report",
        author="Nifty 100 Data Foundation",
    )

    story = []

    # ========================================================
    # TITLE
    # ========================================================

    story.append(
        Paragraph(
            f"{sector} Sector Report",
            title_style,
        )
    )

    story.append(
        Paragraph(
            (
                f"<b>Companies:</b> "
                f"{latest_df['company_id'].nunique()} "
                f"&nbsp;&nbsp; | &nbsp;&nbsp;"
                f"<b>Latest available financial data</b>"
            ),
            subtitle_style,
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm
        )
    )

    # ========================================================
    # SECTOR SUMMARY
    # ========================================================

    story.append(
        Paragraph(
            "Sector Median KPIs",
            section_style,
        )
    )

    story.append(
        build_kpi_table(
            sector_df
        )
    )

    story.append(
        Spacer(
            1,
            7 * mm
        )
    )

    # ========================================================
    # COMPANY METRICS
    # ========================================================

    story.append(
        Paragraph(
            "Company-Level Financial Metrics",
            section_style,
        )
    )

    story.append(
        Paragraph(
            (
                "Metrics shown are the latest available values "
                "for each company. CAGR values represent the "
                "5-year compounded growth metrics available "
                "in the financial ratio dataset."
            ),
            small_style,
        )
    )

    story.append(
        Spacer(
            1,
            3 * mm
        )
    )

    story.append(
        build_company_table(
            latest_df
        )
    )

    # ========================================================
    # BUILD PDF
    # ========================================================

    doc.build(
        story,
        onFirstPage=draw_page,
        onLaterPages=draw_page,
    )

    return output_path


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("DAY 34 - SECTOR REPORT GENERATION")
    print("=" * 60)

    print(
        f"\nDatabase: {DB_PATH}"
    )

    df = load_sector_data()

    if df.empty:

        print(
            "ERROR: No sector data found."
        )

        return

    sectors = sorted(
        df["sector"]
        .dropna()
        .unique()
        .tolist()
    )

    print(
        f"\nSectors found: {len(sectors)}"
    )

    successful = []
    failed = []

    for sector in sectors:

        print(
            f"\nGenerating sector: {sector}"
        )

        try:

            sector_df = df[
                df["sector"] == sector
            ].copy()

            output = generate_sector_report(
                sector,
                sector_df,
            )

            size_kb = (
                output.stat().st_size
                / 1024
            )

            print(
                f"PASS - {output}"
            )

            print(
                f"Size: {size_kb:.1f} KB"
            )

            successful.append(
                sector
            )

        except Exception as exc:

            print(
                f"FAIL - {sector}: {exc}"
            )

            failed.append(
                sector
            )

    print("\n" + "=" * 60)

    print(
        f"Successful: {len(successful)} / "
        f"{len(sectors)}"
    )

    print(
        f"Failed: {len(failed)}"
    )

    if failed:

        print(
            "\nFailed sectors:"
        )

        for sector in failed:

            print(
                f"- {sector}"
            )

    print(
        "\nOutput directory:"
    )

    print(
        OUTPUT_DIR
    )

    print("=" * 60)

    if len(successful) == len(sectors):

        print(
            "DAY 34 SECTOR REPORT GENERATION: PASS"
        )

    else:

        print(
            "DAY 34 SECTOR REPORT GENERATION: CHECK FAILURES"
        )


if __name__ == "__main__":
    main()