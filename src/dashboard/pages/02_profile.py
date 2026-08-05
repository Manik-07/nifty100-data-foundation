import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.db import (
    get_companies,
    get_company_profile,
    get_ratios,
    get_pl,
    get_cf,
)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def format_value(value, suffix="", decimals=2):
    if value is None or pd.isna(value):
        return "N/A"

    return f"{value:.{decimals}f}{suffix}"


def extract_year(value):
    try:
        return int(str(value)[-4:])
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------
# Page Header
# ---------------------------------------------------------

st.title("Company Profile")

st.caption(
    "Search a Nifty 100 company and explore its financial performance."
)


# ---------------------------------------------------------
# Load Companies
# ---------------------------------------------------------

companies = get_companies()

companies = companies.drop_duplicates(
    subset=["company_id"]
).copy()


companies["search_label"] = (
    companies["company_name"].fillna("")
    + " ("
    + companies["company_id"].fillna("")
    + ")"
)


# ---------------------------------------------------------
# Company Search
# ---------------------------------------------------------

search_text = st.text_input(
    "Search company or ticker",
    placeholder="Example: RELIANCE or Reliance Industries",
)


filtered = companies.copy()

if search_text:

    mask = (
        companies["company_name"]
        .str.contains(search_text, case=False, na=False)
        |
        companies["company_id"]
        .str.contains(search_text, case=False, na=False)
    )

    filtered = companies[mask]


if filtered.empty:

    st.warning(
        "Ticker not found — please try another."
    )

    st.stop()


selected_label = st.selectbox(
    "Select Company",
    filtered["search_label"].tolist(),
)


selected_ticker = filtered.loc[
    filtered["search_label"] == selected_label,
    "company_id",
].iloc[0]


# ---------------------------------------------------------
# Load Company Data
# ---------------------------------------------------------

profile = get_company_profile(selected_ticker)
ratios = get_ratios(selected_ticker)
pl = get_pl(selected_ticker)
cf = get_cf(selected_ticker)


if profile.empty:

    st.warning(
        "Ticker not found — please try another."
    )

    st.stop()


company = profile.iloc[0]


# ---------------------------------------------------------
# Company Card
# ---------------------------------------------------------

st.divider()

st.subheader(company["company_name"])

info1, info2, info3 = st.columns(3)

with info1:
    st.write("**NSE Ticker**")
    st.write(selected_ticker)

with info2:
    st.write("**Sector**")
    st.write(
        company["broad_sector"]
        if pd.notna(company["broad_sector"])
        else "N/A"
    )

with info3:
    st.write("**Sub-Sector**")
    st.write(
        company["sub_sector"]
        if pd.notna(company["sub_sector"])
        else "N/A"
    )


st.write("**About Company**")

about = company["about_company"]

if pd.notna(about) and str(about).strip():
    st.write(about)
else:
    st.write("Company description unavailable.")


# ---------------------------------------------------------
# Latest Financial Ratios
# ---------------------------------------------------------

if not ratios.empty:

    ratios = ratios.copy()

    ratios["numeric_year"] = ratios["year"].apply(
        extract_year
    )

    ratios = ratios.sort_values(
        "numeric_year"
    )

    latest_ratio = ratios.iloc[-1]

else:
    latest_ratio = None


# ---------------------------------------------------------
# Latest Cash Flow
# ---------------------------------------------------------

if not cf.empty:

    cf = cf.copy()

    cf["numeric_year"] = cf["year"].apply(
        extract_year
    )

    cf = cf.sort_values(
        "numeric_year"
    )

    latest_cf = cf.iloc[-1]

else:
    latest_cf = None


# ---------------------------------------------------------
# KPI Tiles
# ---------------------------------------------------------

st.subheader("Key Financial Metrics")

k1, k2, k3 = st.columns(3)

with k1:

    roe = (
        latest_ratio["return_on_equity_pct"]
        if latest_ratio is not None
        else None
    )

    st.metric(
        "ROE",
        format_value(roe, "%")
    )


with k2:

    roce = company["roce_percentage"]

    st.metric(
        "ROCE",
        format_value(roce, "%")
    )


