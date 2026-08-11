"""
tearsheet.py

Sprint 5 - Day 33
2-page company financial tearsheet generator.

Page 1:
- Navy header
- Company name + ticker
- Sector
- 6 KPI tiles
- 10-year Revenue / Net Profit charts
- ROE / ROCE trend chart

Page 2:
- Balance sheet composition
- Latest-year cash flow waterfall
- Pros
- Cons
- Capital allocation badge

Designed for ReportLab PDF generation.
"""

from pathlib import Path
import sqlite3
import re
import math

import pandas as pd
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    KeepTogether,
    PageBreak,
)
from reportlab.pdfbase.pdfmetrics import stringWidth


# =========================================================
# PATHS
# =========================================================

ROOT = Path(__file__).resolve().parents[2]

DB_PATH = ROOT / "db" / "nifty100.db"

PROS_CONS_PATH = (
    ROOT / "output" / "pros_cons_generated.csv"
)

CASHFLOW_INTELLIGENCE_PATH = (
    ROOT / "output" / "cashflow_intelligence.xlsx"
)

OUTPUT_DIR = (
    ROOT / "reports" / "tearsheets"
)

CHART_DIR = (
    ROOT / "reports" / "_chart_cache"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

CHART_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================================
# COLORS
# =========================================================

NAVY = HexColor("#0B1F3A")
BLUE = HexColor("#1F4E79")
LIGHT_BLUE = HexColor("#EAF2F8")
GREEN = HexColor("#1B7F3A")
LIGHT_GREEN = HexColor("#EAF6EE")
RED = HexColor("#B42318")
LIGHT_RED = HexColor("#FDECEC")
GREY = HexColor("#6B7280")
LIGHT_GREY = HexColor("#F3F4F6")
DARK = HexColor("#111827")
WHITE = colors.white
BORDER = HexColor("#D1D5DB")


# =========================================================
# PAGE SETTINGS
# =========================================================

PAGE_WIDTH, PAGE_HEIGHT = A4

LEFT = 14 * mm
RIGHT = 14 * mm
TOP = 12 * mm
BOTTOM = 12 * mm

CONTENT_WIDTH = PAGE_WIDTH - LEFT - RIGHT


# =========================================================
# DATABASE
# =========================================================

def get_connection():
    return sqlite3.connect(DB_PATH)


# =========================================================
# GENERAL HELPERS
# =========================================================

def clean_text(value):
    """Clean whitespace and newlines."""
    if value is None:
        return ""

    if pd.isna(value):
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value)
    ).strip()


def safe_float(value):
    """Convert a value to float safely."""
    try:
        if value is None:
            return None

        if pd.isna(value):
            return None

        return float(value)

    except (ValueError, TypeError):
        return None


def fmt_number(value, decimals=1):
    """Format financial number."""
    value = safe_float(value)

    if value is None:
        return "N/A"

    if abs(value) >= 100000:
        return f"{value / 100000:.1f}L"

    if abs(value) >= 1000:
        return f"{value / 1000:.1f}K"

    return f"{value:.{decimals}f}"


def fmt_pct(value):
    value = safe_float(value)

    if value is None:
        return "N/A"

    return f"{value:.1f}%"


def year_sort_key(year):
    """
    Extract numeric year from strings such as:
    Mar 2024
    Dec 2019
    Sep 2023
    """
    match = re.search(
        r"(\d{4})",
        str(year)
    )

    if match:
        return int(match.group(1))

    return 0


def deduplicate_years(df, year_column="year"):
    """
    Remove duplicate years.

    For duplicated years, keep the last database record.
    """
    if df.empty:
        return df.copy()

    result = df.copy()

    result["_year_num"] = (
        result[year_column]
        .apply(year_sort_key)
    )

    result = (
        result
        .sort_values(
            ["_year_num"]
        )
        .drop_duplicates(
            subset=[year_column],
            keep="last"
        )
        .drop(columns=["_year_num"])
    )

    return result.reset_index(drop=True)


# =========================================================
# DATA LOADERS
# =========================================================

