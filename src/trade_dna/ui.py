"""Small helpers shared by the Streamlit pages (sidebar widgets, caching)."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Make `import trade_dna` work when Streamlit runs a page directly
SRC = Path(__file__).resolve().parents[1]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from trade_dna.config import FLOW_LABELS, FOCUS, country_name  # noqa: E402
from trade_dna.data import load_trade  # noqa: E402


@st.cache_data(show_spinner="Loading trade data…")
def cached_trade() -> tuple[pd.DataFrame, dict]:
    df, status = load_trade()
    return df, status.__dict__


def sample_banner(is_sample: bool) -> None:
    if is_sample:
        st.warning("Synthetic sample data. Numbers are not real.", icon="⚠️")


def flow_selector(key: str = "flow") -> str:
    label = st.sidebar.radio("Flow", list(FLOW_LABELS.values()), horizontal=True, key=key)
    return next(k for k, v in FLOW_LABELS.items() if v == label)


def period_slider(periods: list[str], key: str = "period", default: str | None = None) -> str:
    periods = sorted(periods)
    default = default or periods[-1]
    return st.sidebar.select_slider("Year", options=periods, value=default, key=key)


def country_multiselect(codes: list[str], default: list[str], key: str = "countries", label: str = "Compare with") -> list[str]:
    options = sorted(c for c in codes if c != FOCUS)
    chosen = st.sidebar.multiselect(label, options, default=[c for c in default if c in options], format_func=country_name, key=key)
    return chosen


def fmt_eur(x: float) -> str:
    if x >= 1e9:
        return f"{x / 1e9:,.1f} bn €"
    if x >= 1e6:
        return f"{x / 1e6:,.1f} M €"
    return f"{x:,.0f} €"
