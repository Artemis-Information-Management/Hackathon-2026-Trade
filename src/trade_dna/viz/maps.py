"""Choropleth of Europe: how similar is each country to Luxembourg?"""

from __future__ import annotations

import pandas as pd
import plotly.express as px

from ..config import FOCUS, ISO2_TO_ISO3, country_name
from .theme import PALETTE, apply_theme


def similarity_map(sim_long: pd.DataFrame, period: str, focus: str = FOCUS, title: str | None = None):
    sub = sim_long[sim_long["period"] == period].copy()
    sub = sub[sub["reporter"] != focus]
    sub["iso3"] = sub["reporter"].map(ISO2_TO_ISO3)
    sub["country"] = sub["reporter"].map(country_name)
    sub = sub.dropna(subset=["iso3"])

    fig = px.choropleth(
        sub,
        locations="iso3",
        color="fk",
        hover_name="country",
        hover_data={"fk": ":.2f", "iso3": False},
        color_continuous_scale=PALETTE["sequential"],
        range_color=(0, 1),
        scope="europe",
        labels={"fk": "Similarity"},
        title=title or f"Trade-profile similarity with {country_name(focus)} - {period}",
    )
    # Outline the focus country so the eye finds it immediately
    fig.add_scattergeo(
        locations=[ISO2_TO_ISO3[focus]],
        locationmode="ISO-3",
        marker=dict(size=14, color=PALETTE["focus"], line=dict(width=2, color=PALETTE["ink"])),
        name=country_name(focus),
        hoverinfo="name",
    )
    fig.update_geos(
        showcountries=True,
        countrycolor="#B8BEC6",
        showcoastlines=False,
        showframe=False,
        projection_type="natural earth",
        lataxis_range=[34, 71],
        lonaxis_range=[-25, 40],
    )
    fig.update_layout(coloraxis_colorbar=dict(title="FK index", thickness=12, len=0.6))
    return apply_theme(fig, height=520)
