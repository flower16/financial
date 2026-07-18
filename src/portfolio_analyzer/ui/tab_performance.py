"""Tab 3: lifetime performance metric cards + portfolio value over time."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from ..core.holdings import compute_holdings, enrich_with_prices
from ..core.performance import compute_performance
from ..data.market import get_current_prices, get_price_history
from .formatting import money, pct, signed_money
from .state import get_ledger


def render() -> None:
    st.header("Historic performance")

    ledger = get_ledger()
    if ledger.empty:
        st.info("No transactions yet. Add some in the Transactions tab.")
        return

    holdings = compute_holdings(ledger)
    tickers = tuple(holdings["ticker"].tolist())
    with st.spinner("Fetching prices…"):
        prices = get_current_prices(tickers) if tickers else {}
    priced = enrich_with_prices(holdings, prices)

    metrics = compute_performance(ledger, priced)

    _render_cards(metrics)
    st.divider()
    _render_breakdown(metrics)
    st.divider()
    _render_value_chart(ledger, holdings)


def _render_cards(metrics) -> None:
    row1 = st.columns(3)
    row1[0].metric("Total lifetime investment", money(metrics.total_invested))
    row1[1].metric("Total proceeds from sales", money(metrics.total_proceeds))
    row1[2].metric("Current portfolio value", money(metrics.current_value))

    row2 = st.columns(2)
    row2[0].metric(
        "Total returns",
        signed_money(metrics.total_returns),
        delta=f"{metrics.total_returns_pct:,.2f}%",
    )
    xirr_display = pct(metrics.xirr * 100) if metrics.xirr is not None else "—"
    row2[1].metric("XIRR (annualized)", xirr_display)


def _render_breakdown(metrics) -> None:
    st.subheader("Returns breakdown")
    c1, c2 = st.columns(2)
    c1.metric("Realized P&L (from sales)", signed_money(metrics.realized_pnl))
    c2.metric("Unrealized P&L (open positions)", signed_money(metrics.unrealized_pnl))
    st.caption(
        "Total returns = current value + proceeds − invested. "
        "XIRR is the money-weighted annualized return, treating buys as "
        "outflows, sells as inflows, and today's portfolio value as a final inflow."
    )


def _render_value_chart(ledger, holdings) -> None:
    st.subheader("Portfolio value over time")

    if holdings.empty:
        st.info("No open positions to chart.")
        return

    tickers = tuple(holdings["ticker"].tolist())
    start = pd.Timestamp(ledger["date"].min())
    with st.spinner("Building history…"):
        history = get_price_history(tickers, start)

    if history.empty:
        st.info("Price history unavailable for these tickers.")
        return

    value_series = _portfolio_value_series(ledger, history)
    if value_series.empty:
        st.info("Not enough data to build a value series.")
        return

    fig = px.area(
        value_series,
        x=value_series.index,
        y=value_series.values,
        labels={"x": "Date", "y": "Portfolio value"},
    )
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
    st.plotly_chart(fig, width="stretch")


def _portfolio_value_series(ledger, history: pd.DataFrame) -> pd.Series:
    """Compute daily portfolio market value by holding qty held on each date.

    For each date in the price history we know the quantity held of each ticker
    (cumulative signed quantity up to that date) and multiply by that day's
    close.
    """
    dates = history.index
    # Build per-ticker cumulative quantity over the price-history dates.
    qty_by_date = pd.DataFrame(0.0, index=dates, columns=history.columns)

    for ticker in history.columns:
        txns = ledger[ledger["ticker"] == ticker].sort_values("date")
        running = 0.0
        # Step function of quantity over time.
        events = []
        for _, t in txns.iterrows():
            delta = t["quantity"] if t["action"] == "BUY" else -t["quantity"]
            running += delta
            events.append((pd.Timestamp(t["date"]).normalize(), running))

        if not events:
            continue
        # Apply each event level forward in time.
        qty = pd.Series(0.0, index=dates)
        for event_date, level in events:
            qty.loc[dates >= event_date] = level
        qty_by_date[ticker] = qty.clip(lower=0.0)

    value = (qty_by_date * history).sum(axis=1)
    return value[value > 0]