def load_company(company_id):
    """Load company metadata."""

    con = get_connection()

    query = """
        SELECT
            c.id,
            c.company_name,
            c.roce_percentage,
            c.roe_percentage,
            s.broad_sector,
            s.sub_sector
        FROM companies c
        LEFT JOIN sectors s
            ON c.id = s.company_id
        WHERE c.id = ?
        LIMIT 1
    """

    df = pd.read_sql_query(
        query,
        con,
        params=[company_id]
    )

    con.close()

    if df.empty:
        raise ValueError(
            f"Company not found: {company_id}"
        )

    row = df.iloc[0]

    return {
        "company_id": company_id,
        "company_name": clean_text(row["company_name"]),
        "sector": clean_text(row["broad_sector"]) or "N/A",
        "sub_sector": clean_text(row["sub_sector"]),
        "roce": safe_float(row["roce_percentage"]),
        "roe": safe_float(row["roe_percentage"]),
    }


def load_profit_loss(company_id):
    """Load and deduplicate P&L data."""

    con = get_connection()

    query = """
        SELECT
            year,
            sales,
            net_profit,
            operating_profit,
            opm_percentage,
            eps
        FROM profitandloss
        WHERE company_id = ?
    """

    df = pd.read_sql_query(
        query,
        con,
        params=[company_id]
    )

    con.close()

    if df.empty:
        return df

    return deduplicate_years(df)


def load_ratios(company_id):
    """Load financial ratio history."""

    con = get_connection()

    query = """
        SELECT
            year,
            net_profit_margin_pct,
            operating_profit_margin_pct,
            return_on_equity_pct,
            debt_to_equity,
            interest_coverage,
            free_cash_flow_cr,
            capex_cr,
            earnings_per_share,
            book_value_per_share,
            dividend_payout_ratio_pct,
            total_debt_cr,
            cash_from_operations_cr,
            revenue_cagr_5yr,
            pat_cagr_5yr,
            eps_cagr_5yr
        FROM financial_ratios
        WHERE company_id = ?
    """

    df = pd.read_sql_query(
        query,
        con,
        params=[company_id]
    )

    con.close()

    if df.empty:
        return df

    return deduplicate_years(df)


def load_balance_sheet(company_id):
    """Load balance sheet history."""

    con = get_connection()

    query = """
        SELECT
            year,
            equity_capital,
            reserves,
            borrowings,
            other_liabilities,
            total_liabilities,
            total_assets
        FROM balancesheet
        WHERE company_id = ?
    """

    df = pd.read_sql_query(
        query,
        con,
        params=[company_id]
    )

    con.close()

    if df.empty:
        return df

    return deduplicate_years(df)


def load_cashflow(company_id):
    """Load cash flow history."""

    con = get_connection()

    query = """
        SELECT
            year,
            operating_activity,
            investing_activity,
            financing_activity,
            net_cash_flow
        FROM cashflow
        WHERE company_id = ?
    """

    df = pd.read_sql_query(
        query,
        con,
        params=[company_id]
    )

    con.close()

    if df.empty:
        return df

    return deduplicate_years(df)


def load_pros_cons(company_id):
    """Load generated pros and cons."""

    if not PROS_CONS_PATH.exists():
        return pd.DataFrame(
            columns=[
                "company_id",
                "type",
                "rule_id",
                "text",
                "confidence_pct",
            ]
        )

    df = pd.read_csv(
        PROS_CONS_PATH
    )

    df = df[
        df["company_id"].astype(str)
        == str(company_id)
    ].copy()

    return df


def load_cashflow_intelligence(company_id):
    """Load cash flow intelligence row."""

    if not CASHFLOW_INTELLIGENCE_PATH.exists():
        return {}

    df = pd.read_excel(
        CASHFLOW_INTELLIGENCE_PATH
    )

    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.strip()
    )

    result = df[
        df["company_id"] == company_id
    ]

    if result.empty:
        return {}

    return result.iloc[0].to_dict()


# =========================================================
# CHART CREATION
# =========================================================