with k3:

    npm = (
        latest_ratio["net_profit_margin_pct"]
        if latest_ratio is not None
        else None
    )

    st.metric(
        "Net Profit Margin",
        format_value(npm, "%")
    )


k4, k5, k6 = st.columns(3)

with k4:

    de = (
        latest_ratio["debt_to_equity"]
        if latest_ratio is not None
        else None
    )

    st.metric(
        "Debt / Equity",
        format_value(de)
    )


with k5:

    revenue_cagr = (
        latest_ratio["revenue_cagr_5yr"]
        if latest_ratio is not None
        else None
    )

    st.metric(
        "Revenue CAGR 5Y",
        format_value(revenue_cagr, "%")
    )


with k6:

    fcf = (
        latest_ratio["free_cash_flow_cr"]
        if latest_ratio is not None
        else None
    )

    st.metric(
        "Free Cash Flow",
        (
            f"₹{fcf:,.2f} Cr"
            if fcf is not None and not pd.isna(fcf)
            else "N/A"
        )
    )


# ---------------------------------------------------------
# Revenue + Net Profit Chart
# ---------------------------------------------------------

st.divider()

st.subheader("Revenue & Net Profit Trend")


if not pl.empty:

    pl_chart = pl.copy()

    pl_chart["numeric_year"] = pl_chart["year"].apply(
        extract_year
    )

    pl_chart = (
        pl_chart
        .dropna(subset=["numeric_year"])
        .sort_values("numeric_year")
        .tail(10)
    )


    fig_financial = go.Figure()

    fig_financial.add_trace(
        go.Bar(
            x=pl_chart["numeric_year"],
            y=pl_chart["sales"],
            name="Revenue",
        )
    )

    fig_financial.add_trace(
        go.Bar(
            x=pl_chart["numeric_year"],
            y=pl_chart["net_profit"],
            name="Net Profit",
        )
    )


    fig_financial.update_layout(
        xaxis_title="Year",
        yaxis_title="₹ Crore",
        barmode="group",
        legend_title="Metric",
    )


    st.plotly_chart(
        fig_financial,
        use_container_width=True,
    )

else:

    st.info(
        "Revenue and net profit history is unavailable."
    )


# ---------------------------------------------------------
# ROE + ROCE Chart
# ---------------------------------------------------------

st.subheader("ROE & ROCE Trend")


if not ratios.empty:

    ratio_chart = ratios.tail(10).copy()

    fig_returns = go.Figure()


    fig_returns.add_trace(
        go.Scatter(
            x=ratio_chart["numeric_year"],
            y=ratio_chart["return_on_equity_pct"],
            mode="lines+markers",
            name="ROE",
            yaxis="y1",
        )
    )


    # Current database stores company-level ROCE rather
    # than yearly ROCE. Show it as a reference line.

    if pd.notna(company["roce_percentage"]):

        fig_returns.add_trace(
            go.Scatter(
                x=ratio_chart["numeric_year"],
                y=[
                    company["roce_percentage"]
                ] * len(ratio_chart),
                mode="lines",
                name="ROCE",
                yaxis="y2",
            )
        )


    fig_returns.update_layout(

        xaxis=dict(
            title="Year"
        ),

        yaxis=dict(
            title="ROE (%)",
        ),

        yaxis2=dict(
            title="ROCE (%)",
            overlaying="y",
            side="right",
        ),

        legend=dict(
            orientation="h"
        ),
    )


    st.plotly_chart(
        fig_returns,
        use_container_width=True,
    )

else:

    st.info(
        "ROE/ROCE history is unavailable."
    )


# ---------------------------------------------------------
# Pros & Cons
# ---------------------------------------------------------

st.divider()

st.subheader("Pros & Cons")

pros_col, cons_col = st.columns(2)


with pros_col:

    st.markdown("### Pros")

    pros = company["pros"]

    if pd.notna(pros) and str(pros).strip():

        for item in str(pros).split("\n"):

            item = item.strip()

            if item:
                st.success(f"✓ {item}")

    else:
        st.info("No pros available.")


with cons_col:

    st.markdown("### Cons")

    cons = company["cons"]

    if pd.notna(cons) and str(cons).strip():

        for item in str(cons).split("\n"):

            item = item.strip()

            if item:
                st.error(f"✗ {item}")

    else:
        st.info("No cons available.")