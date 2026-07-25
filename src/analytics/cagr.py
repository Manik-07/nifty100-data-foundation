"""
cagr.py

Financial Ratio Engine
Sprint 2 - Day 10

Compound Annual Growth Rate (CAGR)
"""

from typing import Optional, Dict


class CAGRCalculator:

    @staticmethod
    def calculate_cagr(
        start_value: float,
        end_value: float,
        years: int
    ) -> Dict:

        if years <= 0:
            return {
                "value": None,
                "flag": "INSUFFICIENT"
            }

        if start_value == 0:
            return {
                "value": None,
                "flag": "ZERO_BASE"
            }

        if start_value > 0 and end_value < 0:
            return {
                "value": None,
                "flag": "DECLINE_TO_LOSS"
            }

        if start_value < 0 and end_value > 0:
            return {
                "value": None,
                "flag": "TURNAROUND"
            }

        if start_value < 0 and end_value < 0:
            return {
                "value": None,
                "flag": "BOTH_NEGATIVE"
            }

        cagr = ((end_value / start_value) ** (1 / years) - 1) * 100

        return {
            "value": round(cagr, 2),
            "flag": None
        }