from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st


# ---------------------------------------------------------
# Database Configuration
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"


def get_connection():
    """
    Create and return a connection to the Nifty 100 SQLite database.
    """
    return sqlite3.connect(DB_PATH)


# ---------------------------------------------------------
# Companies
# ---------------------------------------------------------

@st.cache_data(ttl=600)
def get_companies():
    """
    Return all companies with their sector information.
    """

    query = """
        SELECT
            c.id AS company_id,
            c.company_name,
            c.company_logo,
            c.about_company,
            c.website,
            c.face_value,
            c.book_value,
            c.roce_percentage,
            c.roe_percentage,
            s.broad_sector,
            s.sub_sector,
            s.index_weight_pct,
            s.market_cap_category
        FROM companies c
        LEFT JOIN sectors s
            ON c.id = s.company_id
        ORDER BY c.company_name
    """

    with get_connection() as conn:
        return pd.read_sql_query(query, conn)


# ---------------------------------------------------------
# Financial Ratios
# ---------------------------------------------------------

@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    """
    Return financial ratios for a company.

    If year is provided, return data for that year only.
    Otherwise return all available years.
    """

    if year is None:
        query = """
            SELECT *
            FROM financial_ratios
            WHERE company_id = ?
            ORDER BY year
        """

        params = (ticker,)

    else:
        query = """
            SELECT *
            FROM financial_ratios
            WHERE company_id = ?
              AND year = ?
            ORDER BY year
        """

        params = (ticker, str(year))

    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)


# ---------------------------------------------------------
# Profit & Loss
# ---------------------------------------------------------

@st.cache_data(ttl=600)
def get_pl(ticker):
    """
    Return Profit & Loss history for a company.
    """

    query = """
        SELECT *
        FROM profitandloss
        WHERE company_id = ?
        ORDER BY year
    """

    with get_connection() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=(ticker,)
        )


# ---------------------------------------------------------
# Balance Sheet
# ---------------------------------------------------------

@st.cache_data(ttl=600)
def get_bs(ticker):
    """
    Return Balance Sheet history for a company.
    """

    query = """
        SELECT *
        FROM balancesheet
        WHERE company_id = ?
        ORDER BY year
    """

    with get_connection() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=(ticker,)
        )


# ---------------------------------------------------------
# Cash Flow
# ---------------------------------------------------------

@st.cache_data(ttl=600)
def get_cf(ticker):
    """
    Return Cash Flow history for a company.
    """

    query = """
        SELECT *
        FROM cashflow
        WHERE company_id = ?
        ORDER BY year
    """

    with get_connection() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=(ticker,)
        )


# ---------------------------------------------------------
# Sectors
# ---------------------------------------------------------

@st.cache_data(ttl=600)
def get_sectors():
    """
    Return sector information for all companies.
    """

    query = """
        SELECT
            s.company_id,
            c.company_name,
            s.broad_sector,
            s.sub_sector,
            s.index_weight_pct,
            s.market_cap_category
        FROM sectors s
        LEFT JOIN companies c
            ON s.company_id = c.id
        ORDER BY s.broad_sector, c.company_name
    """

    with get_connection() as conn:
        return pd.read_sql_query(query, conn)


# ---------------------------------------------------------
# Peer Groups
# ---------------------------------------------------------

@st.cache_data(ttl=600)
def get_peers(group_name):
    """
    Return all companies belonging to a peer group.
    """

    query = """
        SELECT
            p.peer_group_name,
            p.company_id,
            c.company_name,
            p.is_benchmark,
            s.broad_sector,
            s.sub_sector
        FROM peer_groups p
        LEFT JOIN companies c
            ON p.company_id = c.id
        LEFT JOIN sectors s
            ON p.company_id = s.company_id
        WHERE p.peer_group_name = ?
        ORDER BY c.company_name
    """

    with get_connection() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=(group_name,)
        )


# ---------------------------------------------------------
# Valuation
# ---------------------------------------------------------

@st.cache_data(ttl=600)
def get_valuation(ticker):
    """
    Return valuation history for a company.
    """

    query = """
        SELECT
            m.company_id,
            c.company_name,
            m.year,
            m.market_cap_crore,
            m.enterprise_value_crore,
            m.pe_ratio,
            m.pb_ratio,
            m.ev_ebitda,
            m.dividend_yield_pct
        FROM market_cap m
        LEFT JOIN companies c
            ON m.company_id = c.id
        WHERE m.company_id = ?
        ORDER BY m.year
    """

    with get_connection() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=(ticker,)
        )
        
@st.cache_data(ttl=600)
def get_home_metrics(year):
    """
    Return company-level financial metrics for the selected calendar year.

    If a company has more than one record in the selected year,
    the latest available record is retained.
    """

    query = """
        SELECT
            f.company_id,
            c.company_name,
            s.broad_sector,
            f.year,
            f.return_on_equity_pct,
            f.debt_to_equity,
            f.revenue_cagr_5yr,
            f.composite_quality_score,
            f.free_cash_flow_cr,
            f.pat_cagr_5yr
        FROM financial_ratios f

        LEFT JOIN companies c
            ON f.company_id = c.id

        LEFT JOIN sectors s
            ON f.company_id = s.company_id

        WHERE CAST(SUBSTR(f.year, -4) AS INTEGER) = ?
    """

    with get_connection() as conn:
        df = pd.read_sql_query(
            query,
            conn,
            params=(year,)
        )

    if not df.empty:
        df = df.drop_duplicates(
            subset=["company_id"],
            keep="last"
        )

    return df
@st.cache_data(ttl=600)
def get_company_profile(ticker):
    """
    Return company profile, sector and pros/cons information.
    """

    query = """
        SELECT
            c.id AS company_id,
            c.company_name,
            c.company_logo,
            c.about_company,
            c.website,
            c.face_value,
            c.book_value,
            c.roce_percentage,
            c.roe_percentage,
            s.broad_sector,
            s.sub_sector,
            s.market_cap_category,
            pc.pros,
            pc.cons
        FROM companies c

        LEFT JOIN sectors s
            ON c.id = s.company_id

        LEFT JOIN prosandcons pc
            ON c.id = pc.company_id

        WHERE UPPER(c.id) = UPPER(?)
    """

    with get_connection() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=(ticker,)
        )