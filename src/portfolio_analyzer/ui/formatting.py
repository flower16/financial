"""Small display-formatting helpers shared across tabs."""
from __future__ import annotations

import pandas as pd

from ..config import CURRENCY_SYMBOL


def money(value: float | None) -> str:
    """Format a number as currency, or em dash if missing."""
    if value is None or pd.isna(value):
        return "—"
    return f"{CURRENCY_SYMBOL}{value:,.2f}"


def pct(value: float | None) -> str:
    """Format a number as a percentage, or em dash if missing."""
    if value is None or pd.isna(value):
        return "—"
    return f"{value:,.2f}%"


def signed_money(value: float | None) -> str:
    """Currency with an explicit + or - sign (for P&L)."""
    if value is None or pd.isna(value):
        return "—"
    sign = "+" if value >= 0 else "-"
    return f"{sign}{CURRENCY_SYMBOL}{abs(value):,.2f}"
