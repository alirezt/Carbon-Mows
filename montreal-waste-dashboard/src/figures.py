import numpy as np
import plotly.graph_objects as go
from src.geo_utils import extract_rings, polygons_to_xy, bounds_of_rings
from src.constants import (
    UNIT_ABBR, TYPE_COLORS, MATIERE_EN, AFFECTATIO_COLORS, DENSITE_COLORS,
    PARCEL_UNITS_BINS, PARCEL_UNITS_COLORS, parcel_units_bin,
    SCENARIO_EN, SCENARIO_COLORS, HISTORICAL_POP_COLOR,
    MARIANE_MATERIAL_COLORS, BILAN_MASSIQUE_COLOR,
)

BASE_LAYOUT = dict(
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=10, r=10, t=40, b=10),
    font=dict(color="#0b0b0b"),
)


def _map_axes(fig, bounds):
    xmin, xmax, ymin, ymax = bounds
    fig.update_xaxes(range=[xmin, xmax], visible=False)
    fig.update_yaxes(range=[ymin, ymax], visible=False, scaleanchor="x", scaleratio=1)


def overview_map(admin_units, gardens, selected_unit=None):
    fig = go.Figure()
    for u in admin_units:
        rings = list(extract_rings(u["geom"]))
        xs, ys = polygons_to_xy(rings)
        is_selected = selected_unit is not None and (u["Level"], u["Code"]) == selected_unit
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines", fill="toself",
            fillcolor=TYPE_COLORS[u["Level"]], opacity=1.0,
            line=dict(color="#e34948" if is_selected else "black", width=3.5 if is_selected else 0.8),
            name=u["Level"], legendgroup=u["Level"], showlegend=False,
            hovertext=u["Name"], hoverinfo="text",
        ))
        c = u["geom"].representative_point()
        fig.add_trace(go.Scatter(
            x=[c.x], y=[c.y], mode="text", text=[UNIT_ABBR.get(u["Name"], "?")],
            textfont=dict(size=10, color="white"), showlegend=False, hoverinfo="skip",
        ))

    for lvl, color in TYPE_COLORS.items():
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                                  marker=dict(size=12, color=color), name=lvl))

    if gardens:
        areas = np.array([g["area_m2"] for g in gardens])
        sizes = 6 + 18 * (areas - areas.min()) / max(areas.max() - areas.min(), 1)
        fig.add_trace(go.Scatter(
            x=[g["x"] for g in gardens], y=[g["y"] for g in gardens], mode="markers",
            marker=dict(size=sizes, color="black", opacity=0.65),
            name="Community garden", hovertext=[g["name"] for g in gardens], hoverinfo="text",
        ))

    bounds = bounds_of_rings([pt for u in admin_units for pt in extract_rings(u["geom"])])
    _map_axes(fig, bounds)
    layout = {**BASE_LAYOUT, "margin": dict(l=10, r=10, t=110, b=10)}
    fig.update_layout(**layout, height=850,
                       title=dict(text="Montreal Agglomeration", y=0.97, yanchor="top"),
                       legend=dict(orientation="h", yanchor="top", y=0.90, x=0, xanchor="left", font=dict(size=14)))
    return fig


def population_timeseries(scenario_df, historical_df, label):
    fig = go.Figure()
    has_hist = historical_df is not None and not historical_df.empty
    if has_hist:
        hist = historical_df.sort_values("year")
        fig.add_trace(go.Scatter(x=hist["year"], y=hist["population"], mode="lines",
                                  line=dict(color=HISTORICAL_POP_COLOR, width=2), name="Historical (Census)"))
    for scen, color in SCENARIO_COLORS.items():
        sub = scenario_df[scenario_df["Scenario"] == scen].sort_values("Year")
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(x=sub["Year"], y=sub["Population"], mode="lines",
                                  line=dict(color=color, width=2), name=SCENARIO_EN.get(scen, scen)))
    span = "1981-2041" if has_hist else "2021-2041"
    fig.update_yaxes(title="Population")
    fig.update_layout(**BASE_LAYOUT, height=300,
                       title=dict(text=f"{label} — Population ({span})", font=dict(size=13)),
                       legend=dict(font=dict(size=9)))
    return fig


