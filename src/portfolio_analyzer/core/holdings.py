"""Derive current holdings and cost basis from the transaction ledger.

Cost basis uses the weighted-average method: a SELL reduces quantity but does
not change the per-share average cost of the remaining shares. Realized P&L on
a sell is (sell price - avg cost) * quantity, net of fees.
"""
from __future__ import annotations

import pandas as pd


def compute_holdings(ledger: pd.DataFrame) -> pd.DataFrame:
    """Replay the ledger into current positions per ticker.

    Returns one row per ticker with columns:
        ticker, quantity, avg_cost, cost_basis,
        realized_pnl, total_invested, total_proceeds
    Only tickers with a positive remaining quantity are returned.
    """
    records: list[dict] = []

    if ledger.empty:
        return _empty_holdings()

    for ticker, grp in ledger.sort_values("date").groupby("ticker"):
        qty = 0.0
        avg_cost = 0.0
        realized = 0.0
        invested = 0.0
        proceeds = 0.0

        for _, txn in grp.iterrows():
            q = float(txn["quantity"])
            price = float(txn["price"])
            fees = float(txn["fees"])

            if txn["action"] == "BUY":
                buy_cost = q * price + fees
                invested += buy_cost
                new_qty = qty + q
                # Weighted-average cost includes fees in the basis.
                avg_cost = ((avg_cost * qty) + buy_cost) / new_qty if new_qty else 0.0
                qty = new_qty
            elif txn["action"] == "SELL":
                sell_qty = min(q, qty)  # guard against overselling
                gross = q * price - fees
                proceeds += gross
                realized += (price - avg_cost) * sell_qty - fees
                qty -= sell_qty
                if qty <= 1e-9:
                    qty = 0.0
                    avg_cost = 0.0

        records.append(
            {
                "ticker": ticker,
                "quantity": qty,
                "avg_cost": avg_cost,
                "cost_basis": qty * avg_cost,
                "realized_pnl": realized,
                "total_invested": invested,
                "total_proceeds": proceeds,
            }
        )

    holdings = pd.DataFrame.from_records(records)
    open_positions = holdings[holdings["quantity"] > 1e-9].reset_index(drop=True)
    return open_positions if not open_positions.empty else _empty_holdings()


def enrich_with_prices(
    holdings: pd.DataFrame, prices: dict[str, float]
) -> pd.DataFrame:
    """Add current price, market value, and unrealized P&L columns.

    Tickers missing from ``prices`` get NaN market values so the UI can flag them.
    """
    df = holdings.copy()
    if df.empty:
        df["current_price"] = pd.Series(dtype="float64")
        df["market_value"] = pd.Series(dtype="float64")
        df["unrealized_pnl"] = pd.Series(dtype="float64")
        df["unrealized_pnl_pct"] = pd.Series(dtype="float64")
        df["allocation_pct"] = pd.Series(dtype="float64")
        return df

    df["current_price"] = df["ticker"].map(prices)
    df["market_value"] = df["current_price"] * df["quantity"]
    df["unrealized_pnl"] = df["market_value"] - df["cost_basis"]
    df["unrealized_pnl_pct"] = (
        df["unrealized_pnl"] / df["cost_basis"].replace(0, pd.NA) * 100
    )

    total_value = df["market_value"].sum(skipna=True)
    df["allocation_pct"] = (
        df["market_value"] / total_value * 100 if total_value else pd.NA
    )
    return df.sort_values("market_value", ascending=False).reset_index(drop=True)


def _empty_holdings() -> pd.DataFrame:
    cols = [
        "ticker",
        "quantity",
        "avg_cost",
        "cost_basis",
        "realized_pnl",
        "total_invested",
        "total_proceeds",
    ]
    return pd.DataFrame({c: pd.Series(dtype="float64") for c in cols})
