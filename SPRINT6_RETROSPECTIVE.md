# Sprint 6 Retrospective

## Sprint Overview

**Sprint:** Sprint 6
**Focus:** Analytics, Clustering, FastAPI and Dashboard Integration

### Sprint Goal

The objective of Sprint 6 was to extend the Nifty 100 Data Foundation with advanced analytics, clustering analysis, a FastAPI backend, and integration/verification of the Streamlit analytics dashboard.

---

## 1. What Went Well

### Advanced Analytics

* Implemented cash flow KPI analysis.
* Implemented capital allocation analytics.
* Implemented clustering functionality.
* Implemented cluster analysis and company profiling.
* Generated clustering-related analytical outputs.
* Added KPI correlation and outlier analysis outputs.

**Analytics modules include:**

* src/analytics/cashflow_kpis.py
* src/analytics/capital_allocation_report.py
* src/analytics/clustering.py
* src/analytics/cluster_analysis.py
* src/analytics/valuation.py

---

### FastAPI Backend

Successfully implemented the FastAPI backend under:

* src/api/main.py
* src/api/routers/companies.py
* src/api/routers/screener.py
* src/api/routers/sectors.py
* src/api/routers/peers.py
* src/api/routers/valuation.py
* src/api/routers/portfolio.py
* src/api/routers/health.py
* src/api/routers/documents.py

The API exposes the following functional areas:

* Company information
* Profit and loss
* Balance sheet
* Cash flow
* Financial ratios
* Peer comparison
* Company tearsheets
* Company documents
* Stock screener
* Sector analysis
* Peer groups
* Market capitalization
* Portfolio statistics
* Health monitoring

The OpenAPI specification was verified successfully.

There are **17 OpenAPI paths in total**, including the root endpoint, with **16 API endpoints under /api/v1**.

---

### Screener API

The screener endpoint was successfully verified.

Example validations included:

* Complete dataset returned **92 companies**.
* min_roe=20 returned **34 companies**.
* Information Technology sector filtering returned **5 companies**.

The screener successfully supports filtering and returns structured financial metrics.

---

### Company API

Company endpoints were successfully tested using TCS.

Verified functionality included:

* Profit and Loss history
* Balance Sheet history
* Cash Flow history
* Financial ratios
* Peer comparison
* Other company-level endpoints

Example:

/api/v1/companies/TCS/pl

successfully returned historical company data.

---

### Peer Comparison API

Peer comparison was successfully verified using TCS.

The API returned:

* Company information
* Peer group
* Benchmark company
* Radar metrics
* Peer-group averages
* Benchmark values

The Streamlit Peer Comparison screen was also successfully verified.

---

### Streamlit Dashboard

All eight dashboard modules were manually verified successfully:

1. Home
2. Company Profile
3. Stock Screener
4. Peer Comparison
5. Trend Analysis
6. Sector Analysis
7. Capital Allocation
8. Annual Reports

Each dashboard module loaded successfully and its major functionality was verified.

---

### Testing

The complete automated test suite was executed successfully.

Final result:

**80 tests passed**

No test failures remained after resolving the CashFlowKPIs import/test issue.

---

## 2. Challenges Faced

### API Route Verification

Initial route inspection showed only the root route because FastAPI stores included routers internally.

The OpenAPI specification was therefore used to verify the final registered paths.

This confirmed that the API routes were correctly registered.

---

### Cash Flow KPI Test Failure

The initial test collection failed because:

CashFlowKPIs

was not available from:

src.analytics.cashflow_kpis

The implementation was corrected and the dedicated cash-flow test suite subsequently passed:

**11 passed**

The complete test suite then passed:

**80 passed**

---

### Generated Output Management

Several analytics and report files were generated during Sprint 6.

These included:

* cluster_labels.csv
* cluster_profiles.csv
* kpi_correlation.csv
* outlier_report.csv
* portfolio_stats.csv
* correlation_heatmap.png
* elbow_plot.png

Generated analytics outputs were added to .gitignore so that generated files do not unnecessarily appear as untracked Git changes.

---

## 3. What Could Be Improved

* Add more automated API endpoint tests.
* Add automated integration tests between the API and dashboard.
* Add stronger validation for clustering results.
* Add API response schema validation.
* Add pagination for endpoints that may return large datasets.
* Improve API error handling and validation messages.
* Add automated dashboard testing.
* Reduce unnecessary large terminal outputs during development.
* Add automated documentation for API endpoints.
* Improve consistency of financial metric naming across analytics and API layers.

---

## 4. Lessons Learned

* FastAPI provides a clean separation between API routing and analytics logic.
* OpenAPI is useful for verifying the final registered API surface.
* Automated tests are essential before declaring a sprint complete.
* Generated analytical files should be separated from source-controlled code.
* Dashboard verification should be performed after backend changes.
* Large terminal outputs make debugging harder, so focused validation commands are preferable.
* Modular analytics components make the project easier to test and extend.
* API and dashboard layers should be validated independently as well as together.

---

## 5. Sprint 6 Definition of Done

| Criteria | Status |
|---|---|
| Advanced analytics implemented | PASS |
| Clustering implemented | PASS |
| Cluster analysis implemented | PASS |
| Cash Flow KPI tests passing | PASS |
| FastAPI backend implemented | PASS |
| Company API verified | PASS |
| Screener API verified | PASS |
| Sector API verified | PASS |
| Peer API verified | PASS |
| Valuation API verified | PASS |
| Portfolio API verified | PASS |
| Health API verified | PASS |
| Streamlit dashboard integrated | PASS |
| All 8 dashboard modules verified | PASS |
| Full automated test suite passing | PASS |
| 80 tests passing | PASS |
| Generated outputs ignored by Git | PASS |
| Git working tree clean | PASS |

---

## 6. Sprint Conclusion

Sprint 6 successfully extended the Nifty 100 Data Foundation from a financial analytics and reporting system into a broader analytics platform with advanced analytics, clustering, a FastAPI backend, and a verified Streamlit dashboard.

The sprint successfully delivered:

* Advanced financial analytics
* Clustering and company profiling
* FastAPI services
* Screener functionality
* Company-level APIs
* Peer comparison APIs
* Sector APIs
* Portfolio statistics
* Dashboard integration
* Full automated test coverage for the current test suite

The final automated test result was:

**80 passed**

The working tree was verified clean and synchronized with the remote repository.

Sprint 6 is therefore considered successfully completed.
