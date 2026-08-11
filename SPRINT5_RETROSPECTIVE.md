# Sprint 5 Retrospective

## Sprint Overview

**Sprint:** Sprint 5
**Days:** Day 29–35
**Epics:** Epics 07, 08 & 09 — Cash Flow Intelligence, Reports & NLP
**Target Story Points:** 70 SP

### Sprint Goal

The objective of Sprint 5 was to complete the NLP-based pros and cons generation, implement Cash Flow Intelligence, generate company and sector reports, and produce the final portfolio summary PDF for all 92 companies.

---

## 1. What Went Well

### NLP Module

* Successfully implemented the analysis text parser for extracting structured CAGR and financial metric information.
* Implemented the automated Pros/Cons Generator with rule-based financial signals.
* Generated pros and cons with confidence scores for all **92 companies**.
* Verified that every company has at least **one PRO and one CON**.
* Final output contains **511 generated signals**.

**Output:**

* `output/analysis_parsed.csv`
* `output/parse_failures.csv`
* `output/pros_cons_generated.csv`

---

### Cash Flow Intelligence

* Successfully implemented CFO quality analysis.
* Classified companies into:

  * High Quality
  * Moderate
  * Accrual Risk
  * Insufficient Data
* Implemented CapEx intensity classification:

  * Asset Light
  * Moderate
  * Capital Intensive
  * Insufficient Data
* Implemented distress signal detection.
* Implemented deleveraging detection.
* Integrated capital allocation patterns into the cash flow intelligence output.

**Output:**

* `output/cashflow_intelligence.xlsx`
* `output/distress_alerts.csv`

The final Cash Flow Intelligence workbook contains **92 companies**.

---

### Capital Allocation Analysis

* Verified capital allocation data for all **92 companies**.
* Generated the latest-year capital allocation distribution.
* Identified year-over-year capital allocation pattern changes.
* Generated **417 pattern changes across 88 companies**.

Latest-year distribution:

| Pattern               | Companies |
| --------------------- | --------: |
| Reinvestor            |        56 |
| Mixed                 |        13 |
| Growth Funded by Debt |        12 |
| Liquidating Assets    |         7 |
| Unknown               |         2 |
| Distress Signal       |         1 |
| Pre-Revenue           |         1 |

**Output:**

* `output/capital_allocation.csv`
* `output/capital_allocation_distribution.csv`
* `output/pattern_changes.csv`

---

### Company Tearsheet Reports

* Implemented a two-page ReportLab-based financial tearsheet.
* Included company KPIs, financial trends, balance sheet information, cash flow analysis, pros and cons, and capital allocation.
* Successfully tested the tearsheet generation process.
* Batch generation produced **92 PDF files**.
* Generated files were checked for file size and successful creation.
* No generation failures occurred during the final batch run.

The three companies with insufficient historical data were logged separately:

* ATGL
* JIOFIN
* SBIN

**Output:**

* `reports/tearsheets/`
* `output/skipped_tearsheets.csv`

---

### Sector Reports

* Implemented sector-level PDF report generation.
* Successfully generated reports for all available sectors in the database.
* Generated **10 sector PDFs** based on the 10 distinct sectors present in the dataset.

**Output:**

* `reports/sector/`

---

### Portfolio Summary

* Successfully generated the portfolio summary PDF for all **92 companies**.
* The final PDF was successfully created with a size of approximately **191.7 KB**.
* Companies with insufficient ratio data were identified:

  * ATGL
  * SBIN

**Output:**

* `reports/portfolio/portfolio_summary.pdf`

---

## 2. Challenges Faced

### Missing Historical Data

Some companies did not have sufficient historical financial data.

* ATGL had no usable historical cash flow/ratio data for some analyses.
* SBIN had insufficient ratio data.
* JIOFIN had only two years of available data for the tearsheet requirement.

These companies were handled through explicit missing-data checks and logging rather than allowing the reporting pipeline to fail.

### PDF Generation Issues

During development, the tearsheet generator encountered issues including:

* Missing `reportlab` dependency.
* Missing `PageBreak` import.
* Incorrect handling of the company ID list in the batch-generation logic.

These issues were identified through terminal testing and corrected before the final generation.

### Data Quality Differences

The source financial datasets contained different numbers of records across companies and financial periods. Therefore, the reporting modules required validation for missing values and insufficient historical periods.

---

## 3. What Could Be Improved

* Improve handling of companies with limited historical financial data.
* Add more automated PDF visual validation to detect text overflow and blank pages.
* Add automated page-count validation for generated PDFs.
* Improve the fallback logic for missing financial metrics.
* Add stronger automated tests for all Sprint 5 reporting modules.
* Improve consistency of financial-period normalization across datasets.
* Add automated validation that every expected company and sector has a corresponding report.

---

## 4. Lessons Learned

* Financial datasets require extensive validation before analytics are performed.
* Missing data should be handled explicitly rather than causing pipeline failures.
* Rule-based NLP can generate explainable financial insights when the underlying financial signals are clearly defined.
* Automated report generation requires both data validation and document-layout validation.
* Modularizing analytics, NLP, and reporting components makes debugging and batch processing easier.
* Terminal-based validation commands are useful for quickly confirming row counts, company coverage, output files, and generated report sizes.

---

## 5. Sprint 5 Definition of Done

| Criteria                                     | Status |
| -------------------------------------------- | ------ |
| Pros and cons generated for all 92 companies | PASS   |
| Every company has at least 1 PRO             | PASS   |
| Every company has at least 1 CON             | PASS   |
| Cash Flow Intelligence contains 92 companies | PASS   |
| Capital allocation verified for 92 companies | PASS   |
| Company tearsheets generated                 | PASS   |
| 92 tearsheet PDFs present                    | PASS   |
| Companies with insufficient data logged      | PASS   |
| Sector reports generated                     | PASS   |
| Portfolio summary PDF generated              | PASS   |

---

## 6. Sprint Conclusion

Sprint 5 successfully delivered the major NLP, Cash Flow Intelligence, and reporting components of the Nifty 100 Data Foundation project.

The sprint produced automated financial insights for all 92 companies, cash flow classifications, capital allocation analysis, company-level tearsheets, sector reports, and a portfolio summary report.

The major objective of Sprint 5 was achieved, with remaining limitations primarily related to source-data availability for a small number of companies.
