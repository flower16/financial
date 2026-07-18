"""Lifetime performance metrics derived from the ledger and current prices."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from .xirr import xirr


@dataclass
class PerformanceMetrics:
    """Headline lifetime performance numbers for the metric cards."""

    total_invested: float          # sum of all buy costs incl. fees
    total_proceeds: float          # sum of all sell proceeds net of fees
    current_value: float           # current market value of open positions
    realized_pnl: float            # locked-in gains/losses from sells
    unrealized_pnl: float          # paper gains/losses on open positions
    total_returns: float           # current_value + proceeds - invested
    total_returns_pct: float       # total_returns / invested * 100
    xirr: float | None             # money-weighted annualized return (decimal)


def compute_performance(
    ledger: pd.DataFrame,
    holdings_priced: pd.DataFrame,
    as_of: date | None = None,
) -> PerformanceMetrics:
    """Compute lifetime metrics from the ledger plus priced holdings.

    ``holdings_priced`` is the output of ``enrich_with_prices`` (may have NaN
    market values for unresolved tickers, which are treated as 0 for totals).
    """
    as_of = as_of or date.today()

    total_invested = 0.0
    total_proceeds = 0.0
    for _, txn in ledger.iterrows():
        amount = float(txn["quantity"]) * float(txn["price"])
        fees = float(txn["fees"])
        if txn["action"] == "BUY":
            total_invested += amount + fees
        elif txn["action"] == "SELL":
            total_proceeds += amount - fees

    current_value = float(holdings_priced["market_value"].sum(skipna=True)) \
        if not holdings_priced.empty else 0.0
    realized_pnl = float(holdings_priced["realized_pnl"].sum()) \
        if not holdings_priced.empty else 0.0
    unrealized_pnl = float(holdings_priced["unrealized_pnl"].sum(skipna=True)) \
        if not holdings_priced.empty else 0.0

    total_returns = current_value + total_proceeds - total_invested
    total_returns_pct = (
        total_returns / total_invested * 100 if total_invested else 0.0
    )

    return PerformanceMetrics(
        total_invested=total_invested,
        total_proceeds=total_proceeds,
        current_value=current_value,
        realized_pnl=realized_pnl,
        unrealized_pnl=unrealized_pnl,
        total_returns=total_returns,
        total_returns_pct=total_returns_pct,
        xirr=_portfolio_xirr(ledger, current_value, as_of),
    )


def _portfolio_xirr(
    ledger: pd.DataFrame, current_value: float, as_of: date
) -> float | None:
    """Build the cash-flow series and compute XIRR.

    Buys are negative flows, sells are positive flows, and the current
    portfolio value is added as a final positive flow dated ``as_of``.
    """
    flows: list[tuple[date, float]] = []
    for _, txn in ledger.iterrows():
        d = pd.Timestamp(txn["date"]).date()
        amount = float(txn["quantity"]) * float(txn["price"])
        fees = float(txn["fees"])
        if txn["action"] == "BUY":
            flows.append((d, -(amount + fees)))
        elif txn["action"] == "SELL":
            flows.append((d, amount - fees))

    if current_value > 0:
        flows.append((as_of, current_value))

    return xirr(flows)
