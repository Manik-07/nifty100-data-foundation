import csv
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

ROOT = Path(__file__).resolve().parents[3]
PORTFOLIO_STATS_PATH = ROOT / "output" / "portfolio_stats.csv"


@router.get("/stats")
def get_portfolio_stats():
    """
    Return P10-P90 percentile statistics for the 10 core portfolio KPIs.
    """

    if not PORTFOLIO_STATS_PATH.exists():
        return {
            "count": 0,
            "kpis": [],
            "source": "output/portfolio_stats.csv",
        }

    kpis = []

    with PORTFOLIO_STATS_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            kpis.append(
                {
                    "kpi": row["kpi"],
                    "p10": float(row["p10"]),
                    "p25": float(row["p25"]),
                    "p50": float(row["p50"]),
                    "p75": float(row["p75"]),
                    "p90": float(row["p90"]),
                    "mean": float(row["mean"]),
                    "std": float(row["std"]),
                    "count": int(row["count"]),
                }
            )

    return {
        "count": len(kpis),
        "kpis": kpis,
    }