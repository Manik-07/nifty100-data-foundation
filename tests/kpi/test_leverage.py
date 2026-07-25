import pytest

from src.analytics.ratios import RatioCalculator


# -------------------------------------------------------
# Debt-to-Equity Tests
# -------------------------------------------------------

def test_debt_to_equity_normal():
    result = RatioCalculator.debt_to_equity(
        borrowings=500,
        equity_capital=500,
        reserves=500
    )

    assert result == 0.5


def test_debt_to_equity_zero_borrowings():
    result = RatioCalculator.debt_to_equity(
        borrowings=0,
        equity_capital=500,
        reserves=500
    )

    assert result == 0


def test_debt_to_equity_negative_equity():
    result = RatioCalculator.debt_to_equity(
        borrowings=500,
        equity_capital=-500,
        reserves=200
    )

    assert result is None


# -------------------------------------------------------
# High Leverage Flag Tests
# -------------------------------------------------------

def test_high_leverage_flag_true():
    result = RatioCalculator.high_leverage_flag(
        debt_to_equity=6.2,
        broad_sector="Technology"
    )

    assert result is True


def test_high_leverage_flag_financials():
    result = RatioCalculator.high_leverage_flag(
        debt_to_equity=8.0,
        broad_sector="Financials"
    )

    assert result is False


# -------------------------------------------------------
# Interest Coverage Tests
# -------------------------------------------------------

def test_interest_coverage_normal():
    result = RatioCalculator.interest_coverage(
        operating_profit=500,
        other_income=100,
        interest=100
    )

    assert result == 6.0


def test_interest_coverage_zero_interest():
    result = RatioCalculator.interest_coverage(
        operating_profit=500,
        other_income=100,
        interest=0
    )

    assert result is None


# -------------------------------------------------------
# Debt Free Label Test
# -------------------------------------------------------

def test_icr_label():
    result = RatioCalculator.icr_label(0)

    assert result == "Debt Free"


# -------------------------------------------------------
# ICR Warning Tests
# -------------------------------------------------------

def test_icr_warning_true():
    result = RatioCalculator.icr_warning(1.2)

    assert result is True


def test_icr_warning_false():
    result = RatioCalculator.icr_warning(3.5)

    assert result is False


# -------------------------------------------------------
# Net Debt Tests
# -------------------------------------------------------

def test_net_debt_positive():
    result = RatioCalculator.net_debt(
        borrowings=1000,
        investments=300
    )

    assert result == 700


def test_net_debt_negative():
    result = RatioCalculator.net_debt(
        borrowings=200,
        investments=500
    )

    assert result == -300


# -------------------------------------------------------
# Asset Turnover Tests
# -------------------------------------------------------

def test_asset_turnover_normal():
    result = RatioCalculator.asset_turnover(
        sales=4000,
        total_assets=2000
    )

    assert result == 2.0


def test_asset_turnover_zero_assets():
    result = RatioCalculator.asset_turnover(
        sales=4000,
        total_assets=0
    )

    assert result is None