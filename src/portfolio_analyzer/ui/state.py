"""Session-state helpers: the in-memory ledger backed by disk."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from ..data.storage import load_ledger, save_ledger

LEDGER_KEY = "ledger"


def init_state() -> None:
    """Load the ledger from disk into session state once per session."""
    if LEDGER_KEY not in st.session_state:
        st.session_state[LEDGER_KEY] = load_ledger()


def get_ledger() -> pd.DataFrame:
    """Return the current in-memory ledger."""
    return st.session_state[LEDGER_KEY]


def set_ledger(ledger: pd.DataFrame, persist: bool = True) -> None:
    """Replace the ledger in session state and optionally persist to disk."""
    st.session_state[LEDGER_KEY] = ledger
    if persist:
        save_ledger(ledger)
