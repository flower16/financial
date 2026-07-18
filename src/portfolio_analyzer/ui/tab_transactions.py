"""Tab 1: upload a CSV or manually enter transactions."""
from __future__ import annotations

from datetime import date

import streamlit as st

from ..config import ACTIONS, COLUMNS, SAMPLE_LEDGER_PATH
from ..data.ingestion import (
    append_transaction,
    make_transaction,
    parse_csv,
    validate_ledger,
)
from .state import get_ledger, set_ledger


def render() -> None:
    st.header("Transactions")
    st.caption(
        "Upload a transaction history CSV or add trades manually. "
        "Everything else in the app is derived from this ledger."
    )

    _render_upload()
    st.divider()
    _render_manual_entry()
    st.divider()
    _render_ledger_table()


def _render_upload() -> None:
    st.subheader("Upload CSV")
    st.write(
        f"Expected columns: `{'`, `'.join(COLUMNS)}` "
        "— `action` is BUY or SELL, `fees` is optional."
    )

    uploaded = st.file_uploader("Choose a CSV file", type=["csv"])
    if uploaded is None:
        if SAMPLE_LEDGER_PATH.exists():
            st.caption("No file? Load the bundled sample data to explore the app.")
            if st.button("Load sample data"):
                set_ledger(_load_sample())
                st.success("Sample data loaded.")
                st.rerun()
        return

    try:
        raw = parse_csv(uploaded)
    except Exception as exc:  # noqa: BLE001 - surface any parse error to the user
        st.error(f"Could not read CSV: {exc}")
        return

    result = validate_ledger(raw)
    for warning in result.warnings:
        st.warning(warning)

    if not result.ok:
        for err in result.errors:
            st.error(err)
        st.info("Fix the issues above and re-upload.")
        return

    st.success(f"Parsed {len(result.ledger)} transactions.")
    st.dataframe(result.ledger, width="stretch", hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Replace ledger with this file", type="primary"):
            set_ledger(result.ledger)
            st.success("Ledger replaced.")
            st.rerun()
    with col2:
        if st.button("Append to existing ledger"):
            combined = append_transaction(get_ledger(), result.ledger)
            set_ledger(combined)
            st.success("Transactions appended.")
            st.rerun()


def _render_manual_entry() -> None:
    st.subheader("Add a transaction manually")

    with st.form("manual_entry", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            ticker = st.text_input("Ticker", placeholder="AAPL")
            txn_date = st.date_input("Date", value=date.today())
        with c2:
            action = st.selectbox("Action", ACTIONS)
            quantity = st.number_input("Quantity", min_value=0.0, step=1.0, value=0.0)
        with c3:
            price = st.number_input("Price", min_value=0.0, step=1.0, value=0.0)
            fees = st.number_input("Fees", min_value=0.0, step=1.0, value=0.0)

        submitted = st.form_submit_button("Add transaction", type="primary")

    if submitted:
        if not ticker.strip():
            st.error("Ticker is required.")
            return
        if quantity <= 0 or price <= 0:
            st.error("Quantity and price must be greater than zero.")
            return

        row = make_transaction(
            date=txn_date,
            ticker=ticker,
            action=action,
            quantity=quantity,
            price=price,
            fees=fees,
        )
        set_ledger(append_transaction(get_ledger(), row))
        st.success(f"Added {action} {quantity:g} {ticker.upper()} @ {price:g}.")
        st.rerun()


def _render_ledger_table() -> None:
    st.subheader("Current ledger")
    ledger = get_ledger()

    if ledger.empty:
        st.info("No transactions yet. Upload a CSV or add one above.")
        return

    display = ledger.copy()
    display.insert(0, "row", range(1, len(display) + 1))
    st.dataframe(display, width="stretch", hide_index=True)

    c1, c2 = st.columns([3, 1])
    with c1:
        to_delete = st.number_input(
            "Row number to delete",
            min_value=1,
            max_value=len(ledger),
            step=1,
            value=1,
        )
    with c2:
        st.write("")
        st.write("")
        if st.button("Delete row"):
            updated = ledger.drop(ledger.index[int(to_delete) - 1]).reset_index(
                drop=True
            )
            set_ledger(updated)
            st.success(f"Deleted row {int(to_delete)}.")
            st.rerun()

    csv = ledger.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download ledger as CSV", csv, "transactions.csv", "text/csv"
    )


def _load_sample():
    import pandas as pd

    from ..data.storage import normalize_ledger

    return normalize_ledger(pd.read_csv(SAMPLE_LEDGER_PATH))
