# Sprint 4 Retrospective

## Sprint Overview

**Sprint:** Sprint 4  
**Days:** Day 22–28  
**Epics:** Epic 05 & 06 — Streamlit Dashboard + Valuation

The goal of Sprint 4 was to build a complete interactive Streamlit dashboard for Nifty 100 financial analytics and implement a valuation module for all 92 companies.

---

## Completed Deliverables

The following deliverables were completed during Sprint 4:

- Streamlit multi-page dashboard
- 8 analytics screens
- Cached SQLite data-loading utilities
- Interactive stock screener
- Peer comparison analytics
- Trend analysis
- Sector analysis
- Capital allocation analysis
- Annual report browser
- Valuation module
- valuation_summary.xlsx
- valuation_flags.csv
- Dashboard documentation
- Integration and performance testing

---

## UX Decisions

Several UX decisions were made to keep the dashboard simple and usable.

### Wide Dashboard Layout

The Streamlit application uses a wide layout so that financial tables, charts, KPI cards, and comparison views have sufficient horizontal space.

### Shared Navigation

All eight analytics screens are available through Streamlit's page navigation, allowing users to move quickly between company-level and market-level analysis.

### Interactive Company Selection

Company and ticker selectors are used across screens such as Company Profile, Trend Analysis, and Annual Reports.

### KPI Cards

Important financial metrics are displayed as KPI cards to make key information immediately visible.

### Interactive Plotly Charts

Plotly was used for interactive visualisations including:

- Donut charts
- Line charts
- Radar charts
- Bubble charts
- Treemaps
- Bar charts

### Missing Data Handling

Where data is unavailable, the dashboard avoids crashing and provides user-friendly messages or N/A values.

---

## Data Edge Cases Discovered

Several data-related edge cases were identified during implementation and QA.

### Duplicate Company Record

ADANIPORTS appeared twice in the Sector Analysis query output.

The sector loader was updated to guarantee one row per company using company_id.

Final validation:

- 92 rows
- 92 unique companies

### Different Financial Year Endings

Companies use different reporting periods such as:

- Mar 2024
- Dec 2023
- Sep 2024

Trend calculations therefore extract the four-digit year rather than assuming all companies follow the same financial year ending.

### TTM Records

Some financial tables contain TTM records.

TTM was excluded from historical annual-period charts where a valid annual year was required.

### Partial Historical Data

Some companies have fewer than ten years of historical data.

Examples identified during QA included:

- JIOFIN
- LICI
- ATGL
- ADANIGREEN

The Trend Analysis screen uses all available annual periods and displays a data-availability message instead of failing.

### Missing Cash Flow Data

ATGL was identified as having unavailable cash-flow information for the Capital Allocation analysis.

Companies without sufficient cash-flow data are classified separately as Data Unavailable rather than being incorrectly assigned to one of the eight capital-allocation patterns.

---

## Capital Allocation Design

Eight capital-allocation patterns were derived using the sign combinations of:

- Operating Cash Flow
- Investing Cash Flow
- Financing Cash Flow

The eight patterns are:

1. Self-Funded Compounder
2. Expansion with External Funding
3. Cash Generator / Asset Seller
4. Cash Accumulator
5. Externally Funded Expansion
6. Restructuring / Fund Raising
7. Asset Sale / Debt Repayment
8. Cash Burn / High Investment

This classification allows companies to be compared according to their cash-flow behaviour.

---

## Valuation Module Findings

The valuation module processed all 92 companies successfully.

Final classification:

- Caution: 14 companies
- Discount: 30 companies
- Fair: 48 companies

Total:

**92 companies**

The module generates:

- output/valuation_summary.xlsx
- output/valuation_flags.csv

FCF Yield is calculated as:

FCF Yield = Free Cash Flow / Market Capitalisation × 100

Valuation flags compare company P/E against the latest sector median P/E.

---

## QA Findings

Integration testing included companies across:

- Information Technology
- Financials
- Consumer Staples
- Energy
- Healthcare

Testing covered:

- Normal company records
- Partial historical data
- Missing cash-flow data
- Extreme screener filters
- Zero-result screener conditions
- CSV export
- Chart sizing
- Missing-value handling
- Valuation output validation

No critical dashboard crashes remained after QA.

---

## Performance Findings

Company Profile data-loading performance was tested using multiple companies including:

- TCS
- HDFCBANK
- ITC
- RELIANCE
- SUNPHARMA

All tested company profiles loaded in under the required 3-second threshold.

Database queries use Streamlit caching with:

@st.cache_data(ttl=600)

This reduces repeated database reads and improves dashboard responsiveness.

---

## What Went Well

- All eight Streamlit screens were implemented successfully.
- Database loaders were reusable across dashboard pages.
- Plotly provided responsive interactive visualisations.
- Partial and missing data could be handled without application crashes.
- Screener CSV export worked correctly.
- Valuation outputs successfully covered all 92 companies.
- Profile performance remained well below the required limit.

---

## Challenges

- Handling different company financial-year endings.
- Removing duplicate company records from joined datasets.
- Handling TTM records separately from annual data.
- Supporting companies with incomplete historical records.
- Handling missing cash-flow information.
- Managing PowerShell quoting while testing Python and SQLite commands.
- Ensuring joins across multiple financial tables did not duplicate companies.

---

## Improvements for Future Sprints

Potential improvements include:

- Add automated dashboard tests.
- Add strict cached HTTP validation for annual-report links.
- Improve chart scaling when metrics with very different magnitudes are compared.
- Add additional valuation visualisations.
- Add richer company search/autocomplete.
- Add more automated data-quality validation.
- Add dashboard deployment support.

---

## Sprint Outcome

Sprint 4 successfully delivered the Streamlit analytics dashboard and valuation module.

All eight dashboard screens are operational, valuation outputs contain all 92 companies, CSV export works, partial-data cases are handled, and tested Company Profile queries meet the performance requirement.

**Sprint 4 Status: Complete**