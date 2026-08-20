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
# GET /api/v1/peers/{group_name}
# ============================================================

@router.get("/{group_name}")
def get_peer_group(group_name: str):
    """
    Return all companies in a peer group with percentile
    ranks for each metric.
    """

    conn = get_connection()

    try:
        # ----------------------------------------------------
        # Check whether peer group exists
        # ----------------------------------------------------

        group_exists = conn.execute(
            """
            SELECT COUNT(*)
            FROM peer_groups
            WHERE LOWER(peer_group_name) = LOWER(?)
            """,
            (group_name,),
        ).fetchone()[0]

        if group_exists == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown peer group: {group_name}",
            )

        # ----------------------------------------------------
        # Get companies belonging to peer group
        # ----------------------------------------------------

        companies = conn.execute(
            """
            SELECT
                pg.company_id,
                c.company_name,
                pg.is_benchmark
            FROM peer_groups pg
            LEFT JOIN companies c
                ON c.id = pg.company_id
            WHERE LOWER(pg.peer_group_name) = LOWER(?)
            ORDER BY
                pg.is_benchmark DESC,
                c.company_name ASC
            """,
            (group_name,),
        ).fetchall()

        # ----------------------------------------------------
        # Get percentile data
        # ----------------------------------------------------

        percentile_rows = conn.execute(
            """
            SELECT
                pp.company_id,
                pp.metric,
                pp.value,
                pp.percentile_rank,
                pp.year
            FROM peer_percentiles pp
            WHERE LOWER(pp.peer_group_name) = LOWER(?)
            ORDER BY
                pp.company_id,
                pp.metric
            """,
            (group_name,),
        ).fetchall()

        # ----------------------------------------------------
        # Build company dictionary
        # ----------------------------------------------------

        results = {}

        for company_id, company_name, is_benchmark in companies:
            results[company_id] = {
                "company_id": company_id,
                "company_name": company_name,
                "is_benchmark": is_benchmark == "1",
                "metrics": [],
            }

        # ----------------------------------------------------
        # Add percentile metrics
        # ----------------------------------------------------

        for (
            company_id,
            metric,
            value,
            percentile_rank,
            year,
        ) in percentile_rows:

            if company_id not in results:
                results[company_id] = {
                    "company_id": company_id,
                    "company_name": None,
                    "is_benchmark": False,
                    "metrics": [],
                }

            results[company_id]["metrics"].append(
                {
                    "metric": metric,
                    "value": value,
                    "percentile_rank": percentile_rank,
                    "year": year,
                }
            )

        # ----------------------------------------------------
        # Convert dictionary to list
        # ----------------------------------------------------

        company_results = list(results.values())

        return {
            "peer_group": group_name,
            "count": len(company_results),
            "companies": company_results,
        }

    finally:
        conn.close()