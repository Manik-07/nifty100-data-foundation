import pandas as pd
import streamlit as st

from src.dashboard.utils.db import get_screener_data


# ---------------------------------------------------------
# Page Header
# ---------------------------------------------------------

st.title("🔎 Stock Screener")
st.caption(
    "Filter Nifty 100 companies using profitability, growth, "
    "valuation, leverage and cash-flow metrics."
)


# ---------------------------------------------------------
# Load Data
# ---------------------------------------------------------

df = get_screener_data()

if df.empty:
    st.warning("No screener data is available.")
    st.stop()


# Convert metric columns to numeric safely
metric_columns = [
    "composite_quality_score",
    "roe",
    "debt_to_equity",
    "fcf",
    "revenue_cagr",
    "pat_cagr",
    "opm",
    "icr",
    "pe",
    "pb",
    "dividend_yield",
]

for column in metric_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")


# ---------------------------------------------------------
# Preset Definitions
# ---------------------------------------------------------

PRESETS = {
    "Quality": {
        "roe": 15.0,
        "de": 1.0,
        "fcf": 0.0,
        "revenue_cagr": 5.0,
        "pat_cagr": 5.0,
        "opm": 10.0,
        "pe": 100.0,
        "pb": 20.0,
        "dividend": 0.0,
        "icr": 3.0,
    },

    "Value": {
        "roe": 10.0,
        "de": 2.0,
        "fcf": 0.0,
        "revenue_cagr": 0.0,
        "pat_cagr": 0.0,
        "opm": 5.0,
        "pe": 20.0,
        "pb": 3.0,
        "dividend": 0.0,
        "icr": 2.0,
    },

    "Growth": {
        "roe": 12.0,
        "de": 2.0,
        "fcf": -5000.0,
        "revenue_cagr": 12.0,
        "pat_cagr": 12.0,
        "opm": 8.0,
        "pe": 150.0,
        "pb": 30.0,
        "dividend": 0.0,
        "icr": 2.0,
    },

    "Dividend": {
        "roe": 10.0,
        "de": 2.0,
        "fcf": 0.0,
        "revenue_cagr": 0.0,
        "pat_cagr": 0.0,
        "opm": 5.0,
        "pe": 100.0,
        "pb": 20.0,
        "dividend": 2.0,
        "icr": 2.0,
    },

    "Debt-Free": {
        "roe": 0.0,
        "de": 0.10,
        "fcf": -5000.0,
        "revenue_cagr": -20.0,
        "pat_cagr": -20.0,
        "opm": 0.0,
        "pe": 200.0,
        "pb": 50.0,
        "dividend": 0.0,
        "icr": 0.0,
    },

    "Turnaround": {
        "roe": 0.0,
        "de": 3.0,
        "fcf": -5000.0,
        "revenue_cagr": 0.0,
        "pat_cagr": 10.0,
        "opm": 0.0,
        "pe": 200.0,
        "pb": 50.0,
        "dividend": 0.0,
        "icr": 1.0,
    },
}


# ---------------------------------------------------------
# Session State Defaults
# ---------------------------------------------------------

