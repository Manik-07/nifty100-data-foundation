import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException


router = APIRouter()

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "db" / "nifty100.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


# ============================================================
# GET /api/v1/market-cap/{ticker}
# ============================================================

@router.get("/market-cap/{ticker}")
def get_market_cap(ticker: str):
    """
    Return historical valuation multiples for a company
    from 2019 to 2024.
    """

    ticker = ticker.upper().strip()

    conn = get_connection()

    try:
        # ----------------------------------------------------
        # Check company exists
        # ----------------------------------------------------

        company = conn.execute(
            """
            SELECT id, company_name
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
        # Get valuation history
        # ----------------------------------------------------

        rows = conn.execute(
            """
            SELECT
                year,
                market_cap_crore,
                enterprise_value_crore,
                pe_ratio,
                pb_ratio,
                ev_ebitda,
                dividend_yield_pct
            FROM market_cap
            WHERE company_id = ?
              AND year BETWEEN 2019 AND 2024
            ORDER BY year ASC
            """,
            (ticker,),
        ).fetchall()

        history = []

        for row in rows:
            history.append(
                {
                    "year": row[0],
                    "market_cap_crore": row[1],
                    "enterprise_value_crore": row[2],
                    "pe_ratio": row[3],
                    "pb_ratio": row[4],
                    "ev_ebitda": row[5],
                    "dividend_yield_pct": row[6],
                }
            )

        return {
            "ticker": ticker,
            "company_name": company[1],
            "count": len(history),
            "history": history,
        }

    finally:
        conn.close()