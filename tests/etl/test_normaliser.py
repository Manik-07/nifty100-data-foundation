from src.etl.normaliser import normalize_year, normalize_ticker


# -------- normalize_year --------

def test_year_fy23():
    assert normalize_year("FY23") == 2023


def test_year_fy24():
    assert normalize_year("FY24") == 2024


def test_year_2021():
    assert normalize_year("2021") == 2021


def test_year_none():
    assert normalize_year(None) is None


def test_year_empty():
    assert normalize_year("") is None


# -------- normalize_ticker --------

def test_ticker_spaces():
    assert normalize_ticker(" reliance ") == "RELIANCE"


def test_ticker_lowercase():
    assert normalize_ticker("tcs") == "TCS"


def test_ticker_mixed():
    assert normalize_ticker("InFy") == "INFY"


def test_ticker_with_spaces():
    assert normalize_ticker(" t c s ") == "TCS"


def test_ticker_uppercase():
    assert normalize_ticker("SBIN") == "SBIN"