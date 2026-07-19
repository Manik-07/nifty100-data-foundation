"""
Utility functions for cleaning and standardizing data.
"""

import re


def normalize_year(year):
    """
    Convert different year formats into integer years.

    Examples:
        2023 -> 2023
        "2023" -> 2023
        "FY23" -> 2023
        "FY2022" -> 2022
    """

    if year is None:
        return None

    year = str(year).strip().upper()

    if year.startswith("FY"):
        year = year.replace("FY", "")

        if len(year) == 2:
            return int("20" + year)

    if year.isdigit():
        return int(year)

    return None


def normalize_ticker(ticker):
    """
    Standardize stock ticker.

    Examples:
        " tcs " -> "TCS"
        "reliance" -> "RELIANCE"
    """

    if ticker is None:
        return None

    ticker = str(ticker).strip().upper()

    ticker = re.sub(r"\s+", "", ticker)

    return ticker