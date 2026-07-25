"""
cashflow_kpis.py

Financial Ratio Engine
Sprint 2 - Day 11
"""

from typing import Optional


class CashFlowKPIs:

    @staticmethod
    def free_cash_flow(
        operating_activity: float,
        investing_activity: float
    ) -> float:
        """
        Free Cash Flow = CFO + Investing Cash Flow
        """
        return round(
            operating_activity + investing_activity,
            2
        )

    @staticmethod
    def cfo_quality_score(
        cfo: float,
        pat: float
    ):

        if pat == 0:
            return None

        ratio = cfo / pat

        if ratio > 1:
            return "High Quality"

        elif ratio >= 0.5:
            return "Moderate"

        return "Accrual Risk"

    @staticmethod
    def capex_intensity(
        investing_activity: float,
        sales: float
    ):

        if sales == 0:
            return None

        intensity = abs(investing_activity) / sales * 100

        intensity = round(intensity, 2)

        if intensity < 3:
            label = "Asset Light"

        elif intensity <= 8:
            label = "Moderate"

        else:
            label = "Capital Intensive"

        return {
            "value": intensity,
            "label": label
        }

    @staticmethod
    def fcf_conversion(
        free_cash_flow: float,
        operating_profit: float
    ) -> Optional[float]:

        if operating_profit == 0:
            return None

        return round(
            free_cash_flow / operating_profit * 100,
            2
        )

    @staticmethod
    def capital_allocation_pattern(
        cfo: float,
        cfi: float,
        cff: float,
        cfo_pat_ratio: Optional[float] = None
    ):

        s1 = "+" if cfo >= 0 else "-"
        s2 = "+" if cfi >= 0 else "-"
        s3 = "+" if cff >= 0 else "-"

        pattern = (s1, s2, s3)

        if pattern == ("+", "-", "-"):
            if cfo_pat_ratio is not None and cfo_pat_ratio > 1:
                return "Shareholder Returns"
            return "Reinvestor"

        elif pattern == ("+", "+", "-"):
            return "Liquidating Assets"

        elif pattern == ("-", "+", "+"):
            return "Distress Signal"

        elif pattern == ("-", "-", "+"):
            return "Growth Funded by Debt"

        elif pattern == ("+", "+", "+"):
            return "Cash Accumulator"

        elif pattern == ("-", "-", "-"):
            return "Pre-Revenue"

        elif pattern == ("+", "-", "+"):
            return "Mixed"

        return "Unknown"