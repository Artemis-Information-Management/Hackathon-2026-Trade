"""Product dimension of the Trade twins page.

Two charts that take the similarity score apart, chapter by chapter:

* ``overlap_chart``       butterfly: Luxembourg on the left, one other country on the right.
                          Amber = the part of the basket both countries share (min of the two
                          shares), grey = the part only one of them has. The amber bars add up
                          to the similarity score.
* ``twin_product_heatmap`` the same "shared part" for the closest twins side by side.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from ..config import FOCUS, country_name, hs2_name
from .theme import PALETTE, apply_theme

_GREY = "#C9CED6"


def _row_label(code: str) -> str:
    """'84' -> 'Machinery (84)'; folded rows ('Other (12)') are kept as they are."""
    return f"{hs2_name(code)} ({code})" if code[:1].isdigit() else code


def _nice_step(top: float) -> float:
    """A round tick step giving roughly 3-4 ticks per side."""
    raw = max(top, 1e-9) / 3.5
    mag = 10 ** np.floor(np.log10(raw))
    for k in (1, 2, 2.5, 5, 10):
        if raw <= k * mag:
            return float(k * mag)
    return float(10 * mag)


def overlap_chart(table: pd.DataFrame, other: str, focus: str = FOCUS, flow_label: str = "exports") -> go.Figure:
    """Butterfly chart from ``collapse_overlap(product_overlap(...))`` (shares 0-1)."""
    t = table.copy() * 100.0
    labels = [_row_label(c) for c in t.index]
    f_name, o_name = country_name(focus), country_name(other)
    only_f = (t["focus"] - t["common"]).clip(lower=0)
    only_o = (t["other"] - t["common"]).clip(lower=0)
    custom = np.column_stack([t["focus"], t["other"], t["common"]])
    hover = (
        "<b>%{y}</b><br>"
        f"{f_name}: " "%{customdata[0]:.1f} % of " f"{flow_label}<br>"
        f"{o_name}: " "%{customdata[1]:.1f} % of " f"{flow_label}<br>"
        "In common: <b>%{customdata[2]:.1f} points</b><extra></extra>"
    )

    def bars(x, color, name, group, legend, text=None):
        return go.Bar(
            y=labels, x=x, orientation="h", name=name, legendgroup=group, showlegend=legend,
            marker=dict(color=color, line=dict(width=0)), customdata=custom, hovertemplate=hover,
            text=text, textposition="outside", cliponaxis=False, textfont=dict(size=12, color=PALETTE["muted"]),
        )

    fig = go.Figure()
    # Order matters in barmode="relative": the first trace sits against the centre line.
    fig.add_trace(bars(-t["common"], PALETTE["focus"], "In common (adds up to the score)", "common", True))
    fig.add_trace(bars(-only_f, _GREY, "Only in one basket", "only", True, [f"{v:.1f} %" for v in t["focus"]]))
    fig.add_trace(bars(t["common"], PALETTE["focus"], "In common", "common", False))
    fig.add_trace(bars(only_o, _GREY, "Only in one basket", "only", False, [f"{v:.1f} %" for v in t["other"]]))

    apply_theme(fig, height=max(360, 38 * len(t) + 130))   # theme first, then our own layout

    reach = float(max(t["focus"].max(), t["other"].max()))
    step = _nice_step(reach)
    top = step * np.ceil(reach * 1.22 / step)
    ticks = np.arange(-top, top + step / 2, step)
    fig.update_xaxes(
        range=[-top, top], tickvals=ticks, ticktext=[f"{abs(v):g} %" for v in ticks],
        showgrid=True, gridcolor=PALETTE["grid"], zeroline=True, zerolinecolor=PALETTE["ink"], zerolinewidth=1,
    )
    fig.update_yaxes(autorange="reversed", showgrid=False, ticks="", automargin=True)
    fig.update_layout(
        barmode="relative", bargap=0.28, hovermode="closest",
        margin=dict(l=10, r=30, t=44, b=10),
        legend=dict(orientation="h", yanchor="top", y=-0.06, xanchor="center", x=0.5),
        annotations=[
            dict(x=0.25, y=1.0, xref="paper", yref="paper", yanchor="bottom", showarrow=False,
                 text=f"<b>{f_name}</b>", font=dict(size=15)),
            dict(x=0.75, y=1.0, xref="paper", yref="paper", yanchor="bottom", showarrow=False,
                 text=f"<b>{o_name}</b>", font=dict(size=15)),
        ],
    )
    return fig


def twin_product_heatmap(matrix: pd.DataFrame, scores: pd.Series, flow_label: str = "exports") -> go.Figure:
    """Heatmap from ``common_matrix`` (shares 0-1): rows = chapters, columns = countries."""
    z = matrix * 100.0
    names = [country_name(c) for c in matrix.columns]
    cols = [f"{n}<br><b>{scores.get(c, float('nan')) * 100:.0f} pts</b>" for n, c in zip(names, matrix.columns)]
    rows = [_row_label(c) for c in matrix.index]
    fig = go.Figure(
        go.Heatmap(
            z=z.to_numpy(), x=cols, y=rows, xgap=3, ygap=3,
            colorscale=PALETTE["sequential"], zmin=0, zmax=float(np.nanmax(z.to_numpy())) or 1.0,
            text=np.where(z.to_numpy() >= 0.05, np.round(z.to_numpy(), 1).astype(str), ""),
            texttemplate="%{text}", textfont=dict(size=12),
            customdata=np.array([[n for n in names]] * len(rows)),
            hovertemplate=(
                "<b>%{y}</b><br>%{customdata} and " + country_name(FOCUS) + " share "
                "<b>%{z:.1f} points</b><extra></extra>"
            ),
            colorbar=dict(title="points", thickness=12, len=0.7),
        )
    )
    fig.update_xaxes(side="top", showgrid=False, ticks="")
    fig.update_yaxes(autorange="reversed", showgrid=False, ticks="", automargin=True)
    apply_theme(fig, height=max(340, 36 * len(rows) + 110))
    fig.update_layout(margin=dict(l=10, r=10, t=70, b=10))
    return fig
