from pathlib import Path
from typing import Optional
import sqlite3

from fastapi import APIRouter, HTTPException, Query


router = APIRouter()


# ============================================================
# DATABASE
# ============================================================

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "db" / "nifty100.db"


def get_connection():
    """Create a SQLite database connection."""
    return sqlite3.connect(DB_PATH)


# ============================================================
# VALIDATION
# ============================================================

def parse_number(
    value: Optional[str],
    name: str,
    minimum: Optional[float] = None,
):
    """
    Convert query parameter to float.

    Invalid values return HTTP 400.
    """

    if value is None or value.strip() == "":
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=400,
            detail=f"{name} must be a valid number.",
        )

    if minimum is not None and number < minimum:
        raise HTTPException(
            status_code=400,
            detail=f"{name} must be >= {minimum}.",
        )

    return number


# ============================================================
# GET /api/v1/screener
# ============================================================

@router.get("")
def screener(
    min_roe: Optional[str] = Query(
        None,
        description="Minimum ROE percentage",
    ),
    max_de: Optional[str] = Query(
        None,
        description="Maximum debt-to-equity",
    ),
    min_fcf: Optional[str] = Query(
        None,
        description="Minimum free cash flow in Cr",
    ),
    sector: Optional[str] = Query(
        None,
        description="Broad sector",
    ),
    min_rev_cagr_5yr: Optional[str] = Query(
        None,
        description="Minimum 5-year revenue CAGR",
    ),
    min_pat_cagr_5yr: Optional[str] = Query(
        None,
        description="Minimum 5-year PAT CAGR",
    ),
    max_pe: Optional[str] = Query(
        None,
        description="Maximum P/E",
    ),
):
    """
    Screen companies using the latest financial data.
    """

    # ========================================================
    # PARSE NUMERIC FILTERS
    # ========================================================

    min_roe = parse_number(
        min_roe,
        "min_roe",
        0,
    )

    max_de = parse_number(
        max_de,
        "max_de",
        0,
    )

    min_fcf = parse_number(
        min_fcf,
        "min_fcf",
    )

    min_rev_cagr_5yr = parse_number(
        min_rev_cagr_5yr,
        "min_rev_cagr_5yr",
    )

    min_pat_cagr_5yr = parse_number(
        min_pat_cagr_5yr,
        "min_pat_cagr_5yr",
    )

    max_pe = parse_number(
        max_pe,
        "max_pe",
        0,
    )

    # ========================================================
    # VALIDATE SECTOR
    # ========================================================

    if sector is not None:
        sector = sector.strip()

        if not sector:
            raise HTTPException(
                status_code=400,
                detail="sector cannot be empty.",
            )

    # ========================================================
    # DATABASE
    # ========================================================

    conn = get_connection()

    try:

        # ====================================================
        # LATEST FINANCIAL RATIOS
        # ====================================================

        query = """
            WITH latest_ratios AS (
                SELECT *
                FROM financial_ratios fr
                WHERE fr.year = (
                    SELECT MAX(fr2.year)
                    FROM financial_ratios fr2
                    WHERE fr2.company_id = fr.company_id
                )
            ),

            latest_market_cap AS (
                SELECT *
                FROM market_cap mc
                WHERE mc.year = (
                    SELECT MAX(mc2.year)
                    FROM market_cap mc2
                    WHERE mc2.company_id = mc.company_id
                )
            )

            SELECT
                c.id AS company_id,
                c.company_name,

                s.broad_sector,
                s.sub_sector,
                s.market_cap_category,

                lr.year,

                lr.return_on_equity_pct AS roe_pct,
                c.roce_percentage AS roce_pct,

                lr.debt_to_equity AS de,
                lr.free_cash_flow_cr AS fcf,

                lr.revenue_cagr_5yr,
                lr.pat_cagr_5yr,
                lr.eps_cagr_5yr,

                lr.net_profit_margin_pct,
                lr.operating_profit_margin_pct,

                lr.interest_coverage,
                lr.asset_turnover,

                lr.composite_quality_score,

                mc.pe_ratio AS pe

            FROM companies c

            LEFT JOIN latest_ratios lr
                ON c.id = lr.company_id

            LEFT JOIN sectors s
                ON c.id = s.company_id

            LEFT JOIN latest_market_cap mc
                ON c.id = mc.company_id

            WHERE 1 = 1
        """

        params = []

        # ====================================================
        # FILTERS
        # ====================================================

        if min_roe is not None:
            query += """
                AND lr.return_on_equity_pct >= ?
            """
            params.append(min_roe)

        if max_de is not None:
            query += """
                AND lr.debt_to_equity <= ?
            """
            params.append(max_de)

        if min_fcf is not None:
            query += """
                AND lr.free_cash_flow_cr >= ?
            """
            params.append(min_fcf)

        if min_rev_cagr_5yr is not None:
            query += """
                AND lr.revenue_cagr_5yr >= ?
            """
            params.append(min_rev_cagr_5yr)

        if min_pat_cagr_5yr is not None:
            query += """
                AND lr.pat_cagr_5yr >= ?
            """
            params.append(min_pat_cagr_5yr)

        if sector is not None:
            query += """
                AND LOWER(s.broad_sector) = LOWER(?)
            """
            params.append(sector)

        if max_pe is not None:
            query += """
                AND mc.pe_ratio <= ?
            """
            params.append(max_pe)

        # ====================================================
        # RANKING
        # ====================================================

        query += """
            ORDER BY
                lr.composite_quality_score DESC,
                lr.return_on_equity_pct DESC,
                c.id ASC
        """

        # ====================================================
        # EXECUTE
        # ====================================================

        rows = conn.execute(
            query,
            params,
        ).fetchall()

        # ====================================================
        # CONVERT TO JSON
        # ====================================================

        columns = [
            "company_id",
            "company_name",
            "broad_sector",
            "sub_sector",
            "market_cap_category",
            "year",
            "roe_pct",
            "roce_pct",
            "de",
            "fcf",
            "revenue_cagr_5yr",
            "pat_cagr_5yr",
            "eps_cagr_5yr",
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "interest_coverage",
            "asset_turnover",
            "composite_quality_score",
            "pe",
        ]

        results = [
            dict(zip(columns, row))
            for row in rows
        ]

        return {
            "count": len(results),
            "filters": {
                "min_roe": min_roe,
                "max_de": max_de,
                "min_fcf": min_fcf,
                "sector": sector,
                "min_rev_cagr_5yr": min_rev_cagr_5yr,
                "min_pat_cagr_5yr": min_pat_cagr_5yr,
                "max_pe": max_pe,
            },
            "results": results,
        }

    finally:
        conn.close()