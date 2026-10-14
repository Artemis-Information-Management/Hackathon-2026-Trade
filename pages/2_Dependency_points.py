"""Lens 2 - Dependency points (HHI of partner concentration per product)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from trade_dna.config import FOCUS, country_name, hs2_label  # noqa: E402
from trade_dna.indicators.concentration import hhi_by_product, hhi_over_time, weighted_hhi  # noqa: E402
from trade_dna.ui import cached_trade, flow_selector, fmt_eur, period_slider, sample_banner  # noqa: E402
from trade_dna.viz import hhi_lines  # noqa: E402

st.set_page_config(page_title="Dependency points · Trade DNA", page_icon="🧬", layout="wide")
st.title("2 · Dependency points")
st.markdown(
    f"**For which products does {country_name(FOCUS)} rely on a single partner?** "
    "Concentration is the Herfindahl-Hirschman index of partner shares, per HS2 chapter. "
    "Above 0.25 is conventionally called concentrated."
)

df, status = cached_trade()
sample_banner(status["is_sample"])

flow = flow_selector()
periods = sorted(df.loc[df["freq"] == "A", "period"].unique())
period = period_slider(periods)
min_value = st.sidebar.number_input("Ignore products below (M€)", min_value=0.0, value=10.0, step=5.0) * 1e6

table = hhi_by_product(df, period, flow, FOCUS, min_value=min_value)
if table.empty:
    st.error("No bilateral rows for this selection. The processed file needs partner-level data (not only WORLD).")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Trade-weighted HHI", f"{weighted_hhi(table):.2f}")
c2.metric("Concentrated products (HHI > 0.25)", int((table["hhi"] > 0.25).sum()))
top = table.iloc[0]
c3.metric("Most concentrated", hs2_label(top["product"]), f"{country_name(top['top_partner'])} {top['top_share']:.0%}")

show = table.copy()
show["product"] = show["product"].map(hs2_label)
show["top_partner"] = show["top_partner"].map(country_name)
show["total"] = show["total"].map(fmt_eur)
show = show.rename(columns={"product": "Product", "hhi": "HHI", "top_partner": "Top partner", "top_share": "Top share", "total": "Trade", "n_partners": "Partners"})
st.dataframe(
    show,
    width="stretch",
    hide_index=True,
    column_config={
        "HHI": st.column_config.ProgressColumn("HHI", min_value=0, max_value=1, format="%.2f"),
        "Top share": st.column_config.NumberColumn(format="%.0f%%"),
    },
)

st.markdown("#### How concentration moved over time")
default_products = list(table["product"].head(4))
chosen = st.multiselect("Products", options=list(table["product"]), default=default_products, format_func=hs2_label)
if chosen:
    long = hhi_over_time(df, flow, FOCUS, products=chosen)
    st.plotly_chart(hhi_lines(long, chosen), width="stretch")

with st.expander("Method"):
    st.markdown(
        r"""
For product $i$ in year $t$, with $w_{p}$ the share of partner $p$ in Luxembourg's trade of $i$ (aggregates such as *World* or *EU27* excluded):

$$HHI_{i,t} = \sum_p w_{p}^2$$

$1/N$ means perfectly spread over $N$ partners, $1$ means a single partner. The headline number is the trade-weighted mean of $HHI_{i,t}$ across products.
"""
    )
