"""Line charts over time, with Luxembourg (or the chosen focus) always highlighted."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from ..config import FOCUS, country_name, hs2_label
from .theme import PALETTE, apply_theme

# Events worth annotating on any Luxembourg trade series
EVENTS = {
    "2008": "Financial crisis",
    "2016": "Brexit vote",
    "2020": "Covid-19",
    "2022": "Energy price shock",
}


def _add_events(fig: go.Figure, periods: list[str]) -> None:
    for year, label in EVENTS.items():
        if year in periods:
            fig.add_vline(x=year, line_width=1, line_dash="dot", line_color=PALETTE["muted"])
            fig.add_annotation(x=year, y=1.0, yref="paper", text=label, showarrow=False, font=dict(size=10, color=PALETTE["muted"]), yanchor="bottom")


def similarity_lines(sim_long: pd.DataFrame, reporters: list[str], focus: str = FOCUS) -> go.Figure:
    fig = go.Figure()
    periods = sorted(sim_long["period"].unique())
    for i, rep in enumerate(reporters):
        if rep == focus:
            continue
        s = sim_long[sim_long["reporter"] == rep].sort_values("period")
        fig.add_scatter(
            x=s["period"], y=s["fk"], mode="lines+markers", name=country_name(rep),
            line=dict(width=2, color=PALETTE["categorical"][i % len(PALETTE["categorical"])]),
            marker=dict(size=5),
            hovertemplate="%{x}: %{y:.2f}<extra>" + country_name(rep) + "</extra>",
        )
    _add_events(fig, periods)
    fig.update_layout(title=f"Similarity with {country_name(focus)} over time", yaxis_title="Finger-Kreinin index", yaxis_range=[0, 1])
    return apply_theme(fig)


def hhi_lines(hhi_long: pd.DataFrame, products: list[str]) -> go.Figure:
    fig = go.Figure()
    periods = sorted(hhi_long["period"].unique())
    for i, p in enumerate(products):
        s = hhi_long[hhi_long["product"] == p].sort_values("period")
        fig.add_scatter(
            x=s["period"], y=s["hhi"], mode="lines+markers", name=hs2_label(p),
            line=dict(width=2, color=PALETTE["categorical"][i % len(PALETTE["categorical"])]),
            marker=dict(size=5),
            customdata=s[["top_partner", "top_share"]],
            hovertemplate="%{x}: HHI %{y:.2f}<br>Top partner %{customdata[0]} (%{customdata[1]:.0%})<extra>" + hs2_label(p) + "</extra>",
        )
    for y, label in ((0.15, "diversified"), (0.25, "concentrated")):
        fig.add_hline(y=y, line_width=1, line_dash="dash", line_color=PALETTE["muted"], annotation_text=label, annotation_position="right")
    _add_events(fig, periods)
    fig.update_layout(title="Partner concentration by product", yaxis_title="HHI (0 = spread, 1 = single partner)", yaxis_range=[0, 1])
    return apply_theme(fig)


def seasonal_heatmap(fingerprint: pd.DataFrame) -> go.Figure:
    """Rows = series, columns = month (01..12), values = seasonal share of trend."""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    cols = [c for c in sorted(fingerprint.columns)]
    fig = go.Figure(
        go.Heatmap(
            z=fingerprint[cols].values,
            x=[months[int(c) - 1] for c in cols],
            y=list(fingerprint.index),
            colorscale="RdBu",
            reversescale=True,
            zmid=0,
            zmin=-0.3,
            zmax=0.3,
            colorbar=dict(title="% of trend", tickformat=".0%", thickness=12),
            hovertemplate="%{y}<br>%{x}: %{z:+.1%}<extra></extra>",
        )
    )
    fig.update_layout(title="", yaxis=dict(autorange="reversed"))
    return apply_theme(fig, height=120 + 36 * len(fingerprint))


def decomposition_chart(decomp: pd.DataFrame, title: str = "Seasonal decomposition") -> go.Figure:
    """Expects columns period, value, trend, seasonal, remainder (one series)."""
    fig = go.Figure()
    d = decomp.sort_values("period")
    fig.add_scatter(x=d["period"], y=d["value"], name="Observed", line=dict(color=PALETTE["muted"], width=1.5))
    fig.add_scatter(x=d["period"], y=d["trend"], name="Trend (deseasonalised)", line=dict(color=PALETTE["focus"], width=3))
    fig.add_bar(x=d["period"], y=d["seasonal"], name="Seasonal component", marker_color=PALETTE["categorical"][1], opacity=0.5, yaxis="y2")
    fig.update_layout(
        title=title,
        yaxis_title="EUR",
        yaxis2=dict(overlaying="y", side="right", showgrid=False, title="Seasonal"),
        barmode="overlay",
    )
    return apply_theme(fig, height=460)
