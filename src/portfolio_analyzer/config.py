"""Central configuration: schema, paths, and constants."""
from __future__ import annotations

from pathlib import Path

# --- Paths -------------------------------------------------------------------
# Project root = three levels up from this file (.../src/portfolio_analyzer/config.py)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
LEDGER_PATH = DATA_DIR / "transactions.csv"  # legacy CSV, auto-migrated to SQLite
DB_PATH = DATA_DIR / "portfolio.db"
LEDGER_TABLE = "transactions"
SAMPLE_LEDGER_PATH = PROJECT_ROOT / "sample_data" / "sample_transactions.csv"

# --- Transaction ledger schema ----------------------------------------------
# The ledger is the single source of truth. Every other view is derived from it.
COLUMNS = ["date", "ticker", "action", "quantity", "price", "fees"]

ACTIONS = ["BUY", "SELL"]

# dtypes used when reading/normalizing the ledger
COLUMN_DTYPES = {
    "ticker": "string",
    "action": "string",
    "quantity": "float64",
    "price": "float64",
    "fees": "float64",
}

# --- Display / market --------------------------------------------------------
CURRENCY_SYMBOL = "$"

# yfinance price cache TTL (seconds)
PRICE_CACHE_TTL = 600
