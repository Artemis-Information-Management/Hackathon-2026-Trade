"""Lens 1 - Trade twins (Finger-Kreinin similarity + map + trajectory)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st  # noqa: E402

from trade_dna.config import COMPARISON_DEFAULT, FLOW_LABELS, FOCUS, country_name, hs2_name  # noqa: E402
from trade_dna.indicators.similarity import (  # noqa: E402
    collapse_overlap,
    common_matrix,
    finger_kreinin,
    overlap_summary,
    product_overlap,
    product_shares,
    similarity_over_time,
    top_twins,
)
from trade_dna.ui import cached_trade, country_multiselect, flow_selector, period_slider, sample_banner  # noqa: E402
from trade_dna.viz import overlap_chart, similarity_lines, similarity_map, twin_product_heatmap  # noqa: E402

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

# --------------------------------------------------------------------------
# Product dimension: what is each score made of?
# --------------------------------------------------------------------------
st.divider()
st.subheader("Why twins? Look inside the basket")
flow_word = FLOW_LABELS.get(flow, "trade").lower()
st.markdown(
    f"A similarity score is a total. Here it is taken apart **product by product** for {period}: "
    f"for each HS2 chapter, the part of the {flow_word} basket that {country_name(FOCUS)} and the other country "
    "have **in common** is the smaller of their two shares. Add those parts up and you get the score "
    "(0.72 = 72 points out of 100)."
)


@st.cache_data(show_spinner=False)
def _shares(flow: str, period: str, is_sample: bool):
    d, _ = cached_trade()
    return product_shares(d, flow, period)


shares = _shares(flow, period, status["is_sample"])
ranking = finger_kreinin(shares).drop(FOCUS, errors="ignore") if FOCUS in shares.index else None

if ranking is None or ranking.empty:
    st.info(f"No product breakdown available for {period}.")
else:
    tab_one, tab_five = st.tabs(["One country in detail", "Top 5 side by side"])

    with tab_one:
        other = st.selectbox(
            f"Compare {country_name(FOCUS)} with",
            options=list(ranking.index),
            format_func=lambda c: f"{country_name(c)} · {ranking[c] * 100:.0f} pts",
            key="twin_detail",
        )
        overlap = product_overlap(shares, other)
        st.plotly_chart(
            overlap_chart(collapse_overlap(overlap, n=10), other, flow_label=flow_word),
            width="stretch",
            config={"displayModeBar": False},
        )

        info = overlap_summary(overlap, k=3)
        score = ranking[other] * 100
        text = f"**{country_name(other)} scores {score:.0f} points.**"
        if info["top_common"]:
            named = ", ".join(f"**{hs2_name(c)}** ({c})" for c, _ in info["top_common"])
            main = sum(v for _, v in info["top_common"]) * 100
            text += f" Most of it comes from {named}: together {main:.0f} of the {score:.0f} points."
        if info["gap"]:
            code, f_share, o_share = info["gap"]
            text += (
                f" The biggest difference is **{hs2_name(code)}** ({code}): "
                f"{f_share * 100:.0f} % of {country_name(FOCUS)}'s {flow_word} against "
                f"{o_share * 100:.0f} % of {country_name(other)}'s."
            )
        st.markdown(text)
        st.caption(
            "Read it like this: each bar is a chapter's share of the country's total. "
            "The amber part (the smaller of the two shares) is mirrored on both sides, and the amber parts add up "
            "to the score. Grey is what only one of the two countries has."
        )

    with tab_five:
        top5 = list(ranking.index[:5])
        st.plotly_chart(
            twin_product_heatmap(common_matrix(shares, top5, n=10), ranking, flow_label=flow_word),
            width="stretch",
            config={"displayModeBar": False},
        )
        st.caption(
            "Each cell is the number of points a chapter contributes to a country's score "
            f"(the part of the basket shared with {country_name(FOCUS)}). Each column adds up to the score at the top. "
            "A dark cell is a chapter that really ties the two economies together."
        )

with st.expander("Method"):
    st.markdown(
        r"""
For each country $c$ and year $t$, let $s_{c,i,t}$ be the share of HS2 chapter $i$ in total exports (or imports) to the world.

$$FK(LU, c, t) = \sum_i \min\big(s_{LU,i,t},\; s_{c,i,t}\big)$$

**Product view.** The sum can be split by chapter: chapter $i$ contributes $\min(s_{LU,i}, s_{c,i})$, so the contributions add up exactly to $FK(LU, c)$. The butterfly chart shows these terms for one country; the heatmap shows them for the five closest twins. Chapters outside the ten largest are folded into one "Other chapters" row so the totals stay exact.

Finger, J.M. & Kreinin, M.E. (1979), *A measure of export similarity and its possible uses*, Economic Journal 89.
"""
    )
