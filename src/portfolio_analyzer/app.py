"""Streamlit entry point: wires the three tabs together."""
from __future__ import annotations

import streamlit as st

from portfolio_analyzer.ui import tab_performance, tab_portfolio, tab_transactions
from portfolio_analyzer.ui.state import init_state


def main() -> None:
    st.set_page_config(
        page_title="Portfolio Analyzer",
        page_icon="📈",
        layout="wide",
    )
    st.title("📈 Stock Market Portfolio Analyzer")

    init_state()

    tab1, tab2, tab3 = st.tabs(
        ["Transactions", "Portfolio Snapshot", "Historic Performance"]
    )
    with tab1:
        tab_transactions.render()
    with tab2:
        tab_portfolio.render()
    with tab3:
        tab_performance.render()


if __name__ == "__main__":
    main()
