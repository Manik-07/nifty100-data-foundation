import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard.utils.db import get_sector_analysis


# ---------------------------------------------------------
# Page Header
# ---------------------------------------------------------

st.title("🏭 Sector Analysis")

st.caption(
    "Compare companies within a sector using revenue, "
    "profitability, market capitalisation and valuation metrics."
)


# ---------------------------------------------------------
# Load Data
# ---------------------------------------------------------

df = get_sector_analysis()

if df.empty:
    st.warning("No sector data is available.")
    st.stop()


# ---------------------------------------------------------
# Numeric Conversion
# ---------------------------------------------------------

numeric_columns = [
    "revenue",
    "roe",
    "opm",
    "npm",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "market_cap_crore",
    "pe_ratio",
    "pb_ratio",
    "dividend_yield_pct",
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce",
    )


# ---------------------------------------------------------
# Sector Selection
# ---------------------------------------------------------

sectors = sorted(
    df["broad_sector"]
    .dropna()
    .unique()
    .tolist()
)

selected_sector = st.selectbox(
    "Select Sector",
    sectors,
)


sector_df = df[
    df["broad_sector"] == selected_sector
].copy()


if sector_df.empty:
    st.warning(
        "No companies are available for the selected sector."
    )
    st.stop()


# ---------------------------------------------------------
# Summary KPIs
# ---------------------------------------------------------

st.subheader(selected_sector)

col1, col2, col3, col4 = st.columns(4)


with col1:
    st.metric(
        "Companies",
        len(sector_df),
    )


with col2:
    median_revenue = sector_df["revenue"].median()

    st.metric(
        "Median Revenue",
        (
            f"₹{median_revenue:,.0f} Cr"
            if pd.notna(median_revenue)
            else "N/A"
        ),
    )


with col3:
    median_roe = sector_df["roe"].median()

    st.metric(
        "Median ROE",
        (
            f"{median_roe:.2f}%"
            if pd.notna(median_roe)
            else "N/A"
        ),
    )


with col4:
    total_market_cap = sector_df[
        "market_cap_crore"
    ].sum(min_count=1)

    st.metric(
        "Total Market Cap",
        (
            f"₹{total_market_cap:,.0f} Cr"
            if pd.notna(total_market_cap)
            else "N/A"
        ),
    )


st.divider()


# ---------------------------------------------------------
# Bubble Chart
# ---------------------------------------------------------

st.subheader(
    "Revenue vs ROE"
)


bubble_df = sector_df.dropna(
    subset=[
        "revenue",
        "roe",
        "market_cap_crore",
    ]
).copy()


# Plotly bubble sizes must be positive
bubble_df = bubble_df[
    bubble_df["market_cap_crore"] > 0
]


if bubble_df.empty:

    st.info(
        "Insufficient Revenue, ROE or Market Cap data "
        "to generate the bubble chart."
    )

else:

    fig = px.scatter(
        bubble_df,
        x="revenue",
        y="roe",
        size="market_cap_crore",
        color="sub_sector",
        hover_name="company_name",

        hover_data={
            "company_id": True,
            "revenue": ":,.0f",
            "roe": ":.2f",
            "market_cap_crore": ":,.0f",
            "sub_sector": True,
        },

        labels={
            "revenue": "Revenue (₹ Cr)",
            "roe": "ROE (%)",
            "market_cap_crore": "Market Cap (₹ Cr)",
            "sub_sector": "Sub-Sector",
        },

        size_max=65,
    )


    fig.update_layout(
        height=600,
        legend_title="Sub-Sector",
        margin=dict(
            l=40,
            r=40,
            t=40,
            b=40,
        ),
    )


    st.plotly_chart(
        fig,
        use_container_width=True,
    )


st.caption(
    "Bubble size represents market capitalisation. "
    "Bubble colour represents the company's sub-sector."
)


# ---------------------------------------------------------
# Sector Median KPI Chart
# ---------------------------------------------------------

st.divider()

st.subheader(
    "Sector Median KPIs"
)


median_metrics = {
    "ROE %": sector_df["roe"].median(),
    "OPM %": sector_df["opm"].median(),
    "Net Margin %": sector_df["npm"].median(),
    "Revenue CAGR %": sector_df[
        "revenue_cagr_5yr"
    ].median(),
    "PAT CAGR %": sector_df[
        "pat_cagr_5yr"
    ].median(),
    "D/E": sector_df[
        "debt_to_equity"
    ].median(),
    "P/E": sector_df[
        "pe_ratio"
    ].median(),
    "Dividend Yield %": sector_df[
        "dividend_yield_pct"
    ].median(),
}


median_df = pd.DataFrame(
    {
        "Metric": median_metrics.keys(),
        "Median": median_metrics.values(),
    }
)


median_df["Median"] = pd.to_numeric(
    median_df["Median"],
    errors="coerce",
)


median_df = median_df.dropna(
    subset=["Median"]
)


if median_df.empty:

    st.info(
        "No median KPI data is available "
        "for this sector."
    )

else:

    median_fig = px.bar(
        median_df,
        x="Metric",
        y="Median",
        text_auto=".2f",
        labels={
            "Median": "Sector Median",
        },
    )


    median_fig.update_layout(
        height=450,
        xaxis_title="",
        yaxis_title="Median Value",
        showlegend=False,
        margin=dict(
            l=40,
            r=40,
            t=30,
            b=40,
        ),
    )


    st.plotly_chart(
        median_fig,
        use_container_width=True,
    )


# ---------------------------------------------------------
# Company Table
# ---------------------------------------------------------

st.divider()

st.subheader(
    f"Companies in {selected_sector}"
)


table_df = sector_df[
    [
        "company_id",
        "company_name",
        "sub_sector",
        "revenue",
        "roe",
        "opm",
        "debt_to_equity",
        "market_cap_crore",
        "pe_ratio",
    ]
].copy()


table_df = table_df.rename(
    columns={
        "company_id": "Ticker",
        "company_name": "Company",
        "sub_sector": "Sub-Sector",
        "revenue": "Revenue ₹ Cr",
        "roe": "ROE %",
        "opm": "OPM %",
        "debt_to_equity": "D/E",
        "market_cap_crore": "Market Cap ₹ Cr",
        "pe_ratio": "P/E",
    }
)


st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
)