def create_revenue_profit_chart(
    company_id,
    pnl
):
    """Create revenue and net profit bar chart."""

    if pnl.empty:
        return None

    data = pnl.tail(10).copy()

    if "sales" not in data.columns:
        return None

    if "net_profit" not in data.columns:
        return None

    data["sales"] = pd.to_numeric(
        data["sales"],
        errors="coerce"
    )

    data["net_profit"] = pd.to_numeric(
        data["net_profit"],
        errors="coerce"
    )

    data = data.dropna(
        subset=["sales"]
    )

    if data.empty:
        return None

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(10, 3.0)
    )

    x = range(len(data))

    # Revenue
    axes[0].bar(
        list(x),
        data["sales"].fillna(0)
    )

    axes[0].set_title(
        "Revenue",
        fontsize=9
    )

    axes[0].set_xticks(
        list(x)
    )

    axes[0].set_xticklabels(
        [
            str(v)[:4]
            for v in data["year"]
        ],
        rotation=45,
        fontsize=7
    )

    axes[0].tick_params(
        axis="y",
        labelsize=7
    )

    axes[0].grid(
        axis="y",
        alpha=0.2
    )

    # Profit
    axes[1].bar(
        list(x),
        data["net_profit"].fillna(0)
    )

    axes[1].set_title(
        "Net Profit",
        fontsize=9
    )

    axes[1].set_xticks(
        list(x)
    )

    axes[1].set_xticklabels(
        [
            str(v)[:4]
            for v in data["year"]
        ],
        rotation=45,
        fontsize=7
    )

    axes[1].tick_params(
        axis="y",
        labelsize=7
    )

    axes[1].grid(
        axis="y",
        alpha=0.2
    )

    fig.suptitle(
        "10-Year Revenue and Net Profit Trend",
        fontsize=10,
        fontweight="bold"
    )

    fig.tight_layout()

    path = (
        CHART_DIR
        / f"{company_id}_revenue_profit.png"
    )

    fig.savefig(
        path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(fig)

    return path


def create_roe_roce_chart(
    company_id,
    ratios,
    company
):
    """Create ROE / ROCE line chart."""

    if ratios.empty:
        return None

    data = ratios.tail(10).copy()

    data["roe"] = pd.to_numeric(
        data["return_on_equity_pct"],
        errors="coerce"
    )

    # Company-level ROCE is available, but historical
    # ROCE is not directly stored in financial_ratios.
    #
    # Therefore use company-level ROCE as the latest
    # reference and plot it as a horizontal benchmark.

    data = data.dropna(
        subset=["roe"]
    )

    if data.empty:
        return None

    fig, ax = plt.subplots(
        figsize=(10, 2.8)
    )

    x = list(range(len(data)))

    ax.plot(
        x,
        data["roe"],
        marker="o",
        linewidth=2,
        label="ROE"
    )

    roce = company.get("roce")

    if roce is not None:
        ax.axhline(
            roce,
            linestyle="--",
            linewidth=1.5,
            label=f"ROCE {roce:.1f}%"
        )

    ax.set_title(
        "ROE Trend / ROCE Reference",
        fontsize=10,
        fontweight="bold"
    )

    ax.set_xticks(x)

    ax.set_xticklabels(
        [
            str(v)[:4]
            for v in data["year"]
        ],
        rotation=45,
        fontsize=7
    )

    ax.tick_params(
        axis="y",
        labelsize=7
    )

    ax.grid(
        alpha=0.2
    )

    ax.legend(
        fontsize=7
    )

    fig.tight_layout()

    path = (
        CHART_DIR
        / f"{company_id}_roe_roce.png"
    )

    fig.savefig(
        path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(fig)

    return path


def create_balance_chart(
    company_id,
    balance
):
    """Create stacked balance sheet composition chart."""

    if balance.empty:
        return None

    data = balance.tail(10).copy()

    for col in [
        "equity_capital",
        "reserves",
        "borrowings",
        "other_liabilities",
    ]:
        data[col] = pd.to_numeric(
            data[col],
            errors="coerce"
        ).fillna(0)

    x = list(range(len(data)))

    fig, ax = plt.subplots(
        figsize=(10, 2.8)
    )

    bottom = data["equity_capital"]

    ax.bar(
        x,
        data["equity_capital"],
        label="Equity"
    )

    ax.bar(
        x,
        data["reserves"],
        bottom=bottom,
        label="Reserves"
    )

    bottom = (
        bottom
        + data["reserves"]
    )

    ax.bar(
        x,
        data["borrowings"],
        bottom=bottom,
        label="Borrowings"
    )

    bottom = (
        bottom
        + data["borrowings"]
    )

    ax.bar(
        x,
        data["other_liabilities"],
        bottom=bottom,
        label="Other Liabilities"
    )

    ax.set_title(
        "Balance Sheet Composition",
        fontsize=10,
        fontweight="bold"
    )

    ax.set_xticks(x)

    ax.set_xticklabels(
        [
            str(v)[:4]
            for v in data["year"]
        ],
        rotation=45,
        fontsize=7
    )

    ax.tick_params(
        axis="y",
        labelsize=7
    )

    ax.legend(
        fontsize=7,
        ncol=4,
        loc="upper left"
    )

    ax.grid(
        axis="y",
        alpha=0.2
    )

    fig.tight_layout()

    path = (
        CHART_DIR
        / f"{company_id}_balance.png"
    )

    fig.savefig(
        path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(fig)

    return path


# =========================================================
# REPORTLAB COMPONENTS
# =========================================================

styles = getSampleStyleSheet()

BODY_STYLE = ParagraphStyle(
    "BodyCustom",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=7.5,
    leading=10,
    textColor=DARK,
)

SMALL_STYLE = ParagraphStyle(
    "SmallCustom",
    parent=BODY_STYLE,
    fontSize=6.5,
    leading=8,
)

WHITE_STYLE = ParagraphStyle(
    "WhiteCustom",
    parent=BODY_STYLE,
    textColor=WHITE,
)

HEADER_STYLE = ParagraphStyle(
    "HeaderCustom",
    parent=styles["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=18,
    leading=21,
    textColor=WHITE,
)

SUBHEADER_STYLE = ParagraphStyle(
    "SubHeaderCustom",
    parent=BODY_STYLE,
    fontSize=8,
    textColor=WHITE,
)

SECTION_STYLE = ParagraphStyle(
    "SectionCustom",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=10,
    leading=12,
    textColor=NAVY,
    spaceAfter=4,
)

PRO_STYLE = ParagraphStyle(
    "ProCustom",
    parent=BODY_STYLE,
    fontSize=7.2,
    leading=9,
    leftIndent=5,
)

CON_STYLE = ParagraphStyle(
    "ConCustom",
    parent=BODY_STYLE,
    fontSize=7.2,
    leading=9,
    leftIndent=5,
)


def make_kpi_tile(
    label,
    value
):
    data = [
        [
            Paragraph(
                str(label),
                ParagraphStyle(
                    "KpiLabel",
                    parent=SMALL_STYLE,
                    fontName="Helvetica-Bold",
                    textColor=GREY,
                    alignment=TA_CENTER,
                )
            )
        ],
        [
            Paragraph(
                str(value),
                ParagraphStyle(
                    "KpiValue",
                    parent=BODY_STYLE,
                    fontName="Helvetica-Bold",
                    fontSize=13,
                    leading=15,
                    textColor=NAVY,
                    alignment=TA_CENTER,
                )
            )
        ]
    ]

    table = Table(
        data,
        colWidths=[
            CONTENT_WIDTH / 3 - 3 * mm
        ],
        rowHeights=[
            7 * mm,
            9 * mm
        ]
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    LIGHT_GREY
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    BORDER
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    3
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    3
                ),
            ]
        )
    )

    return table


def make_bullet(
    text,
    style
):
    return Paragraph(
        f"• {clean_text(text)}",
        style
    )


def capital_badge(label):
    table = Table(
        [
            [
                Paragraph(
                    f"<b>Capital Allocation: {clean_text(label)}</b>",
                    ParagraphStyle(
                        "Badge",
                        parent=BODY_STYLE,
                        alignment=TA_CENTER,
                        textColor=WHITE,
                        fontSize=9,
                    )
                )
            ]
        ],
        colWidths=[
            CONTENT_WIDTH
        ]
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    NAVY
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    NAVY
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
            ]
        )
    )

    return table


