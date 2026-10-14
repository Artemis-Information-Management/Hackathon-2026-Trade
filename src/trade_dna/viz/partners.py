"""Charts of Luxembourg's bilateral flows (lens 5).

* ``partner_bars``   ranked partner countries for one flow / year / product, in euros.
                     Amber = EU partner, blue = outside the EU. Share labels on the bars.
* ``partner_lines``  how the share of the main partners moved over the years.
* ``partner_mix_bars`` what flows between Luxembourg and ONE partner, by HS2 chapter.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from ..config import FOCUS, country_name, hs2_name
from .theme import PALETTE, apply_theme
from .timeseries import _add_events, _x

_EU, _NON_EU = PALETTE["focus"], PALETTE["categorical"][1]


def _eur(v: float) -> str:
    if v >= 1e9:
        return f"{v / 1e9:,.1f} bn €"
    if v >= 1e6:
        return f"{v / 1e6:,.0f} M €"
    return f"{v:,.0f} €"


def _flow_words(flow: str) -> tuple[str, str]:
    """('imports', 'from') or ('exports', 'to')."""
    return ("imports", "from") if flow == "1" else ("exports", "to")


def partner_bars(table: pd.DataFrame, flow: str, n: int = 15, focus: str = FOCUS) -> go.Figure:
    """Horizontal ranked bars from ``partner_table`` (value in EUR, share 0-1)."""
    t = table.head(n)
    word, prep = _flow_words(flow)
    labels = [f"{i}. {country_name(c)}" for i, c in enumerate(t["partner"], start=1)]
    colors = np.where(t["is_eu"], _EU, _NON_EU)
    fig = go.Figure()
    for is_eu, name in ((True, "EU partner"), (False, "Outside the EU")):
        mask = t["is_eu"] == is_eu
        if not mask.any():
            continue
        fig.add_bar(
            y=[lab for lab, m in zip(labels, mask) if m], x=t.loc[mask, "value"], orientation="h", name=name,
            marker=dict(color=_EU if is_eu else _NON_EU, line=dict(width=0)),
            text=[f"{s:.1%}" for s in t.loc[mask, "share"]], textposition="outside", cliponaxis=False,
            textfont=dict(size=12, color=PALETTE["ink"]),
            customdata=np.column_stack([t.loc[mask, "value"].map(_eur), t.loc[mask, "share"] * 100]),
            hovertemplate=(
                "<b>%{y}</b><br>" f"{country_name(focus)}'s {word} {prep} this country: "
                "<b>%{customdata[0]}</b><br>%{customdata[1]:.1f} % of all " f"{word}<extra></extra>"
            ),
        )
    apply_theme(fig, height=max(320, 30 * len(t) + 120))
    top = float(t["value"].max()) * 1.18 if len(t) else 1.0
    fig.update_xaxes(range=[0, top], showgrid=True, gridcolor=PALETTE["grid"], zeroline=False,
                     tickprefix="", ticksuffix="", tickformat="~s", title_text="euros")
    fig.update_yaxes(categoryorder="array", categoryarray=labels, autorange="reversed",
                     showgrid=False, ticks="", automargin=True, ticklabelstandoff=8)
    fig.update_layout(bargap=0.3, hovermode="closest", showlegend=True,
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0),
                      margin=dict(l=10, r=60, t=40, b=10))
    return fig


def partner_lines(long: pd.DataFrame, partners: list[str], flow: str, focus: str = FOCUS) -> go.Figure:
    """Share of each chosen partner over time, from ``partner_shares_over_time``."""
    word, prep = _flow_words(flow)
    fig = go.Figure()
    periods = sorted(long["period"].unique())
    for i, p in enumerate(partners):
        s = long[long["partner"] == p].sort_values("period")
        if s.empty:
            continue
        fig.add_scatter(
            x=_x(s["period"]), y=s["share"], mode="lines+markers", name=country_name(p),
            line=dict(width=2, color=PALETTE["categorical"][i % len(PALETTE["categorical"])]), marker=dict(size=5),
            customdata=s["value"].map(_eur),
            hovertemplate="%{x}: %{y:.1%} (%{customdata})<extra>" + country_name(p) + "</extra>",
        )
    _add_events(fig, periods)
    fig.update_layout(title=f"Share of {country_name(focus)}'s {word} {prep} each partner, over time",
                      yaxis_title=f"% of {word}", yaxis_tickformat=".0%", yaxis_rangemode="tozero")
    return apply_theme(fig)


def partner_mix_bars(mix: pd.DataFrame, partner: str, flow: str, focus: str = FOCUS) -> go.Figure:
    """Horizontal bars from ``partner_product_mix`` (one partner, by HS2 chapter)."""
    word, prep = _flow_words(flow)
    labels = [f"{hs2_name(c)} ({c})" if c[:1].isdigit() else c for c in mix["product"]]
    fig = go.Figure(
        go.Bar(
            y=labels, x=mix["value"], orientation="h", marker=dict(color=PALETTE["focus"], line=dict(width=0)),
            text=[f"{s:.1%}" for s in mix["share"]], textposition="outside", cliponaxis=False,
            textfont=dict(size=12, color=PALETTE["ink"]),
            customdata=np.column_stack([mix["value"].map(_eur), mix["share"] * 100]),
            hovertemplate=(
                "<b>%{y}</b><br>" f"{country_name(focus)}'s {word} {prep} {country_name(partner)}: "
                "<b>%{customdata[0]}</b><br>%{customdata[1]:.1f} % of the flow<extra></extra>"
            ),
        )
    )
    apply_theme(fig, height=max(300, 30 * len(mix) + 110))
    top = float(mix["value"].max()) * 1.18 if len(mix) else 1.0
    fig.update_xaxes(range=[0, top], showgrid=True, gridcolor=PALETTE["grid"], zeroline=False, tickformat="~s", title_text="euros")
    fig.update_yaxes(autorange="reversed", showgrid=False, ticks="", automargin=True, ticklabelstandoff=8)
    fig.update_layout(bargap=0.3, hovermode="closest", margin=dict(l=10, r=60, t=20, b=10))
    return fig