def waste_timeseries_annual(mariane_df, bilan_df, label):
    fig = go.Figure()
    has_data = False
    for material, color in MARIANE_MATERIAL_COLORS.items():
        sub = mariane_df[mariane_df["Matière corrigé"] == material].sort_values("Year")
        if sub.empty:
            continue
        has_data = True
        fig.add_trace(go.Scatter(x=sub["Year"], y=sub["Net"], mode="lines+markers",
                                  line=dict(color=color, width=2),
                                  name=f"{MATIERE_EN.get(material, material)} (Mariane)"))
    if bilan_df is not None and not bilan_df.empty:
        sub = bilan_df.sort_values("year")
        has_data = True
        fig.add_trace(go.Scatter(x=sub["year"], y=sub["collected"], mode="lines+markers",
                                  line=dict(color=BILAN_MASSIQUE_COLOR, width=2, dash="dash"),
                                  name="Organic matter (Données Québec)"))
    if not has_data:
        fig.add_annotation(text="No waste data available for this unit", showarrow=False,
                            font=dict(size=14, color="#898781"))
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
    else:
        fig.update_yaxes(title="Tonnes/year")
        fig.update_xaxes(title="Year")
    fig.update_layout(**BASE_LAYOUT, height=300,
                       title=dict(text=f"{label} — Organic/Food Waste (Annual)", font=dict(size=13)),
                       legend=dict(font=dict(size=9)), showlegend=has_data)
    return fig


def population_parcels_map(unit_geom, parcels, gardens_for_unit, ecocenters_for_unit, population_value, unit_label):
    fig = go.Figure()
    by_bin = {}
    for p in parcels:
        by_bin.setdefault(parcel_units_bin(p["units"]), []).append(p["points"])
    for _, _, label in PARCEL_UNITS_BINS:
        rings = by_bin.get(label)
        if not rings:
            continue
        xs, ys = polygons_to_xy(rings)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", fill="toself",
                                  fillcolor=PARCEL_UNITS_COLORS[label], opacity=0.9,
                                  line=dict(color="#7a7a7a", width=0.2),
                                  name=label, legendgroup="parcels"))

    rings = list(extract_rings(unit_geom))
    xs, ys = polygons_to_xy(rings)
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="black", width=2.5),
                              showlegend=False, hoverinfo="skip"))

    if ecocenters_for_unit:
        fig.add_trace(go.Scatter(
            x=[e["x"] for e in ecocenters_for_unit], y=[e["y"] for e in ecocenters_for_unit], mode="markers",
            marker=dict(size=14, color="#e34948", symbol="square"), name="Ecocenter",
            hovertext=[e["name"] for e in ecocenters_for_unit], hoverinfo="text",
        ))
    if gardens_for_unit:
        fig.add_trace(go.Scatter(
            x=[g["x"] for g in gardens_for_unit], y=[g["y"] for g in gardens_for_unit], mode="markers",
            marker=dict(size=10, color="#1baf7a", symbol="circle"), name="Community garden",
            hovertext=[g["name"] for g in gardens_for_unit], hoverinfo="text",
        ))

    bounds = bounds_of_rings(rings)
    _map_axes(fig, bounds)
    pop_str = f"{population_value:,.0f}" if population_value is not None else "N/A"
    fig.update_layout(**BASE_LAYOUT, height=460,
                       title=f"{unit_label} — Population: {pop_str} (parcels colored by residential units/lot)",
                       legend=dict(font=dict(size=9)))
    return fig


def landuse_density_map(landuse_fragments, density_fragments, unit_geom, unit_label):
    fig = go.Figure()
    by_cat = {}
    for frag in landuse_fragments:
        by_cat.setdefault(frag["attr"], []).extend(extract_rings(frag["geom"]))
    for cat, rings in by_cat.items():
        xs, ys = polygons_to_xy(rings)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", fill="toself",
                                  fillcolor=AFFECTATIO_COLORS.get(cat, "#c3c2b7"), opacity=0.85,
                                  line=dict(width=0), name=cat, legendgroup="landuse"))

    by_dens = {}
    for frag in density_fragments:
        by_dens.setdefault(frag["attr"], []).extend(extract_rings(frag["geom"]))
    for dens, rings in sorted(by_dens.items(), key=lambda x: float(x[0])):
        xs, ys = polygons_to_xy(rings)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", fill="toself",
                                  fillcolor=DENSITE_COLORS.get(dens, "#7250c4"), opacity=0.5,
                                  line=dict(color=DENSITE_COLORS.get(dens, "#7250c4"), width=1),
                                  name=f"Density {dens}", legendgroup="density"))

    rings = list(extract_rings(unit_geom))
    xs, ys = polygons_to_xy(rings)
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="black", width=2.5),
                              showlegend=False, hoverinfo="skip"))

    bounds = bounds_of_rings(rings)
    _map_axes(fig, bounds)
    fig.update_layout(**BASE_LAYOUT, height=460, title=f"{unit_label} — Land Use & Residential Density",
                       legend=dict(font=dict(size=9)))
    return fig
