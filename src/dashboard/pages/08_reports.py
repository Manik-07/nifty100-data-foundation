import re

import pandas as pd
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_annual_reports,
)


# ---------------------------------------------------------
# Page Header
# ---------------------------------------------------------

st.title("📄 Annual Reports")

st.caption(
    "Browse available company annual reports and open "
    "the original BSE PDF filing."
)


# ---------------------------------------------------------
# Load Companies
# ---------------------------------------------------------

companies = get_companies()

if companies.empty:
    st.warning("No company data is available.")
    st.stop()


# ---------------------------------------------------------
# Company Search / Selection
# ---------------------------------------------------------

companies["search_label"] = (
    companies["company_name"].astype(str)
    + " ("
    + companies["company_id"].astype(str)
    + ")"
)


company_options = companies[
    "search_label"
].tolist()


selected_label = st.selectbox(
    "Search Company / Ticker",
    company_options,
)


selected_company = companies[
    companies["search_label"] == selected_label
].iloc[0]


ticker = selected_company["company_id"]
company_name = selected_company["company_name"]


# ---------------------------------------------------------
# Company Information
# ---------------------------------------------------------

col1, col2, col3 = st.columns(3)


with col1:
    st.metric(
        "Ticker",
        ticker,
    )


with col2:
    st.metric(
        "Sector",
        (
            selected_company["broad_sector"]
            if pd.notna(
                selected_company["broad_sector"]
            )
            else "N/A"
        ),
    )


with col3:
    st.metric(
        "Sub-Sector",
        (
            selected_company["sub_sector"]
            if pd.notna(
                selected_company["sub_sector"]
            )
            else "N/A"
        ),
    )


# ---------------------------------------------------------
# Load Reports
# ---------------------------------------------------------

reports = get_annual_reports(ticker)


st.divider()

st.subheader(
    f"{company_name} — Annual Reports"
)


if reports.empty:

    st.warning(
        "No annual reports are available "
        "for this company."
    )

    st.stop()


# ---------------------------------------------------------
# URL Extraction
# ---------------------------------------------------------

def extract_url(value):
    """
    Extract URL from either:
    [https://example.com/file.pdf](https://example.com/file.pdf)
    or a plain URL.
    """

    if pd.isna(value):
        return None

    value = str(value).strip()

    # Markdown link
    match = re.search(
        r"\((https?://[^)]+)\)",
        value,
    )

    if match:
        return match.group(1).strip()

    # Plain URL
    match = re.search(
        r"https?://\S+",
        value,
    )

    if match:
        return match.group(0).strip()

    return None


reports["url"] = reports[
    "annual_report"
].apply(extract_url)


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

valid_reports = reports[
    reports["url"].notna()
].copy()


col1, col2 = st.columns(2)


with col1:
    st.metric(
        "Reports Available",
        len(valid_reports),
    )


with col2:

    if not valid_reports.empty:

        latest_year = valid_reports[
            "year"
        ].astype(str).max()

    else:
        latest_year = "N/A"

    st.metric(
        "Latest Report",
        latest_year,
    )


st.divider()


# ---------------------------------------------------------
# Annual Report List
# ---------------------------------------------------------

for _, report in reports.iterrows():

    year = str(
        report["year"]
    )

    url = report["url"]


    col1, col2, col3 = st.columns(
        [1, 4, 2]
    )


    with col1:

        st.markdown(
            f"### {year}"
        )


    with col2:

        st.write(
            f"{company_name} Annual Report"
        )


    with col3:

        if url:

            st.link_button(
                "📄 Open BSE PDF",
                url,
                use_container_width=True,
            )

        else:

            st.markdown(
                """
                <div style="
                    background-color:#ffdddd;
                    color:#b30000;
                    padding:8px;
                    border-radius:6px;
                    text-align:center;
                    font-weight:bold;
                ">
                    Report unavailable
                </div>
                """,
                unsafe_allow_html=True,
            )


    st.divider()


# ---------------------------------------------------------
# Source Information
# ---------------------------------------------------------

st.caption(
    "Annual report links are sourced from the project "
    "documents dataset and point to BSE-hosted filings."
)