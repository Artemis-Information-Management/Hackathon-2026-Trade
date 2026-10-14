"""One look for every chart: a restrained palette and a shared layout."""

from __future__ import annotations

import plotly.graph_objects as go

# Luxembourg always gets the accent; comparison countries get muted tones.
PALETTE = {
    "focus": "#E4A11B",       # warm amber, matches the STATEC hackathon visuals
    "ink": "#1F2328",
    "muted": "#8B949E",
    "grid": "#E6E8EB",
    "sequential": "YlOrBr",   # for maps: low = pale, high = deep amber
    "categorical": ["#E4A11B", "#3B6EA5", "#6A9F58", "#B5534C", "#7A5C99", "#4FA3A5", "#A26A3F", "#5E6B7A"],
}


def apply_theme(fig: go.Figure, height: int = 420) -> go.Figure:
    # The legend sits just above the plot: leave room for a title above it
    top = 72 if fig.layout.title.text else 40
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=10, r=10, t=top, b=10),
        font=dict(family="Inter, Segoe UI, sans-serif", color=PALETTE["ink"], size=13),
        colorway=PALETTE["categorical"],
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hoverlabel=dict(bgcolor="white"),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor=PALETTE["grid"], zeroline=False)
    return fig