defaults = {
    "roe_filter": 0.0,
    "de_filter": 5.0,
    "fcf_filter": -5000.0,
    "revenue_filter": -20.0,
    "pat_filter": -20.0,
    "opm_filter": 0.0,
    "pe_filter": 200.0,
    "pb_filter": 50.0,
    "dividend_filter": 0.0,
    "icr_filter": 0.0,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ---------------------------------------------------------
# Preset Function
# ---------------------------------------------------------

def apply_preset(name):
    preset = PRESETS[name]

    st.session_state.roe_filter = preset["roe"]
    st.session_state.de_filter = preset["de"]
    st.session_state.fcf_filter = preset["fcf"]
    st.session_state.revenue_filter = preset["revenue_cagr"]
    st.session_state.pat_filter = preset["pat_cagr"]
    st.session_state.opm_filter = preset["opm"]
    st.session_state.pe_filter = preset["pe"]
    st.session_state.pb_filter = preset["pb"]
    st.session_state.dividend_filter = preset["dividend"]
    st.session_state.icr_filter = preset["icr"]


# ---------------------------------------------------------
# Preset Buttons
# ---------------------------------------------------------

st.subheader("Quick Presets")

preset_cols = st.columns(6)

preset_names = [
    "Quality",
    "Value",
    "Growth",
    "Dividend",
    "Debt-Free",
    "Turnaround",
]

for col, preset_name in zip(preset_cols, preset_names):
    with col:
        st.button(
            preset_name,
            use_container_width=True,
            on_click=apply_preset,
            args=(preset_name,),
        )


# ---------------------------------------------------------
# Sidebar Filters
# ---------------------------------------------------------

st.sidebar.header("Screener Filters")

roe_min = st.sidebar.slider(
    "ROE Min (%)",
    min_value=-50.0,
    max_value=100.0,
    step=1.0,
    key="roe_filter",
)

de_max = st.sidebar.slider(
    "D/E Max",
    min_value=0.0,
    max_value=10.0,
    step=0.1,
    key="de_filter",
)

fcf_min = st.sidebar.slider(
    "FCF Min (₹ Cr)",
    min_value=-5000.0,
    max_value=50000.0,
    step=100.0,
    key="fcf_filter",
)

revenue_cagr_min = st.sidebar.slider(
    "Revenue CAGR 5Y Min (%)",
    min_value=-20.0,
    max_value=50.0,
    step=1.0,
    key="revenue_filter",
)

pat_cagr_min = st.sidebar.slider(
    "PAT CAGR 5Y Min (%)",
    min_value=-20.0,
    max_value=100.0,
    step=1.0,
    key="pat_filter",
)

opm_min = st.sidebar.slider(
    "OPM Min (%)",
    min_value=-20.0,
    max_value=100.0,
    step=1.0,
    key="opm_filter",
)

pe_max = st.sidebar.slider(
    "P/E Max",
    min_value=0.0,
    max_value=200.0,
    step=1.0,
    key="pe_filter",
)

pb_max = st.sidebar.slider(
    "P/B Max",
    min_value=0.0,
    max_value=50.0,
    step=0.5,
    key="pb_filter",
)

dividend_min = st.sidebar.slider(
    "Dividend Yield Min (%)",
    min_value=0.0,
    max_value=10.0,
    step=0.1,
    key="dividend_filter",
)

icr_min = st.sidebar.slider(
    "ICR Min",
    min_value=0.0,
    max_value=50.0,
    step=0.5,
    key="icr_filter",
)


# ---------------------------------------------------------
# Apply Filters
# ---------------------------------------------------------

filtered_df = df[
    (df["roe"].fillna(float("-inf")) >= roe_min)
    & (df["debt_to_equity"].fillna(float("inf")) <= de_max)
    & (df["fcf"].fillna(float("-inf")) >= fcf_min)
    & (df["revenue_cagr"].fillna(float("-inf")) >= revenue_cagr_min)
    & (df["pat_cagr"].fillna(float("-inf")) >= pat_cagr_min)
    & (df["opm"].fillna(float("-inf")) >= opm_min)
    & (df["pe"].fillna(float("inf")) <= pe_max)
    & (df["pb"].fillna(float("inf")) <= pb_max)
    & (df["dividend_yield"].fillna(float("-inf")) >= dividend_min)
    & (df["icr"].fillna(float("-inf")) >= icr_min)
].copy()


# ---------------------------------------------------------
# Result Count
# ---------------------------------------------------------

st.divider()

st.subheader("Screener Results")

st.write(
    f"**{len(filtered_df)} companies match your filters** "
    f"out of {len(df)} Nifty 100 companies."
)


# ---------------------------------------------------------
# Display Table
# ---------------------------------------------------------

display_columns = [
    "company_id",
    "company_name",
    "sector",
    "composite_quality_score",
    "roe",
    "debt_to_equity",
    "fcf",
    "revenue_cagr",
    "pat_cagr",
    "opm",
    "pe",
    "pb",
    "dividend_yield",
    "icr",
]

display_df = filtered_df[display_columns].copy()

display_df = display_df.rename(
    columns={
        "company_id": "Ticker",
        "company_name": "Company",
        "sector": "Sector",
        "composite_quality_score": "Quality Score",
        "roe": "ROE %",
        "debt_to_equity": "D/E",
        "fcf": "FCF ₹ Cr",
        "revenue_cagr": "Revenue CAGR %",
        "pat_cagr": "PAT CAGR %",
        "opm": "OPM %",
        "pe": "P/E",
        "pb": "P/B",
        "dividend_yield": "Dividend Yield %",
        "icr": "ICR",
    }
)

if display_df.empty:
    st.warning(
        "No companies match the selected filters. "
        "Try relaxing one or more criteria."
    )

else:
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------
# CSV Download
# ---------------------------------------------------------

csv_data = display_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇️ Download Results as CSV",
    data=csv_data,
    file_name="nifty100_screener_results.csv",
    mime="text/csv",
    disabled=display_df.empty,
)