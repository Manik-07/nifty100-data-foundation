from pathlib import Path
import re
import sqlite3

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse


# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "db" / "nifty100.db"

router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# HELPERS
# ============================================================

def rows_to_dict(rows):
    return [dict(row) for row in rows]


def extract_year_month(value):
    """
    Convert database year values such as:
        Mar 2024
        Dec 2023
        Jun 2022

    into YYYY-MM.

    Returns None when the format cannot be parsed.
    """

    if not value:
        return None

    match = re.search(
        r"([A-Za-z]{3})\s+(\d{4})",
        str(value)
    )

    if not match:
        return None

    month_text = match.group(1).lower()
    year = int(match.group(2))

    months = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }

    month = months.get(month_text)

    if month is None:
        return None

    return f"{year:04d}-{month:02d}"


def validate_year_month(value, parameter_name):
    if value is None:
        return None

    if not re.fullmatch(r"\d{4}-\d{2}", value):
        raise HTTPException(
            status_code=400,
            detail=f"{parameter_name} must use YYYY-MM format.",
        )

    month = int(value[5:7])

    if month < 1 or month > 12:
        raise HTTPException(
            status_code=400,
            detail=f"{parameter_name} must use YYYY-MM format.",
        )

    return value


def filter_year_rows(rows, from_year=None, to_year=None):
    from_year = validate_year_month(from_year, "from_year")
    to_year = validate_year_month(to_year, "to_year")

    if from_year and to_year and from_year > to_year:
        raise HTTPException(
            status_code=400,
            detail="from_year cannot be greater than to_year.",
        )

    result = []

    for row in rows:
        item = dict(row)

        item_year = extract_year_month(
            item.get("year")
        )

        if item_year is None:
            continue

        if from_year and item_year < from_year:
            continue

        if to_year and item_year > to_year:
            continue

        result.append(item)

    return result


def get_company_or_404(conn, ticker):
    row = conn.execute(
        """
        SELECT *
        FROM companies
        WHERE UPPER(id) = UPPER(?)
        """,
        (ticker,),
    ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Company '{ticker}' not found.",
        )

    return row


def get_latest_ratio(conn, ticker):
    return conn.execute(
        """
        SELECT *
        FROM financial_ratios
        WHERE UPPER(company_id) = UPPER(?)
        ORDER BY
            CAST(
                substr(
                    year,
                    instr(year, ' ') + 1,
                    4
                ) AS INTEGER
            ) DESC,
            id DESC
        LIMIT 1
        """,
        (ticker,),
    ).fetchone()


# ============================================================
# GET /companies
# ============================================================

@router.get("")
def get_companies(
    sector: str | None = Query(
        default=None,
        description="Filter by broad sector",
    ),
    market_cap_category: str | None = Query(
        default=None,
        description="Filter by market-cap category",
    ),
    search: str | None = Query(
        default=None,
        description="Partial company name or ticker search",
    ),
):
    conn = get_connection()

    try:
        query = """
            SELECT
                c.id,
                c.company_name,
                s.broad_sector,
                s.sub_sector,
                c.roe_percentage AS roe_pct,
                c.roce_percentage AS roce_pct
            FROM companies c
            LEFT JOIN sectors s
                ON s.company_id = c.id
            WHERE 1 = 1
        """

        params = []

        if sector:
            query += """
                AND LOWER(s.broad_sector) = LOWER(?)
            """
            params.append(sector)

        if market_cap_category:
            query += """
                AND LOWER(s.market_cap_category) =
                    LOWER(?)
            """
            params.append(market_cap_category)

        if search:
            query += """
                AND (
                    LOWER(c.id) LIKE LOWER(?)
                    OR LOWER(c.company_name) LIKE LOWER(?)
                )
            """

            search_pattern = f"%{search}%"

            params.extend([
                search_pattern,
                search_pattern,
            ])

        query += """
            ORDER BY c.id
        """

        rows = conn.execute(
            query,
            params,
        ).fetchall()

        return {
            "count": len(rows),
            "companies": rows_to_dict(rows),
        }

    finally:
        conn.close()


