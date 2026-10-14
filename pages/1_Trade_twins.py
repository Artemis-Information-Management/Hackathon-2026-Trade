"""Lens 1 - Trade twins (Finger-Kreinin similarity + map + trajectory)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st  # noqa: E402

from trade_dna.config import COMPARISON_DEFAULT, FOCUS, country_name  # noqa: E402
from trade_dna.indicators.similarity import similarity_over_time, top_twins  # noqa: E402
from trade_dna.ui import cached_trade, country_multiselect, flow_selector, period_slider, sample_banner  # noqa: E402
from trade_dna.viz import similarity_lines, similarity_map  # noqa: E402

st.set_page_config(page_title="Trade twins · Trade DNA", page_icon="🧬", layout="wide")
st.title("1 · Trade twins")
st.markdown(
    f"**Which countries have a trade profile like {country_name(FOCUS)}'s, and is that changing?** "
    "Similarity is the Finger-Kreinin index on HS2 product shares (0 = nothing in common, 1 = identical mix)."
)

df, status = cached_trade()
sample_banner(status["is_sample"])

flow = flow_selector()
periods = sorted(df.loc[df["freq"] == "A", "period"].unique())
period = period_slider(periods)
compare = country_multiselect(list(status["reporters"]), COMPARISON_DEFAULT, label="Trajectories for")


@st.cache_data(show_spinner="Computing similarity…")
def _sim(flow: str, is_sample: bool):
    d, _ = cached_trade()
    return similarity_over_time(d, flow, FOCUS)


sim = _sim(flow, status["is_sample"])
if sim.empty:
    st.error("No data for this flow. Check that `partner == 'WORLD'` rows exist in the processed file.")
    st.stop()

left, right = st.columns([3, 2])
with left:
    st.plotly_chart(similarity_map(sim, period), width="stretch")
with right:
    st.markdown(f"#### Closest twins in {period}")
    twins = top_twins(sim, period, n=5)
    for _, r in twins.iterrows():
        st.markdown(f"**{country_name(r['reporter'])}** &nbsp; `{r['fk']:.2f}`")
        st.progress(float(r["fk"]))
    first = periods[0]
    then = top_twins(sim, first, n=1)
    if len(then):
        st.caption(f"In {first} the closest twin was **{country_name(then.iloc[0]['reporter'])}** ({then.iloc[0]['fk']:.2f}).")

st.plotly_chart(similarity_lines(sim, compare), width="stretch")

with st.expander("Method"):
    st.markdown(
        r"""
For each country $c$ and year $t$, let $s_{c,i,t}$ be the share of HS2 chapter $i$ in total exports (or imports) to the world.

$$FK(LU, c, t) = \sum_i \min\big(s_{LU,i,t},\; s_{c,i,t}\big)$$

Finger, J.M. & Kreinin, M.E. (1979), *A measure of export similarity and its possible uses*, Economic Journal 89.
"""
    )
