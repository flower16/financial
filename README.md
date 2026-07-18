# 📈 Stock Market Portfolio Analyzer

A simple Streamlit app to track stock transactions and analyze portfolio
performance. Built with [UV](https://docs.astral.sh/uv/), Streamlit, and
yfinance.

## Features

- **Transactions tab** — upload a CSV of your trade history or enter trades
  manually. The ledger is persisted to a local **SQLite** database at
  `data/portfolio.db` (an existing `data/transactions.csv` is auto-migrated on
  first run).
- **Portfolio Snapshot tab** — allocation pie chart plus a holdings table with
  quantity, weighted-average cost basis, current price, market value, and
  unrealized P&L.
- **Historic Performance tab** — metric cards for total invested, proceeds from
  sales, current value, total returns, and **XIRR**, plus a portfolio-value-
  over-time chart.

## Setup

```bash
uv sync
```

## Run

```bash
uv run portfolio-analyzer
# or, equivalently:
uv run streamlit run src/portfolio_analyzer/app.py
```

The app opens in your browser at http://localhost:8501.

## Deploy on Replit

This repo is Replit-ready:

1. Create a new Repl by importing this GitHub repository.
2. Replit installs dependencies from `requirements.txt` automatically.
3. Press **Run** — the `.replit` file launches Streamlit on port 8080
   (`0.0.0.0`), and Replit exposes it as a web view. Use **Deploy** for a
   permanent URL (Autoscale/Cloud Run target is preconfigured).

The SQLite database lives at `data/portfolio.db` inside the Repl, so your
ledger persists across runs.

## CSV format

Your transaction CSV must have these columns:

| column     | description                                  |
|------------|----------------------------------------------|
| `date`     | trade date (any parseable format, e.g. 2024-01-15) |
| `ticker`   | stock symbol, e.g. `AAPL`                     |
| `action`   | `BUY` or `SELL`                               |
| `quantity` | number of shares (> 0)                        |
| `price`    | price per share (> 0)                         |
| `fees`     | transaction fees (optional, defaults to 0)    |

See [`sample_data/sample_transactions.csv`](sample_data/sample_transactions.csv)
for an example — you can load it from the Transactions tab with one click.

## Notes & assumptions

- **US stocks (USD).** Tickers are passed to yfinance as-is.
- **Weighted-average cost basis.** A sell reduces quantity but doesn't change
  the average cost of remaining shares.
- **XIRR** treats buys as negative cash flows, sells as positive, and the
  current portfolio value as a final positive flow dated today.
- Dividends and stock splits are out of scope for v1 (buy/sell ledger only).
- Single-user, local app. Your ledger lives only on your machine.

## Project structure

```
src/portfolio_analyzer/
├── app.py              # Streamlit entry point (tab orchestration)
├── cli.py              # `portfolio-analyzer` console script
├── config.py           # schema, paths, constants
├── data/
│   ├── storage.py      # load/save the ledger CSV
│   ├── ingestion.py    # CSV parse + validation, manual entry
│   └── market.py       # cached yfinance price/history fetch
├── core/
│   ├── holdings.py     # ledger → positions + cost basis
│   ├── performance.py  # lifetime metrics
│   └── xirr.py         # XIRR solver
└── ui/
    ├── state.py        # session-state ledger backed by disk
    ├── formatting.py   # display helpers
    ├── tab_transactions.py
    ├── tab_portfolio.py
    └── tab_performance.py
```
