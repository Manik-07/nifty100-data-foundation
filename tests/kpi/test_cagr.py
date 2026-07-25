import pytest

from src.analytics.cagr import CAGRCalculator


# -------------------------------------------------------
# Normal CAGR
# -------------------------------------------------------

def test_normal_cagr():

    result = CAGRCalculator.calculate_cagr(
        start_value=100,
        end_value=200,
        years=5
    )

    assert result["flag"] is None
    assert round(result["value"], 2) == 14.87


# -------------------------------------------------------
# Zero Base
# -------------------------------------------------------

def test_zero_base():

    result = CAGRCalculator.calculate_cagr(
        start_value=0,
        end_value=100,
        years=5
    )

    assert result["flag"] == "ZERO_BASE"
    assert result["value"] is None


# -------------------------------------------------------
# Turnaround
# -------------------------------------------------------

def test_turnaround():

    result = CAGRCalculator.calculate_cagr(
        start_value=-100,
        end_value=200,
        years=5
    )

    assert result["flag"] == "TURNAROUND"


# -------------------------------------------------------
# Decline to Loss
# -------------------------------------------------------

def test_decline_to_loss():

    result = CAGRCalculator.calculate_cagr(
        start_value=200,
        end_value=-50,
        years=5
    )

    assert result["flag"] == "DECLINE_TO_LOSS"


# -------------------------------------------------------
# Both Negative
# -------------------------------------------------------

def test_both_negative():

    result = CAGRCalculator.calculate_cagr(
        start_value=-100,
        end_value=-50,
        years=5
    )

    assert result["flag"] == "BOTH_NEGATIVE"


# -------------------------------------------------------
# Insufficient Years
# -------------------------------------------------------

def test_insufficient():

    result = CAGRCalculator.calculate_cagr(
        start_value=100,
        end_value=200,
        years=0
    )

    assert result["flag"] == "INSUFFICIENT"


# -------------------------------------------------------
# CAGR Growth
# -------------------------------------------------------

def test_positive_growth():

    result = CAGRCalculator.calculate_cagr(
        100,
        300,
        10
    )

    assert result["flag"] is None


# -------------------------------------------------------
# CAGR No Growth
# -------------------------------------------------------

def test_no_growth():

    result = CAGRCalculator.calculate_cagr(
        100,
        100,
        5
    )

    assert result["value"] == 0.0


# -------------------------------------------------------
# CAGR Decline
# -------------------------------------------------------

def test_negative_growth():

    result = CAGRCalculator.calculate_cagr(
        500,
        250,
        5
    )

    assert result["value"] < 0


# -------------------------------------------------------
# Large Growth
# -------------------------------------------------------

def test_large_growth():

    result = CAGRCalculator.calculate_cagr(
        50,
        800,
        10
    )

    assert result["flag"] is None