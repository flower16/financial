"""Tab 2: consolidated portfolio snapshot — allocation pie + holdings table."""
from __future__ import annotations

import plotly.express as px
import streamlit as st

from ..core.holdings import compute_holdings, enrich_with_prices
from ..data.market import get_current_prices
from .formatting import money, pct, signed_money
from .state import get_ledger


def render() -> None:
    st.header("Portfolio snapshot")

    ledger = get_ledger()
    if ledger.empty:
        st.info("No transactions yet. Add some in the Transactions tab.")
        return

    holdings = compute_holdings(ledger)
    if holdings.empty:
        st.info("No open positions — all holdings have been sold.")
        return

    tickers = tuple(holdings["ticker"].tolist())
    with st.spinner("Fetching current prices…"):
        prices = get_current_prices(tickers)

    priced = enrich_with_prices(holdings, prices)

    missing = [t for t in tickers if t not in prices]
    if missing:
        st.warning(
            "Could not fetch prices for: "
            f"{', '.join(missing)}. They're excluded from value totals."
        )

    _render_summary(priced)
    st.divider()

    left, right = st.columns([1, 1])
    with left:
        _render_pie(priced)
    with right:
        _render_holdings_table(priced)


def _render_summary(priced) -> None:
    total_value = priced["market_value"].sum(skipna=True)
    total_cost = priced["cost_basis"].sum()
    total_unrealized = priced["unrealized_pnl"].sum(skipna=True)
    pnl_pct = (total_unrealized / total_cost * 100) if total_cost else 0.0

    c1, c2, c3 = st.columns(3)
    c1.metric("Current value", money(total_value))
    c2.metric("Invested (open positions)", money(total_cost))
    c3.metric(
        "Unrealized P&L",
        signed_money(total_unrealized),
        delta=f"{pnl_pct:,.2f}%",
    )


def _render_pie(priced) -> None:
    st.subheader("Allocation")
    chart_df = priced.dropna(subset=["market_value"])
    if chart_df.empty or chart_df["market_value"].sum() <= 0:
        st.info("No priced holdings to chart.")
        return

    fig = px.pie(
        chart_df,
        names="ticker",
        values="market_value",
        hole=0.4,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(showlegend=True, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig, width="stretch")


def _render_holdings_table(priced) -> None:
    st.subheader("Holdings")

    view = priced.copy()
    display = view.assign(
        Quantity=view["quantity"].map(lambda v: f"{v:,.4g}"),
        **{
            "Avg cost": view["avg_cost"].map(money),
            "Current price": view["current_price"].map(money),
            "Market value": view["market_value"].map(money),
            "Unrealized P&L": view["unrealized_pnl"].map(signed_money),
            "Return %": view["unrealized_pnl_pct"].map(pct),
            "Allocation": view["allocation_pct"].map(pct),
        },
    )
    display = display.rename(columns={"ticker": "Ticker"})
    columns = [
        "Ticker",
        "Quantity",
        "Avg cost",
        "Current price",
        "Market value",
        "Unrealized P&L",
        "Return %",
        "Allocation",
    ]
    st.dataframe(display[columns], width="stretch", hide_index=True)