# ============================================================
# GET /companies/{ticker}
# ============================================================

@router.get("/{ticker}")
def get_company_profile(ticker: str):
    conn = get_connection()

    try:
        company = get_company_or_404(
            conn,
            ticker,
        )

        company_data = dict(company)

        sector = conn.execute(
            """
            SELECT
                company_id,
                broad_sector,
                sub_sector,
                index_weight_pct,
                market_cap_category
            FROM sectors
            WHERE UPPER(company_id) = UPPER(?)
            LIMIT 1
            """,
            (ticker,),
        ).fetchone()

        latest_ratio = get_latest_ratio(
            conn,
            ticker,
        )

        company_data["sector"] = (
            dict(sector)
            if sector
            else None
        )

        company_data["latest_year_kpis"] = (
            dict(latest_ratio)
            if latest_ratio
            else None
        )

        return company_data

    finally:
        conn.close()


# ============================================================
# GENERIC HISTORY LOADER
# ============================================================

def get_history(
    ticker,
    table,
    from_year=None,
    to_year=None,
):
    conn = get_connection()

    try:
        # Verify ticker first.
        get_company_or_404(
            conn,
            ticker,
        )

        rows = conn.execute(
            f"""
            SELECT *
            FROM {table}
            WHERE UPPER(company_id) = UPPER(?)
            ORDER BY id
            """,
            (ticker,),
        ).fetchall()

        filtered = filter_year_rows(
            rows,
            from_year,
            to_year,
        )

        return {
            "ticker": ticker.upper(),
            "count": len(filtered),
            "history": filtered,
        }

    finally:
        conn.close()


# ============================================================
# GET /companies/{ticker}/pl
# ============================================================

@router.get("/{ticker}/pl")
def get_profit_loss(
    ticker: str,
    from_year: str | None = Query(
        default=None,
        description="YYYY-MM",
    ),
    to_year: str | None = Query(
        default=None,
        description="YYYY-MM",
    ),
):
    return get_history(
        ticker,
        "profitandloss",
        from_year,
        to_year,
    )


# ============================================================
# GET /companies/{ticker}/bs
# ============================================================

@router.get("/{ticker}/bs")
def get_balance_sheet(
    ticker: str,
    from_year: str | None = Query(
        default=None,
        description="YYYY-MM",
    ),
    to_year: str | None = Query(
        default=None,
        description="YYYY-MM",
    ),
):
    return get_history(
        ticker,
        "balancesheet",
        from_year,
        to_year,
    )


# ============================================================
# GET /companies/{ticker}/cashflow
# ============================================================

@router.get("/{ticker}/cashflow")
def get_cashflow(
    ticker: str,
    from_year: str | None = Query(
        default=None,
        description="YYYY-MM",
    ),
    to_year: str | None = Query(
        default=None,
        description="YYYY-MM",
    ),
):
    return get_history(
        ticker,
        "cashflow",
        from_year,
        to_year,
    )


# ============================================================
# GET /companies/{ticker}/ratios
# ============================================================

@router.get("/{ticker}/ratios")
def get_ratios(
    ticker: str,
    year: str | None = Query(
        default=None,
        description="Optional year in YYYY format",
    ),
):
    if year is not None:
        if not re.fullmatch(r"\d{4}", year):
            raise HTTPException(
                status_code=400,
                detail="year must use YYYY format.",
            )

    conn = get_connection()

    try:
        get_company_or_404(
            conn,
            ticker,
        )

        rows = conn.execute(
            """
            SELECT *
            FROM financial_ratios
            WHERE UPPER(company_id) = UPPER(?)
            ORDER BY id
            """,
            (ticker,),
        ).fetchall()

        if year is not None:
         filtered = [
            row
          for row in rows
          if str(row["year"]).endswith(year)
    ]
        else:
            filtered = rows

        return {
            "ticker": ticker.upper(),
            "count": len(filtered),
            "ratios": filtered,
        }

    finally:
        conn.close()


