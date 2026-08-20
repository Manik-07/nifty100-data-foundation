import logging
import sqlite3
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware



# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DATABASE = ROOT / "db" / "nifty100.db"


# ============================================================
# API CONFIGURATION
# ============================================================

API_VERSION = "1.0.0"


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("nifty100-api")


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():
    """Create a SQLite database connection."""

    return sqlite3.connect(DATABASE)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Nifty 100 Data Foundation API",
    description="REST API for Nifty 100 financial analytics.",
    version=API_VERSION,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST LOGGING MIDDLEWARE
# ============================================================

@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):
    """Log method, path, status code and response time."""

    start_time = time.perf_counter()

    response = await call_next(request)

    elapsed = time.perf_counter() - start_time

    logger.info(
        "%s %s -> %s | %.2f ms",
        request.method,
        request.url.path,
        response.status_code,
        elapsed * 1000,
    )

    return response


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():
    return {
        "name": "Nifty 100 Data Foundation API",
        "version": API_VERSION,
        "docs": "/docs",
        "status": "ok",
    }


# ============================================================
# ROUTERS
# ============================================================

from src.api.routers import (
    companies,
    screener,
    sectors,
    peers,
    valuation,
    portfolio,
    documents,
    health,
)


# ============================================================
# API PREFIXES
# ============================================================

API_PREFIX = "/api/v1"

# ============================================================
# REGISTER ROUTERS
# ============================================================

app.include_router(
    companies.router,
    prefix=API_PREFIX,
    tags=["Companies"],
)

app.include_router(
    screener.router,
    prefix=f"{API_PREFIX}/screener",
    tags=["Screener"],
)

app.include_router(
    sectors.router,
    prefix=f"{API_PREFIX}/sectors",
    tags=["Sectors"],
)

app.include_router(
    peers.router,
    prefix=f"{API_PREFIX}/peers",
    tags=["Peers"],
)

# IMPORTANT:
# valuation router contains /market-cap/{ticker}
# so its prefix must be /api/v1
app.include_router(
    valuation.router,
    prefix=API_PREFIX,
    tags=["Valuation"],
)

app.include_router(
    portfolio.router,
    prefix=f"{API_PREFIX}/portfolio",
    tags=["Portfolio"],
)

app.include_router(
    documents.router,
    prefix=f"{API_PREFIX}/documents",
    tags=["Documents"],
)

app.include_router(
    health.router,
    prefix=API_PREFIX,
    tags=["Health"],
)