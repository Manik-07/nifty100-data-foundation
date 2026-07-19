from src.etl.validator import DataValidator
import pandas as pd


# --------------------------------------------------
# DQ-01 : Primary Key Tests
# --------------------------------------------------

def test_primary_key():
    df = pd.DataFrame({"id": [1, 2, 3]})

    validator = DataValidator()
    validator.check_primary_key(df, "test", "id")

    assert len(validator.failures) == 0


def test_duplicate_primary_key():
    df = pd.DataFrame({"id": [1, 2, 2]})

    validator = DataValidator()
    validator.check_primary_key(df, "test", "id")

    assert len(validator.failures) > 0


# --------------------------------------------------
# DQ-02 : Composite Key Tests
# --------------------------------------------------

def test_composite_key_valid():
    df = pd.DataFrame({
        "company_id": ["A", "B"],
        "year": ["2023", "2023"]
    })

    validator = DataValidator()
    validator.check_composite_key(df, "test", ["company_id", "year"])

    assert len(validator.failures) == 0


def test_composite_key_duplicate():
    df = pd.DataFrame({
        "company_id": ["A", "A"],
        "year": ["2023", "2023"]
    })

    validator = DataValidator()
    validator.check_composite_key(df, "test", ["company_id", "year"])

    assert len(validator.failures) > 0


# --------------------------------------------------
# DQ-03 : Foreign Key Tests
# --------------------------------------------------

def test_foreign_key_valid():
    parent = pd.DataFrame({"id": ["A", "B"]})
    child = pd.DataFrame({"company_id": ["A"]})

    validator = DataValidator()
    validator.check_foreign_key(child, parent, "company_id", "id", "test")

    assert len(validator.failures) == 0


def test_foreign_key_invalid():
    parent = pd.DataFrame({"id": ["A"]})
    child = pd.DataFrame({"company_id": ["B"]})

    validator = DataValidator()
    validator.check_foreign_key(child, parent, "company_id", "id", "test")

    assert len(validator.failures) == 1


# --------------------------------------------------
# DQ-04 : Balance Sheet Tests
# --------------------------------------------------

def test_balance_sheet():
    df = pd.DataFrame({
        "total_assets": [1000],
        "total_liabilities": [1000]
    })

    validator = DataValidator()
    validator.check_balance_sheet(df)

    assert len(validator.failures) == 0


def test_balance_sheet_mismatch():
    df = pd.DataFrame({
        "total_assets": [100],
        "total_liabilities": [80]
    })

    validator = DataValidator()
    validator.check_balance_sheet(df)

    assert len(validator.failures) == 1


# --------------------------------------------------
# DQ-05 : Operating Profit Tests
# --------------------------------------------------

def test_operating_profit():
    df = pd.DataFrame({
        "sales": [100],
        "expenses": [40],
        "operating_profit": [60]
    })

    validator = DataValidator()
    validator.check_operating_profit(df)

    assert len(validator.failures) == 0


def test_operating_profit_mismatch():
    df = pd.DataFrame({
        "sales": [100],
        "expenses": [40],
        "operating_profit": [50]
    })

    validator = DataValidator()
    validator.check_operating_profit(df)

    assert len(validator.failures) == 1


# --------------------------------------------------
# DQ-06 : Positive Sales Tests
# --------------------------------------------------

def test_positive_sales():
    df = pd.DataFrame({
        "sales": [100, 200, 300]
    })

    validator = DataValidator()
    validator.check_positive_sales(df)

    assert len(validator.failures) == 0


def test_negative_sales():
    df = pd.DataFrame({
        "sales": [100, -50, 200]
    })

    validator = DataValidator()
    validator.check_positive_sales(df)

    assert len(validator.failures) == 1


def test_positive_sales_zero():
    df = pd.DataFrame({
        "sales": [0]
    })

    validator = DataValidator()
    validator.check_positive_sales(df)

    assert len(validator.failures) == 1


def test_positive_sales_null():
    df = pd.DataFrame({
        "sales": [None]
    })

    validator = DataValidator()
    validator.check_positive_sales(df)

    assert len(validator.failures) == 0


def test_empty_dataframe():
    df = pd.DataFrame(columns=["sales"])

    validator = DataValidator()
    validator.check_positive_sales(df)

    assert len(validator.failures) == 0