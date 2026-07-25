import pytest

from src.analytics.cashflow_kpis import CashFlowKPIs


def test_free_cash_flow():
    assert CashFlowKPIs.free_cash_flow(
        500,
        -200
    ) == 300


def test_cfo_quality_high():
    assert CashFlowKPIs.cfo_quality_score(
        120,
        100
    ) == "High Quality"


def test_cfo_quality_moderate():
    assert CashFlowKPIs.cfo_quality_score(
        70,
        100
    ) == "Moderate"


def test_cfo_quality_accrual():
    assert CashFlowKPIs.cfo_quality_score(
        30,
        100
    ) == "Accrual Risk"


def test_cfo_quality_zero_pat():
    assert CashFlowKPIs.cfo_quality_score(
        100,
        0
    ) is None


def test_capex_intensity():
    result = CashFlowKPIs.capex_intensity(
        -100,
        5000
    )

    assert result["label"] == "Asset Light"


def test_fcf_conversion():
    assert CashFlowKPIs.fcf_conversion(
        300,
        600
    ) == 50.0


def test_fcf_conversion_zero():
    assert CashFlowKPIs.fcf_conversion(
        300,
        0
    ) is None


def test_capital_allocation_reinvestor():
    assert CashFlowKPIs.capital_allocation_pattern(
        100,
        -50,
        -30
    ) == "Reinvestor"


def test_capital_allocation_distress():
    assert CashFlowKPIs.capital_allocation_pattern(
        -100,
        50,
        20
    ) == "Distress Signal"


def test_capital_allocation_cash_accumulator():
    assert CashFlowKPIs.capital_allocation_pattern(
        100,
        50,
        20
    ) == "Cash Accumulator"