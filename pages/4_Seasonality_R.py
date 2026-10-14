"""Lens 4 - Seasonality, computed by the R script r/seasonality.R.

This page is the template for any R-backed page:
  1. build the input frame in the tidy schema,
  2. call r_bridge.run_or_cached(script, frame, output_name),
  3. plot what comes back.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st  # noqa: E402

from trade_dna import r_bridge  # noqa: E402
from trade_dna.config import FLOW_LABELS, country_name, hs2_label  # noqa: E402
from trade_dna.data.loader import load_monthly  # noqa: E402
from trade_dna.ui import sample_banner  # noqa: E402
from trade_dna.viz import decomposition_chart, seasonal_heatmap  # noqa: E402

st.set_page_config(page_title="Seasonality (R) · Trade DNA", page_icon="🧬", layout="wide")
st.title("4 · Seasonality")
st.markdown(
    "**Which flows are seasonal, and what is left once seasonality is removed?** "
    "The decomposition runs in **R** (`r/seasonality.R`, STL). Python only ships the data in and draws the result."
)

monthly, is_sample = load_monthly()
sample_banner(is_sample)

with st.sidebar:
    st.markdown("#### R status")
    if r_bridge.rscript_available():
        st.success(f"Rscript found: `{r_bridge.rscript_path()}`")
    else:
        st.info("Rscript not found. Using the last committed output in `data/processed/r/`.")
    force = st.button("Re-run R script", disabled=not r_bridge.rscript_available())
    scripts = [p.name for p in r_bridge.list_r_scripts()]
    st.caption("Scripts in r/: " + (", ".join(f"`{s}`" for s in scripts) or "none"))

try:
    result, source = r_bridge.run_or_cached("seasonality.R", monthly, "seasonality.csv", force=force)
except r_bridge.RNotAvailable as e:
    st.error(str(e))
    st.markdown(
        "To produce the cached output once, on a machine with R:\n\n"
        "```bash\nRscript r/seasonality.R --input data/processed/r/_input_seasonality.csv --output data/processed/r/seasonality.csv\n```"
    )
    st.stop()
except RuntimeError as e:
    st.error("R script failed")
    st.code(str(e))
    st.stop()

st.caption(f"Decomposition source: **{'R, just now' if source == 'r' else 'cached CSV'}** · {result['series_id'].nunique()} series")

series_ids = sorted(result["series_id"].unique())


def _label(sid: str) -> str:
    rep, part, prod, flow = sid.split("|")
    return f"{country_name(rep)} → {country_name(part)} · {hs2_label(prod)} · {FLOW_LABELS.get(flow, flow)}"


sid = st.selectbox("Series", series_ids, format_func=_label)
one = result[result["series_id"] == sid]
st.plotly_chart(decomposition_chart(one, title=_label(sid)), width="stretch")

# Seasonal profile: average seasonal component by calendar month, across series
st.markdown("#### Seasonal fingerprint (average seasonal component by month, % of trend)")
prof = result.copy()
prof["month"] = prof["period"].str[5:7]
prof["seasonal_pct"] = prof["seasonal"] / prof["trend"]
fp = prof.pivot_table(index="series_id", columns="month", values="seasonal_pct", aggfunc="mean")
fp.index = [_label(s) for s in fp.index]
st.plotly_chart(seasonal_heatmap(fp), width="stretch")
