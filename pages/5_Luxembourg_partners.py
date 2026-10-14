"""Lens 5 - Luxembourg's partners: the bilateral flows declared by Luxembourg."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st  # noqa: E402

from trade_dna.config import FOCUS, country_name, hs2_name  # noqa: E402
from trade_dna.indicators.partners import ALL_PRODUCTS, partner_product_mix, partner_shares_over_time, partner_table  # noqa: E402
from trade_dna.ui import cached_trade, flow_selector, fmt_eur, period_slider, sample_banner  # noqa: E402
from trade_dna.viz import partner_bars, partner_lines, partner_mix_bars  # noqa: E402

st.set_page_config(page_title="Luxembourg's partners · Trade DNA", page_icon="🧬", layout="wide")
st.title("5 · Luxembourg's partners")
st.markdown(
    f"**Who does {country_name(FOCUS)} actually trade with?** Country by country, as declared by {country_name(FOCUS)}: "
    f"its imports *from* each partner, or its exports *to* each partner. No *World* total here, only named countries."
)

df, status = cached_trade()
sample_banner(status["is_sample"])

flow = flow_selector()
word, prep = ("imports", "from") if flow == "1" else ("exports", "to")
periods = sorted(df.loc[df["freq"] == "A", "period"].unique())
period = period_slider(periods)

# Product filter: all products, or one HS2 chapter (biggest for Luxembourg first)
lu_year = df[(df["reporter"] == FOCUS) & (df["flow"] == flow) & (df["freq"] == "A") & (df["period"] == period) & (df["product"].str.len() == 2)]
chapter_weight = lu_year.groupby("product")["value"].sum().sort_values(ascending=False)
product = st.sidebar.selectbox(
    "Product",
    options=[ALL_PRODUCTS] + list(chapter_weight.index),
    format_func=lambda c: "All products" if c == ALL_PRODUCTS else f"{hs2_name(c)} ({c})",
    key="partner_product",
)
n_show = st.sidebar.slider("Partners shown", 5, 30, 15, key="partner_n")

table = partner_table(df, flow, period, product)
if table.empty:
    st.error("No bilateral rows for this selection. The processed file needs partner-level data (not only WORLD).")
    st.stop()

what = "all products" if product == ALL_PRODUCTS else f"{hs2_name(product)} ({product})"
total = float(table["value"].sum())
first = table.iloc[0]
eu_share = float(table.loc[table["is_eu"], "share"].sum())
top3 = float(table["share"].head(3).sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric(f"{word.capitalize()} {prep} named countries", fmt_eur(total))
c1.caption(f"{what} · {period}")
c2.metric("First partner", country_name(first["partner"]))
c2.caption(f"{first['share']:.0%} of {word}")
c3.metric("Top 3 partners", f"{top3:.0%}")
c3.caption("of the flow")
c4.metric("Stays in the EU", f"{eu_share:.0%}")
c4.caption("share going to EU partners" if flow == "2" else "share coming from EU partners")

st.markdown(f"#### {country_name(FOCUS)}'s {word} {prep} each country · {what} · {period}")
st.plotly_chart(partner_bars(table, flow, n=n_show), width="stretch", config={"displayModeBar": False})
runners = ", ".join(f"**{country_name(c)}** ({s:.0%})" for c, s in zip(table["partner"].iloc[1:3], table["share"].iloc[1:3]))
st.markdown(
    f"In {period}, {country_name(FOCUS)} {'bought' if flow == '1' else 'sold'} {fmt_eur(float(first['value']))} of {what} "
    f"{prep} **{country_name(first['partner'])}**, {first['share']:.0%} of its {word}{'' if product == ALL_PRODUCTS else ' of this product'}"
    + (f"; then {runners}." if runners else ".")
    + f" EU countries take {eu_share:.0%} of the total."
)
st.caption(
    f"Each bar is the value of {country_name(FOCUS)}'s {word} {prep} that country, in euros, with its share of the flow. "
    "Amber = EU member, blue = outside the EU. Shares are computed over named countries only."
)

st.divider()
st.markdown("#### How the main partners moved over time")
default_lines = list(table["partner"].head(5))
chosen = st.multiselect("Partners", options=list(table["partner"]), default=default_lines, format_func=country_name, key="partner_lines")
if chosen:
    long = partner_shares_over_time(df, flow, chosen, product)
    st.plotly_chart(partner_lines(long, chosen, flow), width="stretch", config={"displayModeBar": False})
    st.caption(f"Share of {country_name(FOCUS)}'s {word} of {what} {'coming from' if flow == '1' else 'going to'} each partner, year by year.")

st.divider()
st.markdown("#### One partner in detail: what flows between the two countries")
partner = st.selectbox(
    "Partner",
    options=list(table["partner"]),
    format_func=lambda c: f"{country_name(c)} · {table.set_index('partner').loc[c, 'share']:.0%} of {word}",
    key="partner_detail",
)
mix = partner_product_mix(df, flow, period, partner, n=10)
if mix.empty:
    st.info("No product detail for this partner.")
else:
    lead = mix.iloc[0]
    st.plotly_chart(partner_mix_bars(mix, partner, flow), width="stretch", config={"displayModeBar": False})
    st.markdown(
        f"{country_name(FOCUS)}'s {word} {prep} **{country_name(partner)}** in {period} are led by "
        f"**{hs2_name(lead['product']) if lead['product'][:1].isdigit() else lead['product']}**: "
        f"{fmt_eur(float(lead['value']))}, {lead['share']:.0%} of everything {'bought from' if flow == '1' else 'sold to'} this country."
    )

with st.expander("Method"):
    st.markdown(
        r"""
Rows with reporter = Luxembourg and a **named partner country** $p$ (Eurostat aggregates such as *World*, *EU27* and the
special codes for stores, provisions or confidential trade are dropped). For a flow (imports or exports), a year and a
product (all products, or one HS2 chapter), the share of partner $p$ is

$$w_p = \frac{v_p}{\sum_q v_q}$$

so the shares add up to 100 % over named countries. "Imports from Germany" is what **Luxembourg** declared it bought from
Germany, not what Germany declared it sold to Luxembourg; the two usually differ a little (transport costs, timing,
goods routed through a third country).
"""
    )