# =========================================================
# PAGE HEADER
# =========================================================

def page_header(
    company
):
    company_name = clean_text(
        company["company_name"]
    )

    ticker = company["company_id"]

    sector = clean_text(
        company["sector"]
    )

    header = Table(
        [
            [
                Paragraph(
                    company_name,
                    HEADER_STYLE
                )
            ],
            [
                Paragraph(
                    f"{ticker}  |  {sector}",
                    SUBHEADER_STYLE
                )
            ]
        ],
        colWidths=[
            CONTENT_WIDTH
        ]
    )

    header.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    NAVY
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, 0),
                    5
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, 0),
                    1
                ),
                (
                    "TOPPADDING",
                    (0, 1),
                    (-1, 1),
                    1
                ),
                (
                    "BOTTOMPADDING",
                    (0, 1),
                    (-1, 1),
                    5
                ),
            ]
        )
    )

    return header


# =========================================================
# WATERFALL
# =========================================================

def create_cashflow_waterfall(
    company_id,
    cashflow
):
    """
    Create a simple waterfall-style cash flow chart.

    CFO + CFI + CFF = Net Cash Flow.
    """

    if cashflow.empty:
        return None

    latest = cashflow.iloc[-1]

    cfo = safe_float(
        latest["operating_activity"]
    ) or 0

    cfi = safe_float(
        latest["investing_activity"]
    ) or 0

    cff = safe_float(
        latest["financing_activity"]
    ) or 0

    net = safe_float(
        latest["net_cash_flow"]
    )

    if net is None:
        net = cfo + cfi + cff

    labels = [
        "CFO",
        "CFI",
        "CFF",
        "Net Cash"
    ]

    values = [
        cfo,
        cfi,
        cff,
        net
    ]

    fig, ax = plt.subplots(
        figsize=(10, 2.6)
    )

    x = list(range(4))

    ax.bar(
        x,
        values
    )

    ax.axhline(
        0,
        linewidth=0.8
    )

    ax.set_xticks(x)

    ax.set_xticklabels(
        labels,
        fontsize=8
    )

    ax.set_title(
        f"Latest-Year Cash Flow ({latest['year']})",
        fontsize=10,
        fontweight="bold"
    )

    ax.tick_params(
        axis="y",
        labelsize=7
    )

    ax.grid(
        axis="y",
        alpha=0.2
    )

    fig.tight_layout()

    path = (
        CHART_DIR
        / f"{company_id}_waterfall.png"
    )

    fig.savefig(
        path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(fig)

    return path


# =========================================================
# PDF GENERATOR
# =========================================================

def generate_tearsheet(
    company_id,
    output_path=None
):
    """Generate a complete 2-page company tearsheet."""

    company = load_company(
        company_id
    )

    pnl = load_profit_loss(
        company_id
    )

    ratios = load_ratios(
        company_id
    )

    balance = load_balance_sheet(
        company_id
    )

    cashflow = load_cashflow(
        company_id
    )

    pros_cons = load_pros_cons(
        company_id
    )

    intelligence = load_cashflow_intelligence(
        company_id
    )

    if output_path is None:
        output_path = (
            OUTPUT_DIR
            / f"{company_id}_tearsheet.pdf"
        )

    output_path = Path(
        output_path
    )

    # -----------------------------------------------------
    # CHECK MINIMUM DATA
    # -----------------------------------------------------

    available_years = set()

    for source in [
        pnl,
        ratios,
        balance,
        cashflow,
    ]:
        if not source.empty:
            available_years.update(
                source["year"].astype(str)
            )

    if len(available_years) < 3:
        raise ValueError(
            f"{company_id} has fewer than 3 years of data."
        )

    # -----------------------------------------------------
    # CHARTS
    # -----------------------------------------------------

    revenue_profit_chart = (
        create_revenue_profit_chart(
            company_id,
            pnl
        )
    )

    roe_roce_chart = (
        create_roe_roce_chart(
            company_id,
            ratios,
            company
        )
    )

    balance_chart = (
        create_balance_chart(
            company_id,
            balance
        )
    )

    waterfall_chart = (
        create_cashflow_waterfall(
            company_id,
            cashflow
        )
    )

    # -----------------------------------------------------
    # LATEST DATA
    # -----------------------------------------------------

    latest_pnl = (
        pnl.iloc[-1]
        if not pnl.empty
        else {}
    )

    latest_ratio = (
        ratios.iloc[-1]
        if not ratios.empty
        else {}
    )

    latest_cashflow = (
        cashflow.iloc[-1]
        if not cashflow.empty
        else {}
    )

    # -----------------------------------------------------
    # KPI VALUES
    # -----------------------------------------------------

    revenue = (
        safe_float(
            latest_pnl.get("sales")
        )
        if hasattr(latest_pnl, "get")
        else None
    )

    net_profit = (
        safe_float(
            latest_pnl.get("net_profit")
        )
        if hasattr(latest_pnl, "get")
        else None
    )

    roe = (
        safe_float(
            latest_ratio.get(
                "return_on_equity_pct"
            )
        )
        if hasattr(latest_ratio, "get")
        else company["roe"]
    )

    roce = company["roce"]

    debt_equity = (
        safe_float(
            latest_ratio.get(
                "debt_to_equity"
            )
        )
        if hasattr(latest_ratio, "get")
        else None
    )

    fcf = (
        safe_float(
            latest_ratio.get(
                "free_cash_flow_cr"
            )
        )
        if hasattr(latest_ratio, "get")
        else None
    )

    opm = (
        safe_float(
            latest_ratio.get(
                "operating_profit_margin_pct"
            )
        )
        if hasattr(latest_ratio, "get")
        else None
    )

    # -----------------------------------------------------
    # DOCUMENT
    # -----------------------------------------------------

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=RIGHT,
        leftMargin=LEFT,
        topMargin=TOP,
        bottomMargin=BOTTOM,
        title=f"{company_id} Financial Tearsheet",
        author="Nifty 100 Data Foundation",
    )

    story = []

    # =====================================================
    # PAGE 1
    # =====================================================

    story.append(
        page_header(company)
    )

    story.append(
        Spacer(1, 4 * mm)
    )

    # -----------------------------------------------------
    # KPI TILES
    # -----------------------------------------------------

    kpi_data = [
        [
            make_kpi_tile(
                "Revenue",
                fmt_number(revenue)
            ),
            make_kpi_tile(
                "Net Profit",
                fmt_number(net_profit)
            ),
            make_kpi_tile(
                "ROE",
                fmt_pct(roe)
            ),
        ],
        [
            make_kpi_tile(
                "ROCE",
                fmt_pct(roce)
            ),
            make_kpi_tile(
                "Debt / Equity",
                (
                    "Debt Free"
                    if debt_equity == 0
                    else (
                        f"{debt_equity:.2f}x"
                        if debt_equity is not None
                        else "N/A"
                    )
                )
            ),
            make_kpi_tile(
                "Free Cash Flow",
                fmt_number(fcf)
            ),
        ]
    ]

    kpi_table = Table(
        kpi_data,
        colWidths=[
            CONTENT_WIDTH / 3
        ] * 3,
        hAlign="LEFT"
    )

    kpi_table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    2
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    2
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    2
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    2
                ),
            ]
        )
    )

    story.append(
        kpi_table
    )

    story.append(
        Spacer(1, 3 * mm)
    )

    # -----------------------------------------------------
    # REVENUE / PROFIT
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "Operating Performance",
            SECTION_STYLE
        )
    )

    if revenue_profit_chart:
        story.append(
            Image(
                str(revenue_profit_chart),
                width=CONTENT_WIDTH,
                height=67 * mm,
            )
        )
    else:
        story.append(
            Paragraph(
                "Revenue / profit history unavailable.",
                BODY_STYLE
            )
        )

    story.append(
        Spacer(1, 2 * mm)
    )

    # -----------------------------------------------------
    # ROE / ROCE
    # -----------------------------------------------------

    if roe_roce_chart:
        story.append(
            Image(
                str(roe_roce_chart),
                width=CONTENT_WIDTH,
                height=52 * mm,
            )
        )

    # =====================================================
    # PAGE 2
    # =====================================================

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "Balance Sheet & Cash Flow Intelligence",
            SECTION_STYLE
        )
    )

    # -----------------------------------------------------
    # BALANCE SHEET
    # -----------------------------------------------------

    if balance_chart:
        story.append(
            Image(
                str(balance_chart),
                width=CONTENT_WIDTH,
                height=55 * mm,
            )
        )

    story.append(
        Spacer(1, 2 * mm)
    )

    # -----------------------------------------------------
    # CASH FLOW
    # -----------------------------------------------------

    if waterfall_chart:
        story.append(
            Image(
                str(waterfall_chart),
                width=CONTENT_WIDTH,
                height=48 * mm,
            )
        )

    story.append(
        Spacer(1, 2 * mm)
    )

    # -----------------------------------------------------
    # PROS / CONS
    # -----------------------------------------------------

    pros = pros_cons[
        pros_cons["type"].astype(str).str.lower()
        == "pro"
    ].copy()

    cons = pros_cons[
        pros_cons["type"].astype(str).str.lower()
        == "con"
    ].copy()

    # Sort by confidence
    if not pros.empty:
        pros = pros.sort_values(
            "confidence_pct",
            ascending=False
        )

    if not cons.empty:
        cons = cons.sort_values(
            "confidence_pct",
            ascending=False
        )

    # Limit to prevent overflow
    pros = pros.head(5)
    cons = cons.head(5)

    pro_flowables = [
        Paragraph(
            "Pros",
            ParagraphStyle(
                "ProsHeader",
                parent=SECTION_STYLE,
                textColor=GREEN
            )
        )
    ]

    if pros.empty:
        pro_flowables.append(
            Paragraph(
                "No significant positive signal available.",
                PRO_STYLE
            )
        )
    else:
        for _, row in pros.iterrows():
            pro_flowables.append(
                make_bullet(
                    row["text"],
                    PRO_STYLE
                )
            )

    con_flowables = [
        Paragraph(
            "Cons",
            ParagraphStyle(
                "ConsHeader",
                parent=SECTION_STYLE,
                textColor=RED
            )
        )
    ]

    if cons.empty:
        con_flowables.append(
            Paragraph(
                "No significant downside signal available.",
                CON_STYLE
            )
        )
    else:
        for _, row in cons.iterrows():
            con_flowables.append(
                make_bullet(
                    row["text"],
                    CON_STYLE
                )
            )

    pros_table = Table(
        [[
            pro_flowables,
            con_flowables
        ]],
        colWidths=[
            CONTENT_WIDTH / 2 - 2 * mm,
            CONTENT_WIDTH / 2 - 2 * mm
        ]
    )

    pros_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    LIGHT_GREEN
                ),
                (
                    "BACKGROUND",
                    (1, 0),
                    (1, 0),
                    LIGHT_RED
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    BORDER
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    BORDER
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
            ]
        )
    )

    story.append(
        pros_table
    )

    story.append(
        Spacer(1, 3 * mm)
    )

    # -----------------------------------------------------
    # CAPITAL ALLOCATION
    # -----------------------------------------------------

    capital_label = (
        intelligence.get(
            "capital_allocation_label",
            "Unknown"
        )
        if intelligence
        else "Unknown"
    )

    story.append(
        capital_badge(
            capital_label
        )
    )

    story.append(
        Spacer(1, 2 * mm)
    )

    # -----------------------------------------------------
    # CASH FLOW FLAGS
    # -----------------------------------------------------

    distress = (
        intelligence.get(
            "distress_flag",
            False
        )
        if intelligence
        else False
    )

    deleveraging = (
        intelligence.get(
            "deleveraging_flag",
            False
        )
        if intelligence
        else False
    )

    flag_text = []

    if str(distress).lower() in [
        "true",
        "1",
        "yes"
    ]:
        flag_text.append(
            "<b>Distress signal detected.</b>"
        )

    if str(deleveraging).lower() in [
        "true",
        "1",
        "yes"
    ]:
        flag_text.append(
            "<b>Deleveraging activity detected.</b>"
        )

    if not flag_text:
        flag_text.append(
            "No major cash-flow warning flag detected."
        )

    story.append(
        Paragraph(
            " | ".join(flag_text),
            SMALL_STYLE
        )
    )

    # -----------------------------------------------------
    # BUILD
    # -----------------------------------------------------

    doc.build(story)

    return output_path


