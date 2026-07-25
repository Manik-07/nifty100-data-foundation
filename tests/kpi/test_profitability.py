import pytest

from src.analytics.ratios import RatioCalculator


# -------------------------------------------------------
# Net Profit Margin Tests
# -------------------------------------------------------

def test_net_profit_margin_normal():
    result = RatioCalculator.net_profit_margin(100, 1000)
    assert result == 10.0


def test_net_profit_margin_zero_sales():
    result = RatioCalculator.net_profit_margin(100, 0)
    assert result is None


# -------------------------------------------------------
# Operating Profit Margin Tests
# -------------------------------------------------------

def test_operating_profit_margin_normal():
    result = RatioCalculator.operating_profit_margin(250, 1000)
    assert result == 25.0


def test_compare_opm_match():
    result = RatioCalculator.compare_opm(
        calculated_opm=25.0,
        source_opm=25.5
    )

    assert result["match"] is True
    assert result["difference"] == 0.5


def test_compare_opm_mismatch():
    result = RatioCalculator.compare_opm(
        calculated_opm=20.0,
        source_opm=23.5
    )

    assert result["match"] is False
    assert result["difference"] == 3.5


# -------------------------------------------------------
# ROE Tests
# -------------------------------------------------------

def test_return_on_equity_normal():
    result = RatioCalculator.return_on_equity(
        net_profit=200,
        equity_capital=500,
        reserves=500
    )

    assert result == 20.0


def test_return_on_equity_negative_equity():
    result = RatioCalculator.return_on_equity(
        net_profit=200,
        equity_capital=-500,
        reserves=200
    )

    assert result is None


# -------------------------------------------------------
# ROCE Test
# -------------------------------------------------------

def test_return_on_capital_employed():
    result = RatioCalculator.return_on_capital_employed(
        ebit=300,
        equity_capital=500,
        reserves=500,
        borrowings=500
    )

    assert result == 20.0


# -------------------------------------------------------
# ROA Tests
# -------------------------------------------------------

def test_return_on_assets_normal():
    result = RatioCalculator.return_on_assets(
        net_profit=100,
        total_assets=2000
    )

    assert result == 5.0


def test_return_on_assets_zero_assets():
    result = RatioCalculator.return_on_assets(
        net_profit=100,
        total_assets=0
    )

    assert result is None