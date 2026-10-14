"""Lens 3 - Smart zoom (HS2 -> CN8 with top-k pruning, as a sunburst)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st  # noqa: E402

from trade_dna.config import FLOW_LABELS, FOCUS, country_name  # noqa: E402
from trade_dna.data.loader import load_lu_detail  # noqa: E402
from trade_dna.indicators.hierarchy import prune_hierarchy  # noqa: E402
from trade_dna.ui import fmt_eur, sample_banner  # noqa: E402
from trade_dna.viz import product_sunburst  # noqa: E402

st.set_page_config(page_title="Smart zoom · Trade DNA", page_icon="🧬", layout="wide")
st.title("3 · Smart zoom")
st.markdown(
    "**How do we show HS2 → HS4 → HS6 → CN8 detail without drowning the reader?** "
    "At every node of the product tree we keep the top-*k* children (and anything above a minimum share) "
    "and fold the rest into one *Other* slice. Nothing is dropped, but only the significant flows get a name. "
    "Click a slice to zoom in, click the centre to zoom out."
)


@st.cache_data(show_spinner="Loading detail…")
def _detail():
    return load_lu_detail()


detail, is_sample = _detail()
sample_banner(is_sample)

flows = sorted(detail["flow"].unique())
periods = sorted(detail["period"].unique())
partners = sorted(detail["partner"].unique())

flow = st.sidebar.radio("Flow", flows, format_func=lambda f: FLOW_LABELS.get(f, f), horizontal=True)
period = st.sidebar.select_slider("Year", options=periods, value=periods[-1])
partner = st.sidebar.selectbox("Partner", partners, index=partners.index("WORLD") if "WORLD" in partners else 0, format_func=country_name)
top_k = st.sidebar.slider("Keep top-k per level", 2, 10, 5)
min_share = st.sidebar.slider("…plus anything above (% of parent)", 0.0, 10.0, 2.0, 0.5) / 100
depth = st.sidebar.slider("Rings shown", 2, 4, 3)

sub = detail[(detail["flow"] == flow) & (detail["period"] == period) & (detail["partner"] == partner)]
if sub.empty:
    st.error("No rows for this selection.")
    st.stop()

nodes = prune_hierarchy(sub, top_k=top_k, min_share=min_share, root_label=f"{country_name(FOCUS)} {FLOW_LABELS.get(flow, flow).lower()} {period}")

c1, c2, c3 = st.columns(3)
c1.metric("Total", fmt_eur(nodes.loc[nodes['level'] == 0, 'value'].iloc[0]))
c2.metric("Named nodes", int((~nodes["is_other"] & (nodes["level"] > 0)).sum()))
c3.metric("Folded into 'Other'", int(nodes["is_other"].sum()), help="Number of 'Other' slices, one per parent with a tail")

st.plotly_chart(product_sunburst(nodes, title="", max_depth=depth), width="stretch")

with st.expander("Node table (what the chart is drawn from)"):
    st.dataframe(nodes, width="stretch", hide_index=True)
