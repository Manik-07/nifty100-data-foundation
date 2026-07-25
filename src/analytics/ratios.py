"""
ratios.py

Financial Ratio Engine - Sprint 2 (Day 08)

Contains profitability ratio calculations.

Author: Manik Soodan
"""

from typing import Optional


class RatioCalculator:
    """
    Collection of financial ratio calculation methods.

    All methods return:
        - float (rounded to 2 decimals)
        - None (if ratio cannot be computed)
    """

    @staticmethod
    def _safe_round(value: float) -> float:
        """Round values to 2 decimal places."""
        return round(value, 2)

    # ---------------------------------------------------------
    # 1. NET PROFIT MARGIN
    # Formula:
    # (Net Profit / Sales) * 100
    # ---------------------------------------------------------
    @staticmethod
    def net_profit_margin(
        net_profit: float,
        sales: float
    ) -> Optional[float]:

        if sales == 0:
            return None

        return RatioCalculator._safe_round(
            (net_profit / sales) * 100
        )

    # ---------------------------------------------------------
    # 2. OPERATING PROFIT MARGIN
    # Formula:
    # (Operating Profit / Sales) * 100
    # ---------------------------------------------------------
    @staticmethod
    def operating_profit_margin(
        operating_profit: float,
        sales: float
    ) -> Optional[float]:

        if sales == 0:
            return None

        return RatioCalculator._safe_round(
            (operating_profit / sales) * 100
        )

    # ---------------------------------------------------------
    # 3. OPM CROSS CHECK
    #
    # Returns:
    # {
    #     "difference": float,
    #     "match": bool
    # }
    #
    # match=True if difference <= tolerance
    # ---------------------------------------------------------
    @staticmethod
    def compare_opm(
        calculated_opm: Optional[float],
        source_opm: Optional[float],
        tolerance: float = 1.0
    ):

        if calculated_opm is None or source_opm is None:
            return {
                "difference": None,
                "match": False
            }

        difference = abs(calculated_opm - source_opm)

        return {
            "difference": round(difference, 2),
            "match": difference <= tolerance
        }

    # ---------------------------------------------------------
    # 4. RETURN ON EQUITY (ROE)
    #
    # Formula:
    # Net Profit / (Equity + Reserves) * 100
    #
    # Return None if denominator <=0
    # ---------------------------------------------------------
    @staticmethod
    def return_on_equity(
        net_profit: float,
        equity_capital: float,
        reserves: float
    ) -> Optional[float]:

        shareholder_equity = equity_capital + reserves

        if shareholder_equity <= 0:
            return None

        return RatioCalculator._safe_round(
            (net_profit / shareholder_equity) * 100
        )

    # ---------------------------------------------------------
    # 5. RETURN ON CAPITAL EMPLOYED (ROCE)
    #
    # Formula:
    # EBIT /
    # (Equity + Reserves + Borrowings)
    #
    # *100
    # ---------------------------------------------------------
    @staticmethod
    def return_on_capital_employed(
        ebit: float,
        equity_capital: float,
        reserves: float,
        borrowings: float
    ) -> Optional[float]:

        capital_employed = (
            equity_capital
            + reserves
            + borrowings
        )

        if capital_employed <= 0:
            return None

        return RatioCalculator._safe_round(
            (ebit / capital_employed) * 100
        )

    # ---------------------------------------------------------
    # 6. RETURN ON ASSETS (ROA)
    #
    # Formula:
    # Net Profit / Total Assets *100
    # ---------------------------------------------------------
    @staticmethod
    def return_on_assets(
        net_profit: float,
        total_assets: float
    ) -> Optional[float]:

        if total_assets == 0:
            return None

        return RatioCalculator._safe_round(
            (net_profit / total_assets) * 100
        )

      # ---------------------------------------------------------
    # 7. DEBT TO EQUITY
    # Formula:
    # Borrowings / (Equity + Reserves)
    # ---------------------------------------------------------
    @staticmethod
    def debt_to_equity(
        borrowings: float,
        equity_capital: float,
        reserves: float
    ) -> Optional[float]:

        if borrowings == 0:
            return 0

        shareholder_equity = equity_capital + reserves

        if shareholder_equity <= 0:
            return None

        return RatioCalculator._safe_round(
            borrowings / shareholder_equity
        )

    # ---------------------------------------------------------
    # HIGH LEVERAGE FLAG
    # ---------------------------------------------------------
    @staticmethod
    def high_leverage_flag(
        debt_to_equity: Optional[float],
        broad_sector: str
    ) -> bool:

        if debt_to_equity is None:
            return False

        if broad_sector.lower() == "financials":
            return False

        return debt_to_equity > 5

    # ---------------------------------------------------------
    # 8. INTEREST COVERAGE RATIO
    # Formula:
    # (Operating Profit + Other Income) / Interest
    # ---------------------------------------------------------
    @staticmethod
    def interest_coverage(
        operating_profit: float,
        other_income: float,
        interest: float
    ) -> Optional[float]:

        if interest == 0:
            return None

        return RatioCalculator._safe_round(
            (operating_profit + other_income) / interest
        )

    # ---------------------------------------------------------
    # ICR LABEL
    # ---------------------------------------------------------
    @staticmethod
    def icr_label(
        interest: float
    ):

        if interest == 0:
            return "Debt Free"

        return None

    # ---------------------------------------------------------
    # ICR WARNING
    # ---------------------------------------------------------
    @staticmethod
    def icr_warning(
        interest_coverage: Optional[float]
    ) -> bool:

        if interest_coverage is None:
            return False

        return interest_coverage < 1.5

    # ---------------------------------------------------------
    # 9. NET DEBT
    # Formula:
    # Borrowings - Investments
    # ---------------------------------------------------------
    @staticmethod
    def net_debt(
        borrowings: float,
        investments: float
    ) -> float:

        return RatioCalculator._safe_round(
            borrowings - investments
        )

    # ---------------------------------------------------------
    # 10. ASSET TURNOVER
    # Formula:
    # Sales / Total Assets
    # ---------------------------------------------------------
    @staticmethod
    def asset_turnover(
        sales: float,
        total_assets: float
    ) -> Optional[float]:

        if total_assets == 0:
            return None

        return RatioCalculator._safe_round(
            sales / total_assets
        )

    # ---------------------------------------------------------
    # Helper Method
    # ---------------------------------------------------------
    @staticmethod
    def print_ratio(name: str, value: Optional[float]):

        if value is None:
            print(f"{name}: Not Available")
        else:
            print(f"{name}: {value:.2f}%")