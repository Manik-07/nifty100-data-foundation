import pandas as pd
from src.etl.loader import ExcelLoader


loader = ExcelLoader()


def test_loader_created():
    assert loader is not None


def test_load_all_returns_dict():
    datasets = loader.load_all()
    assert isinstance(datasets, dict)


def test_companies_exists():
    datasets = loader.load_all()
    assert "companies" in datasets


def test_profitandloss_exists():
    datasets = loader.load_all()
    assert "profitandloss" in datasets


def test_balancesheet_exists():
    datasets = loader.load_all()
    assert "balancesheet" in datasets


def test_cashflow_exists():
    datasets = loader.load_all()
    assert "cashflow" in datasets


def test_stock_prices_exists():
    datasets = loader.load_all()
    assert "stock_prices" in datasets


def test_companies_not_empty():
    datasets = loader.load_all()
    assert len(datasets["companies"]) > 0


def test_profitandloss_not_empty():
    datasets = loader.load_all()
    assert len(datasets["profitandloss"]) > 0


def test_loader_returns_dataframe():
    datasets = loader.load_all()
    assert isinstance(datasets["companies"], pd.DataFrame)