# =========================================================
# TEST COMPANIES
# =========================================================

def get_all_company_ids():
    conn = sqlite3.connect(DB_PATH)

    rows = conn.execute("""
        SELECT id
        FROM companies
        ORDER BY id
    """).fetchall()

    conn.close()

    return [row[0] for row in rows]

def get_year_count(company_id):
    conn = sqlite3.connect(DB_PATH)

    row = conn.execute("""
        SELECT COUNT(DISTINCT year)
        FROM financial_ratios
        WHERE company_id = ?
    """, (company_id,)).fetchone()

    conn.close()

    return row[0] if row else 0


def main():
    print("=" * 60)
    print("DAY 34 - ALL COMPANY TEARSHEET GENERATION")
    print("=" * 60)

    print(f"\nDatabase: {DB_PATH}")

    company_ids = get_all_company_ids()

    print(f"Companies loaded: {len(company_ids)}")

    successful = []
    failed = []
    skipped = []

    for company_id in company_ids:

        print(f"\nGenerating: {company_id}")

        # -------------------------------------------------
        # Day 34 requirement:
        # Skip companies with fewer than 3 years of data
        # -------------------------------------------------
        year_count = get_year_count(company_id)

        if year_count < 3:
            print(
                f"SKIP - {company_id}: "
                f"only {year_count} years of data"
            )

            skipped.append({
                "company_id": company_id,
                "year_count": year_count
            })

            continue

        try:

            output = generate_tearsheet(company_id)

            size_kb = (
                output.stat().st_size / 1024
            )

            print(f"PASS - {output}")
            print(f"Size: {size_kb:.1f} KB")

            successful.append(company_id)

        except Exception as exc:

            print(
                f"FAIL - {company_id}: {exc}"
            )

            failed.append(company_id)

    # -------------------------------------------------
    # Save skipped companies
    # -------------------------------------------------

    skipped_path = (
        ROOT
        / "output"
        / "skipped_tearsheets.csv"
    )

    if skipped:

        pd.DataFrame(skipped).to_csv(
            skipped_path,
            index=False
        )

    else:

        pd.DataFrame(
            columns=["company_id", "year_count"]
        ).to_csv(
            skipped_path,
            index=False
        )

    # -------------------------------------------------
    # Final summary
    # -------------------------------------------------

    print("\n" + "=" * 60)

    print(
        f"Successful: {len(successful)} / "
        f"{len(company_ids)}"
    )

    print(
        f"Failed: {len(failed)}"
    )

    print(
        f"Skipped: {len(skipped)}"
    )

    print(
        f"\nSkipped companies log: "
        f"{skipped_path}"
    )

    if failed:

        print("\nFailed companies:")

        for company_id in failed:
            print(f"- {company_id}")

    print("=" * 60)

    if not failed:

        print("\nDAY 34 TEARSHEET GENERATION: PASS")

    else:

        print("\nDAY 34 TEARSHEET GENERATION: REVIEW FAILURES")


if __name__ == "__main__":
    main()