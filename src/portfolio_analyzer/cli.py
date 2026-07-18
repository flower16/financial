"""Console entry point that launches the Streamlit app."""
from __future__ import annotations

import sys
from pathlib import Path

from streamlit.web import cli as stcli

APP_PATH = Path(__file__).resolve().parent / "app.py"


def run() -> None:
    """Launch `streamlit run app.py`, forwarding any extra CLI args."""
    sys.argv = ["streamlit", "run", str(APP_PATH), *sys.argv[1:]]
    sys.exit(stcli.main())