# ============================================================
# GET /companies/{ticker}/tearsheet
# ============================================================
# ============================================================
# GET /companies/{ticker}/peers/compare
# ============================================================

@router.get("/{ticker}/peers/compare")
def compare_company_with_peers(ticker: str):
    """
    Return radar-chart comparison data for a company,
    its peer-group average, and benchmark company.

    Eight metrics are returned:
        ROE
        ROCE
        Revenue CAGR 5yr
        PAT CAGR 5yr
        EPS CAGR 5yr
        FCF
        D/E
        Net Profit Margin
    """

    conn = get_connection()

    try:
        # ----------------------------------------------------
        # Verify company
        # ----------------------------------------------------

        company = get_company_or_404(conn, ticker)

        ticker_upper = ticker.upper()

        # ----------------------------------------------------
        # Find peer group
        # ----------------------------------------------------

        peer_group = conn.execute(
            """
            SELECT peer_group_name
            FROM peer_groups
            WHERE UPPER(company_id) = UPPER(?)
            LIMIT 1
            """,
            (ticker_upper,),
        ).fetchone()

        if peer_group is None:
            raise HTTPException(
                status_code=404,
                detail=f"No peer group found for '{ticker_upper}'.",
            )

        group_name = peer_group["peer_group_name"]

        # ----------------------------------------------------
        # Eight radar metrics
        # ----------------------------------------------------

        metrics = [
            "ROE",
            "ROCE",
            "Revenue CAGR 5yr",
            "PAT CAGR 5yr",
            "EPS CAGR 5yr",
            "FCF",
            "D/E",
            "Net Profit Margin",
        ]

        # ----------------------------------------------------
        # Company values
        # ----------------------------------------------------

        company_rows = conn.execute(
            """
            SELECT
                metric,
                value,
                percentile_rank,
                year
            FROM peer_percentiles
            WHERE UPPER(company_id) = UPPER(?)
              AND peer_group_name = ?
            """,
            (ticker_upper, group_name),
        ).fetchall()

        company_metrics = {
            row["metric"]: {
                "value": row["value"],
                "percentile_rank": row["percentile_rank"],
                "year": row["year"],
            }
            for row in company_rows
        }

        # ----------------------------------------------------
        # Check that company has peer metrics
        # ----------------------------------------------------

        if not company_metrics:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No peer metrics found for "
                    f"'{ticker_upper}' in '{group_name}'."
                ),
            )

        # ----------------------------------------------------
        # Peer group averages
        # ----------------------------------------------------

        peer_rows = conn.execute(
            """
            SELECT
                metric,
                AVG(value) AS average_value
            FROM peer_percentiles
            WHERE peer_group_name = ?
              AND metric IN (
                    'ROE',
                    'ROCE',
                    'Revenue CAGR 5yr',
                    'PAT CAGR 5yr',
                    'EPS CAGR 5yr',
                    'FCF',
                    'D/E',
                    'Net Profit Margin'
              )
            GROUP BY metric
            """,
            (group_name,),
        ).fetchall()

        peer_average = {
            row["metric"]: row["average_value"]
            for row in peer_rows
        }

        # ----------------------------------------------------
        # Find benchmark company
        # ----------------------------------------------------

        benchmark = conn.execute(
            """
            SELECT
                company_id
            FROM peer_groups
            WHERE peer_group_name = ?
              AND is_benchmark = '1'
            LIMIT 1
            """,
            (group_name,),
        ).fetchone()

        benchmark_ticker = (
            benchmark["company_id"]
            if benchmark
            else None
        )

        benchmark_metrics = {}

        if benchmark_ticker:
            benchmark_rows = conn.execute(
                """
                SELECT
                    metric,
                    value,
                    percentile_rank,
                    year
                FROM peer_percentiles
                WHERE UPPER(company_id) = UPPER(?)
                  AND peer_group_name = ?
                """,
                (
                    benchmark_ticker,
                    group_name,
                ),
            ).fetchall()

            benchmark_metrics = {
                row["metric"]: {
                    "value": row["value"],
                    "percentile_rank": row["percentile_rank"],
                    "year": row["year"],
                }
                for row in benchmark_rows
            }

        # ----------------------------------------------------
        # Build radar data
        # ----------------------------------------------------

        radar = []

        for metric in metrics:

            company_data = company_metrics.get(metric)
            benchmark_data = benchmark_metrics.get(metric)

            radar.append(
                {
                    "metric": metric,
                    "company": (
                        company_data["value"]
                        if company_data
                        else None
                    ),
                    "peer_group_average": peer_average.get(
                        metric
                    ),
                    "benchmark": (
                        benchmark_data["value"]
                        if benchmark_data
                        else None
                    ),
                }
            )

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return {
            "ticker": ticker_upper,
            "company_name": company["company_name"],
            "peer_group": group_name,
            "benchmark_company": benchmark_ticker,
            "axis_count": len(radar),
            "radar": radar,
        }

    finally:
        conn.close()
        
