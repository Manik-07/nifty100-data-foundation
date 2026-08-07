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
# ---------------------------------------------------------
# Screener
# ---------------------------------------------------------

@st.cache_data(ttl=600)
def get_screener_data():
    """
    Return latest available financial and valuation metrics
    for all companies for use on the Screener screen.
    """

    query = """
        WITH latest_ratios AS (
            SELECT f.*
            FROM financial_ratios f
            INNER JOIN (
                SELECT company_id, MAX(year) AS latest_year
                FROM financial_ratios
                GROUP BY company_id
            ) latest
                ON f.company_id = latest.company_id
               AND f.year = latest.latest_year
        ),

        latest_valuation AS (
            SELECT m.*
            FROM market_cap m
            INNER JOIN (
                SELECT company_id, MAX(year) AS latest_year
                FROM market_cap
                GROUP BY company_id
            ) latest
                ON m.company_id = latest.company_id
               AND m.year = latest.latest_year
        )

        SELECT
            c.id AS company_id,
            c.company_name,
            s.broad_sector AS sector,

            f.composite_quality_score,
            f.return_on_equity_pct AS roe,
            f.debt_to_equity AS debt_to_equity,
            f.free_cash_flow_cr AS fcf,
            f.revenue_cagr_5yr AS revenue_cagr,
            f.pat_cagr_5yr AS pat_cagr,
            f.operating_profit_margin_pct AS opm,
            f.interest_coverage AS icr,

            m.pe_ratio AS pe,
            m.pb_ratio AS pb,
            m.dividend_yield_pct AS dividend_yield

        FROM companies c

        LEFT JOIN sectors s
            ON c.id = s.company_id

        LEFT JOIN latest_ratios f
            ON c.id = f.company_id

        LEFT JOIN latest_valuation m
            ON c.id = m.company_id

        ORDER BY c.company_name
    """

    with get_connection() as conn:
        return pd.read_sql_query(query, conn)
    
# ---------------------------------------------------------
# Peer Comparison Metrics
# ---------------------------------------------------------

@st.cache_data(ttl=600)
def get_peer_metrics(group_name):
    """
    Return latest financial and valuation metrics for
    companies belonging to the selected peer group.
    """

    query = """
        WITH latest_ratios AS (
            SELECT f.*
            FROM financial_ratios f
            INNER JOIN (
                SELECT company_id, MAX(year) AS latest_year
                FROM financial_ratios
                GROUP BY company_id
            ) latest
                ON f.company_id = latest.company_id
               AND f.year = latest.latest_year
        ),

        latest_valuation AS (
            SELECT m.*
            FROM market_cap m
            INNER JOIN (
                SELECT company_id, MAX(year) AS latest_year
                FROM market_cap
                GROUP BY company_id
            ) latest
                ON m.company_id = latest.company_id
               AND m.year = latest.latest_year
        )

        SELECT
            p.peer_group_name,
            p.company_id,
            c.company_name,
            p.is_benchmark,
            s.broad_sector,
            s.sub_sector,

            f.return_on_equity_pct AS roe,
            f.operating_profit_margin_pct AS opm,
            f.debt_to_equity AS debt_to_equity,
            f.revenue_cagr_5yr AS revenue_cagr,
            f.pat_cagr_5yr AS pat_cagr,
            f.interest_coverage AS icr,

            m.pe_ratio AS pe,
            m.dividend_yield_pct AS dividend_yield

        FROM peer_groups p

        LEFT JOIN companies c
            ON p.company_id = c.id

        LEFT JOIN sectors s
            ON p.company_id = s.company_id

        LEFT JOIN latest_ratios f
            ON p.company_id = f.company_id

        LEFT JOIN latest_valuation m
            ON p.company_id = m.company_id

        WHERE p.peer_group_name = ?

        ORDER BY c.company_name
    """

    with get_connection() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=(group_name,),
        )
# ---------------------------------------------------------
# Trend Analysis
# ---------------------------------------------------------

@st.cache_data(ttl=600)
def get_trend_data(ticker):
    """
    Return historical financial metrics for Trend Analysis.
    Combines Profit & Loss data with Financial Ratios.
    """

    query = """
        SELECT
            p.company_id,
            p.year,
            p.sales,
            p.operating_profit,
            p.net_profit,
            p.eps,

            f.return_on_equity_pct,
            f.operating_profit_margin_pct,
            f.net_profit_margin_pct,
            f.debt_to_equity,
            f.free_cash_flow_cr,
            f.interest_coverage

        FROM profitandloss p

        LEFT JOIN financial_ratios f
            ON p.company_id = f.company_id
            AND p.year = f.year

        WHERE p.company_id = ?

        ORDER BY
            CAST(SUBSTR(p.year, -4) AS INTEGER)
    """

    with get_connection() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=(ticker,),
        )
# ---------------------------------------------------------
# Sector Analysis
# ---------------------------------------------------------

