import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard.utils.db import get_capital_allocation


# ---------------------------------------------------------
# Page Header
# ---------------------------------------------------------

st.title("💰 Capital Allocation Map")

st.caption(
    "Classify Nifty 100 companies by the direction of their "
    "operating, investing and financing cash flows."
)


# ---------------------------------------------------------
# Load Data
# ---------------------------------------------------------

df = get_capital_allocation()

if df.empty:
    st.warning("No capital allocation data is available.")
    st.stop()


# ---------------------------------------------------------
# Numeric Conversion
# ---------------------------------------------------------

cashflow_columns = [
    "operating_activity",
    "investing_activity",
    "financing_activity",
    "net_cash_flow",
    "market_cap_crore",
]

for column in cashflow_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce",
    )


# ---------------------------------------------------------
# Capital Allocation Classification
# ---------------------------------------------------------

def classify_pattern(row):

    cfo = row["operating_activity"]
    cfi = row["investing_activity"]
    cff = row["financing_activity"]

    # Missing cash-flow information
    if pd.isna(cfo) or pd.isna(cfi) or pd.isna(cff):
        return "Data Unavailable"

    cfo_positive = cfo >= 0
    cfi_positive = cfi >= 0
    cff_positive = cff >= 0

    if cfo_positive and not cfi_positive and not cff_positive:
        return "Self-Funded Compounder"

    elif cfo_positive and not cfi_positive and cff_positive:
        return "Expansion with External Funding"

    elif cfo_positive and cfi_positive and not cff_positive:
        return "Cash Generator / Asset Seller"

    elif cfo_positive and cfi_positive and cff_positive:
        return "Cash Accumulator"

    elif not cfo_positive and not cfi_positive and cff_positive:
        return "Externally Funded Expansion"

    elif not cfo_positive and cfi_positive and cff_positive:
        return "Restructuring / Fund Raising"

    elif not cfo_positive and cfi_positive and not cff_positive:
        return "Asset Sale / Debt Repayment"

    else:
        return "Cash Burn / High Investment"


df["capital_pattern"] = df.apply(
    classify_pattern,
    axis=1,
)


# ---------------------------------------------------------
# Eight Required Patterns
# ---------------------------------------------------------

PATTERNS = [
    "Self-Funded Compounder",
    "Expansion with External Funding",
    "Cash Generator / Asset Seller",
    "Cash Accumulator",
    "Externally Funded Expansion",
    "Restructuring / Fund Raising",
    "Asset Sale / Debt Repayment",
    "Cash Burn / High Investment",
]


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

valid_df = df[
    df["capital_pattern"].isin(PATTERNS)
].copy()

missing_df = df[
    df["capital_pattern"] == "Data Unavailable"
].copy()


col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Companies",
        len(df),
    )

with col2:
    st.metric(
        "Classified",
        len(valid_df),
    )

with col3:
    st.metric(
        "Patterns",
        8,
    )

with col4:
    st.metric(
        "Data Unavailable",
        len(missing_df),
    )


st.divider()


# ---------------------------------------------------------
# Pattern Distribution
# ---------------------------------------------------------

st.subheader("Capital Allocation Patterns")


pattern_counts = (
    valid_df["capital_pattern"]
    .value_counts()
    .reindex(PATTERNS, fill_value=0)
    .reset_index()
)

pattern_counts.columns = [
    "Pattern",
    "Companies",
]


st.dataframe(
    pattern_counts,
    use_container_width=True,
    hide_index=True,
)


# ---------------------------------------------------------
# Treemap
# ---------------------------------------------------------

st.subheader("Capital Allocation Treemap")


treemap_df = valid_df.copy()


# Market cap is the preferred treemap size.
# If unavailable/non-positive, use 1 so the company still appears.
treemap_df["treemap_size"] = (
    treemap_df["market_cap_crore"]
    .fillna(1)
    .clip(lower=1)
)


if treemap_df.empty:

    st.info(
        "Insufficient cash-flow data to generate the treemap."
    )

else:

    fig = px.treemap(
        treemap_df,

        path=[
            "capital_pattern",
            "company_name",
        ],

        values="treemap_size",

        color="capital_pattern",

        hover_data={
            "company_id": True,
            "broad_sector": True,
            "sub_sector": True,
            "year": True,
            "operating_activity": ":,.0f",
            "investing_activity": ":,.0f",
            "financing_activity": ":,.0f",
            "net_cash_flow": ":,.0f",
            "market_cap_crore": ":,.0f",
            "treemap_size": False,
        },
    )


    fig.update_layout(
        height=700,
        margin=dict(
            l=10,
            r=10,
            t=40,
            b=10,
        ),
    )


    st.plotly_chart(
        fig,
        use_container_width=True,
    )


st.caption(
    "Treemap size is based on market capitalisation where available. "
    "Companies are grouped using the signs of operating, investing "
    "and financing cash flows."
)


# ---------------------------------------------------------
# Pattern Explorer
# ---------------------------------------------------------

st.divider()

st.subheader("Explore a Capital Allocation Pattern")


selected_pattern = st.selectbox(
    "Select Pattern",
    PATTERNS,
)


selected_df = df[
    df["capital_pattern"] == selected_pattern
].copy()


st.write(
    f"**{len(selected_df)} companies** are classified as "
    f"**{selected_pattern}**."
)


if selected_df.empty:

    st.info(
        "No companies currently fall into this pattern."
    )

else:

    display_df = selected_df[
        [
            "company_id",
            "company_name",
            "broad_sector",
            "year",
            "operating_activity",
            "investing_activity",
            "financing_activity",
            "net_cash_flow",
            "market_cap_crore",
        ]
    ].copy()


    display_df = display_df.rename(
        columns={
            "company_id": "Ticker",
            "company_name": "Company",
            "broad_sector": "Sector",
            "year": "Year",
            "operating_activity": "Operating CF ₹ Cr",
            "investing_activity": "Investing CF ₹ Cr",
            "financing_activity": "Financing CF ₹ Cr",
            "net_cash_flow": "Net Cash Flow ₹ Cr",
            "market_cap_crore": "Market Cap ₹ Cr",
        }
    )


    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------
# Missing Data
# ---------------------------------------------------------

if not missing_df.empty:

    st.divider()

    with st.expander(
        f"Data Unavailable ({len(missing_df)} companies)"
    ):

        missing_display = missing_df[
            [
                "company_id",
                "company_name",
                "broad_sector",
            ]
        ].copy()


        missing_display = missing_display.rename(
            columns={
                "company_id": "Ticker",
                "company_name": "Company",
                "broad_sector": "Sector",
            }
        )


        st.dataframe(
            missing_display,
            use_container_width=True,
            hide_index=True,
        )