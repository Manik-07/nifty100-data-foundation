"""
test_validator.py

Runs Data Quality validation for Sprint 1 - Day 3
"""

from src.etl.loader import ExcelLoader
from src.etl.validator import DataValidator


# --------------------------------------------------
# Load all datasets
# --------------------------------------------------

loader = ExcelLoader()

datasets = loader.load_all()

validator = DataValidator()

# --------------------------------------------------
# Companies table
# --------------------------------------------------

companies = datasets["companies"]

# --------------------------------------------------
# DQ-01 : Primary Key
# --------------------------------------------------

validator.check_primary_key(
    companies,
    "companies",
    "id"
)

# --------------------------------------------------
# DQ-02 : Composite Key
# --------------------------------------------------

validator.check_composite_key(
    datasets["profitandloss"],
    "profitandloss",
    ["company_id", "year"]
)

validator.check_composite_key(
    datasets["balancesheet"],
    "balancesheet",
    ["company_id", "year"]
)

validator.check_composite_key(
    datasets["cashflow"],
    "cashflow",
    ["company_id", "year"]
)

validator.check_composite_key(
    datasets["financial_ratios"],
    "financial_ratios",
    ["company_id", "year"]
)

validator.check_composite_key(
    datasets["market_cap"],
    "market_cap",
    ["company_id", "year"]
)

# --------------------------------------------------
# DQ-03 : Foreign Key Integrity
# --------------------------------------------------

validator.check_foreign_key(
    datasets["profitandloss"],
    companies,
    "company_id",
    "id",
    "profitandloss"
)

validator.check_foreign_key(
    datasets["balancesheet"],
    companies,
    "company_id",
    "id",
    "balancesheet"
)

validator.check_foreign_key(
    datasets["cashflow"],
    companies,
    "company_id",
    "id",
    "cashflow"
)

validator.check_foreign_key(
    datasets["financial_ratios"],
    companies,
    "company_id",
    "id",
    "financial_ratios"
)

validator.check_foreign_key(
    datasets["market_cap"],
    companies,
    "company_id",
    "id",
    "market_cap"
)

validator.check_foreign_key(
    datasets["documents"],
    companies,
    "company_id",
    "id",
    "documents"
)

validator.check_foreign_key(
    datasets["analysis"],
    companies,
    "company_id",
    "id",
    "analysis"
)

validator.check_foreign_key(
    datasets["prosandcons"],
    companies,
    "company_id",
    "id",
    "prosandcons"
)

validator.check_foreign_key(
    datasets["sectors"],
    companies,
    "company_id",
    "id",
    "sectors"
)

validator.check_foreign_key(
    datasets["stock_prices"],
    companies,
    "company_id",
    "id",
    "stock_prices"
)

validator.check_foreign_key(
    datasets["peer_groups"],
    companies,
    "company_id",
    "id",
    "peer_groups"
)

# --------------------------------------------------
# DQ-04 : Balance Sheet Validation
# --------------------------------------------------

validator.check_balance_sheet(
    datasets["balancesheet"]
)

# --------------------------------------------------
# DQ-05 : Operating Profit Validation
# --------------------------------------------------

validator.check_operating_profit(
    datasets["profitandloss"]
)

# --------------------------------------------------
# DQ-06 : Positive Sales Validation
# --------------------------------------------------

validator.check_positive_sales(
    datasets["profitandloss"]
)

# --------------------------------------------------
# Save Validation Report
# --------------------------------------------------

validator.save_failures()

print("\n==========================================")
print("Data Validation Completed Successfully")
print("==========================================")