@st.cache_data(ttl=600)
def get_sector_analysis():
    """
    Return latest Revenue, ROE and Market Cap data
    for all companies for Sector Analysis.
    """

    query = """
        WITH latest_pl AS (
            SELECT p.*
            FROM profitandloss p
            INNER JOIN (
                SELECT
                    company_id,
                    MAX(
                        CAST(SUBSTR(year, -4) AS INTEGER)
                    ) AS latest_year
                FROM profitandloss
                WHERE year GLOB '*[0-9][0-9][0-9][0-9]'
                GROUP BY company_id
            ) latest
                ON p.company_id = latest.company_id
                AND CAST(SUBSTR(p.year, -4) AS INTEGER)
                    = latest.latest_year
        ),

        latest_ratios AS (
            SELECT f.*
            FROM financial_ratios f
            INNER JOIN (
                SELECT
                    company_id,
                    MAX(
                        CAST(SUBSTR(year, -4) AS INTEGER)
                    ) AS latest_year
                FROM financial_ratios
                WHERE year GLOB '*[0-9][0-9][0-9][0-9]'
                GROUP BY company_id
            ) latest
                ON f.company_id = latest.company_id
                AND CAST(SUBSTR(f.year, -4) AS INTEGER)
                    = latest.latest_year
        ),

        latest_market AS (
            SELECT m.*
            FROM market_cap m
            INNER JOIN (
                SELECT
                    company_id,
                    MAX(
                        CAST(SUBSTR(year, -4) AS INTEGER)
                    ) AS latest_year
                FROM market_cap
                WHERE year GLOB '*[0-9][0-9][0-9][0-9]'
                GROUP BY company_id
            ) latest
                ON m.company_id = latest.company_id
                AND CAST(SUBSTR(m.year, -4) AS INTEGER)
                    = latest.latest_year
        )

        SELECT
            c.id AS company_id,
            c.company_name,

            s.broad_sector,
            s.sub_sector,

            p.sales AS revenue,
            f.return_on_equity_pct AS roe,
            f.operating_profit_margin_pct AS opm,
            f.net_profit_margin_pct AS npm,
            f.debt_to_equity,
            f.revenue_cagr_5yr,
            f.pat_cagr_5yr,

            m.market_cap_crore,
            m.pe_ratio,
            m.pb_ratio,
            m.dividend_yield_pct

        FROM companies c

        LEFT JOIN sectors s
            ON c.id = s.company_id

        LEFT JOIN latest_pl p
            ON c.id = p.company_id

        LEFT JOIN latest_ratios f
            ON c.id = f.company_id

        LEFT JOIN latest_market m
            ON c.id = m.company_id

        ORDER BY
            s.broad_sector,
            c.company_name
    """

    with get_connection() as conn:
     df = pd.read_sql_query(query, conn)

# Guarantee one row per company
    if not df.empty:
        df = df.drop_duplicates(
            subset=["company_id"],
            keep="last",
        ).reset_index(drop=True)

    return df

# ---------------------------------------------------------
# Capital Allocation Map
# ---------------------------------------------------------

@st.cache_data(ttl=600)
def get_capital_allocation():
    """
    Return the latest annual cash-flow record for each company
    for Capital Allocation analysis.
    """

    query = """
        WITH ranked_cashflow AS (
            SELECT
                cf.*,

                CAST(
                    SUBSTR(cf.year, -4)
                    AS INTEGER
                ) AS year_number,

                ROW_NUMBER() OVER (
                    PARTITION BY cf.company_id

                    ORDER BY
                        CAST(
                            SUBSTR(cf.year, -4)
                            AS INTEGER
                        ) DESC,
                        cf.id DESC
                ) AS rn

            FROM cashflow cf

            WHERE cf.year GLOB '*[0-9][0-9][0-9][0-9]'
        )

        SELECT
            c.id AS company_id,
            c.company_name,

            s.broad_sector,
            s.sub_sector,

            r.year,
            r.operating_activity,
            r.investing_activity,
            r.financing_activity,
            r.net_cash_flow,

            m.market_cap_crore

        FROM companies c

        LEFT JOIN sectors s
            ON c.id = s.company_id

        LEFT JOIN ranked_cashflow r
            ON c.id = r.company_id
            AND r.rn = 1

        LEFT JOIN (
            SELECT m1.*
            FROM market_cap m1

            INNER JOIN (
                SELECT
                    company_id,
                    MAX(
                        CAST(
                            SUBSTR(year, -4)
                            AS INTEGER
                        )
                    ) AS latest_year

                FROM market_cap

                WHERE year GLOB '*[0-9][0-9][0-9][0-9]'

                GROUP BY company_id

            ) latest

                ON m1.company_id = latest.company_id

                AND CAST(
                    SUBSTR(m1.year, -4)
                    AS INTEGER
                ) = latest.latest_year

        ) m

            ON c.id = m.company_id

        ORDER BY c.company_name
    """

    with get_connection() as conn:
        df = pd.read_sql_query(query, conn)

    if not df.empty:

        df = df.drop_duplicates(
            subset=["company_id"],
            keep="last",
        ).reset_index(drop=True)

    return df
# ---------------------------------------------------------
# Annual Reports
# ---------------------------------------------------------

@st.cache_data(ttl=600)
def get_annual_reports(ticker):
    """
    Return available annual report records for a company.
    """

    query = """
        SELECT
            d.company_id,
            c.company_name,
            d.Year AS year,
            d.Annual_Report AS annual_report

        FROM documents d

        LEFT JOIN companies c
            ON d.company_id = c.id

        WHERE UPPER(d.company_id) = UPPER(?)

        ORDER BY
            CAST(d.Year AS INTEGER) DESC
    """

    with get_connection() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=(ticker,),
        )