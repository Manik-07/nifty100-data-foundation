import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()

# ============================================================
# DATABASE
# ============================================================

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "db" / "nifty100.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


# ============================================================
# GET /api/v1/sectors
# ============================================================

@router.get("")
def get_sectors():
    """
    Return all sectors with:
    - company_count
    - median ROE
    - median P/E
    - median D/E
    """

    conn = get_connection()

    try:
        # ----------------------------------------------------
        # Get all sectors
        # ----------------------------------------------------

        sectors = conn.execute(
            """
            SELECT DISTINCT broad_sector
            FROM sectors
            WHERE broad_sector IS NOT NULL
            ORDER BY broad_sector
            """
        ).fetchall()

        results = []

        for (sector,) in sectors:

            # ------------------------------------------------
            # Company count
            # ------------------------------------------------

            company_count = conn.execute(
                """
                SELECT COUNT(DISTINCT company_id)
                FROM sectors
                WHERE broad_sector = ?
                """,
                (sector,),
            ).fetchone()[0]

            # ------------------------------------------------
            # Latest ROE values
            # ------------------------------------------------

            roe_values = conn.execute(
                """
                SELECT fr.return_on_equity_pct
                FROM financial_ratios fr
                INNER JOIN sectors s
                    ON fr.company_id = s.company_id
                WHERE s.broad_sector = ?
                  AND fr.year = (
                      SELECT MAX(fr2.year)
                      FROM financial_ratios fr2
                      WHERE fr2.company_id = fr.company_id
                  )
                  AND fr.return_on_equity_pct IS NOT NULL
                """,
                (sector,),
            ).fetchall()

            # ------------------------------------------------
            # Latest D/E values
            # ------------------------------------------------

            de_values = conn.execute(
                """
                SELECT fr.debt_to_equity
                FROM financial_ratios fr
                INNER JOIN sectors s
                    ON fr.company_id = s.company_id
                WHERE s.broad_sector = ?
                  AND fr.year = (
                      SELECT MAX(fr2.year)
                      FROM financial_ratios fr2
                      WHERE fr2.company_id = fr.company_id
                  )
                  AND fr.debt_to_equity IS NOT NULL
                """,
                (sector,),
            ).fetchall()

            # ------------------------------------------------
            # Latest P/E values
            # ------------------------------------------------

            pe_values = conn.execute(
                """
                SELECT mc.pe_ratio
                FROM market_cap mc
                INNER JOIN sectors s
                    ON mc.company_id = s.company_id
                WHERE s.broad_sector = ?
                  AND mc.year = (
                      SELECT MAX(mc2.year)
                      FROM market_cap mc2
                      WHERE mc2.company_id = mc.company_id
                  )
                  AND mc.pe_ratio IS NOT NULL
                """,
                (sector,),
            ).fetchall()

            # ------------------------------------------------
            # Median helper
            # ------------------------------------------------

            def median(values):
                values = sorted(
                    float(row[0])
                    for row in values
                    if row[0] is not None
                )

                if not values:
                    return None

                n = len(values)
                middle = n // 2

                if n % 2 == 0:
                    return round(
                        (values[middle - 1] + values[middle]) / 2,
                        2,
                    )

                return round(values[middle], 2)

            results.append(
                {
                    "sector": sector,
                    "company_count": company_count,
                    "median_roe": median(roe_values),
                    "median_pe": median(pe_values),
                    "median_de": median(de_values),
                }
            )

        return {
            "count": len(results),
            "sectors": results,
        }

    finally:
        conn.close()


# ============================================================
# GET /api/v1/sectors/{sector}/companies
# ============================================================

@router.get("/{sector}/companies")
def get_sector_companies(sector: str):
    """
    Return all companies in a sector with latest-year KPIs.
    """

    conn = get_connection()

    try:

        # ----------------------------------------------------
        # Check sector exists
        # ----------------------------------------------------

        sector_exists = conn.execute(
            """
            SELECT COUNT(*)
            FROM sectors
            WHERE LOWER(broad_sector) = LOWER(?)
            """,
            (sector,),
        ).fetchone()[0]

        if sector_exists == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown sector: {sector}",
            )

        # ----------------------------------------------------
        # Get companies + latest ratios
        # ----------------------------------------------------

        rows = conn.execute(
            """
            WITH latest_ratios AS (
                SELECT fr.*
                FROM financial_ratios fr
                WHERE fr.year = (
                    SELECT MAX(fr2.year)
                    FROM financial_ratios fr2
                    WHERE fr2.company_id = fr.company_id
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
                lr.net_profit_margin_pct,
                lr.operating_profit_margin_pct,
                lr.debt_to_equity AS de,
                lr.free_cash_flow_cr AS fcf,
                lr.revenue_cagr_5yr,
                lr.pat_cagr_5yr,
                lr.eps_cagr_5yr,
                lr.interest_coverage,
                lr.asset_turnover,
                lr.composite_quality_score

            FROM companies c

            INNER JOIN sectors s
                ON c.id = s.company_id

            LEFT JOIN latest_ratios lr
                ON c.id = lr.company_id

            WHERE LOWER(s.broad_sector) = LOWER(?)

            ORDER BY
                lr.composite_quality_score DESC,
                c.company_name ASC
            """,
            (sector,),
        ).fetchall()

        columns = [
            "company_id",
            "company_name",
            "broad_sector",
            "sub_sector",
            "market_cap_category",
            "year",
            "roe_pct",
            "roce_pct",
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "de",
            "fcf",
            "revenue_cagr_5yr",
            "pat_cagr_5yr",
            "eps_cagr_5yr",
            "interest_coverage",
            "asset_turnover",
            "composite_quality_score",
        ]

        results = [
            dict(zip(columns, row))
            for row in rows
        ]

        return {
            "sector": sector,
            "count": len(results),
            "companies": results,
        }

    finally:
        conn.close()