"""XIRR: money-weighted internal rate of return for irregular cash flows."""
from __future__ import annotations

from datetime import date

import numpy as np
from scipy.optimize import brentq


def _xnpv(rate: float, amounts: np.ndarray, years: np.ndarray) -> float:
    """Net present value of cash flows given a discount ``rate`` (annual)."""
    return float(np.sum(amounts / (1.0 + rate) ** years))


def xirr(cash_flows: list[tuple[date, float]]) -> float | None:
    """Compute the annualized internal rate of return for dated cash flows.

    ``cash_flows`` is a list of (date, amount) pairs. By convention outflows
    (buys) are negative and inflows (sells, current value) are positive.

    Returns the rate as a decimal (0.12 == 12%), or None when it cannot be
    solved (e.g. all flows same sign, fewer than 2 flows).
    """
    if len(cash_flows) < 2:
        return None

    flows = sorted(cash_flows, key=lambda x: x[0])
    amounts = np.array([amt for _, amt in flows], dtype=float)
    t0 = flows[0][0]
    years = np.array([(d - t0).days / 365.0 for d, _ in flows], dtype=float)

    # Need at least one positive and one negative flow for a root to exist.
    if not (np.any(amounts > 0) and np.any(amounts < 0)):
        return None

    try:
        # Bracket the rate between -99.99% and +100000%.
        return float(brentq(lambda r: _xnpv(r, amounts, years), -0.9999, 1000.0))
    except (ValueError, RuntimeError):
        return None
