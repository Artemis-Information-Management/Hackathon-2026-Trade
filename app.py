"""Trade DNA - Streamlit entry point.

Run with:  streamlit run app.py
Pages live in ./pages and are picked up automatically by Streamlit.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))

from trade_dna import __version__  # noqa: E402
from trade_dna.config import FOCUS, country_name  # noqa: E402
from trade_dna.data import load_trade  # noqa: E402

st.set_page_config(page_title="Trade DNA", page_icon="🧬", layout="wide")

df, status = load_trade()

st.title("🧬 Trade DNA")
st.subheader(f"The trade profile of {country_name(FOCUS)}: who it resembles, what it depends on, and how that changed")

if status.is_sample:
    st.warning(
        "Running on a **synthetic sample**. Real figures appear once "
        "`data/processed/trade_hs2.parquet` exists (see README, *Data*).",
        icon="⚠️",
    )

c1, c2, c3 = st.columns(3)
c1.metric("Reporters", len(status.reporters))
c2.metric("Period", f"{status.periods[0]} – {status.periods[1]}")
c3.metric("Rows", f"{status.n_rows:,}")

st.markdown(
    """
Most trade dashboards answer *who* and *what*. This one asks a different question on each page of the sidebar:

| Lens | Question | Indicator |
|---|---|---|
| **1 · Trade twins** | Which European countries have a trade profile like Luxembourg's, and is that changing? | Finger-Kreinin similarity index |
| **2 · Dependency points** | For which products does Luxembourg rely on a single partner? | Herfindahl-Hirschman concentration |
| **3 · Smart zoom** | How do we show HS2 → CN8 detail without drowning the reader? | Top-k pruning of the product tree |
| **4 · Seasonality (R)** | Which flows are seasonal, and what is left once seasonality is removed? | STL decomposition, computed in R |
| **5 · Luxembourg's partners** | Who does Luxembourg actually trade with, country by country, and what flows between them? | Bilateral flows declared by Luxembourg (no *World* line) |

Data: Eurostat Comext **ds-045409**, *EU trade since 1988 by HS2-4-6 and CN8*.
Luxembourg is reported separately from Belgium only since **1999**, so series start there.
"""
)

with st.expander("About the data currently loaded"):
    st.write(f"Source: `{status.source}`")
    st.dataframe(df.head(20), width="stretch")

st.caption(f"Trade DNA v{__version__} · STATEC Hackathon 2026 · EUPL-1.2")