@router.get("/{ticker}/tearsheet")
def get_tearsheet(ticker: str):
    conn = get_connection()

    try:
        get_company_or_404(
            conn,
            ticker,
        )
    finally:
        conn.close()

    # Search the generated tearsheet directories.
    candidates = [
    ROOT / "reports" / "tearsheets" / f"{ticker.upper()}_tearsheet.pdf",
    ROOT / "reports" / "tearsheet" / f"{ticker.upper()}_tearsheet.pdf",
    ROOT / "reports" / "portfolio" / f"{ticker.upper()}_tearsheet.pdf",
]

    pdf_path = next(
        (
            path
            for path in candidates
            if path.exists()
        ),
        None,
    )

    if pdf_path is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Tearsheet PDF for "
                f"'{ticker.upper()}' not found."
            ),
        )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=pdf_path.name,
    )
# ============================================================
# GET /companies/{ticker}/documents
# ============================================================

@router.get("/{ticker}/documents")
def get_company_documents(ticker: str):
    """
    Return annual report links for a company with URL validity flags.
    """

    from urllib.parse import urlparse

    ticker = ticker.upper().strip()

    conn = get_connection()

    try:
        # ----------------------------------------------------
        # Check company exists
        # ----------------------------------------------------

        company = conn.execute(
            """
            SELECT
                id,
                company_name
            FROM companies
            WHERE UPPER(id) = ?
            """,
            (ticker,),
        ).fetchone()

        if company is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company not found: {ticker}",
            )

        # ----------------------------------------------------
        # Get annual reports
        # ----------------------------------------------------

        rows = conn.execute(
            """
            SELECT
                Year,
                Annual_Report
            FROM documents
            WHERE UPPER(company_id) = UPPER(?)
            ORDER BY CAST(Year AS INTEGER) DESC
            """,
            (ticker,),
        ).fetchall()

        documents = []

        for row in rows:
            year = row[0]
            url = row[1]

            # ------------------------------------------------
            # Fast URL validation
            #
            # We only validate the URL structure here.
            # We do NOT contact BSE because external requests
            # can make the API endpoint extremely slow.
            # ------------------------------------------------

            is_url_valid = False

            if url:
                try:
                    parsed = urlparse(str(url).strip())

                    is_url_valid = (
                        parsed.scheme in ("http", "https")
                        and bool(parsed.netloc)
                    )

                except Exception:
                    is_url_valid = False

            documents.append(
                {
                    "year": str(year),
                    "annual_report": url,
                    "is_url_valid": is_url_valid,
                }
            )

        return {
            "ticker": ticker,
            "company_name": company[1],
            "count": len(documents),
            "documents": documents,
        }

    finally:
        conn.close()
