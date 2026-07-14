import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from src import loaders, figures
from src.constants import UNIT_ABBR, DECENTRALIZATION_OPTIONS, LU_MOBILITY_OPTIONS

st.set_page_config(page_title="Montreal Organic Waste Dashboard", layout="wide")


@st.cache_resource
def get_static_data():
    return dict(
        admin_units=loaders.load_admin_units(),
        parcels=loaders.load_parcels_by_unit(),
        landuse=loaders.load_landuse_by_unit(),
        density=loaders.load_density_by_unit(),
        gardens=loaders.load_gardens(),
        ecocenters=loaders.load_ecocenters(),
    )


@st.cache_data
def get_tabular_data():
    return dict(
        population=loaders.load_population(),
        historical_population=loaders.load_historical_population(),
        mariane_annual=loaders.load_mariane_annual(),
        bilan_agglo=loaders.load_bilan_massique_agglo(),
        bilan_by_unit=loaders.load_bilan_massique_by_unit(),
    )


data = get_static_data()
tabular = get_tabular_data()
population_df = tabular["population"]
historical_df = tabular["historical_population"]
mariane_annual = tabular["mariane_annual"]
bilan_agglo = tabular["bilan_agglo"]
bilan_by_unit = tabular["bilan_by_unit"]
admin_units = data["admin_units"]

abbr_to_unit = {UNIT_ABBR.get(u["Name"], u["Code"]): (u["Level"], u["Code"], u["Name"]) for u in admin_units}
sorted_abbrs = sorted(abbr_to_unit, key=lambda a: (abbr_to_unit[a][0], abbr_to_unit[a][2]))

st.title("Montreal Organic Waste Dashboard")

row1_left, row1_right = st.columns([3, 1])

with row1_right:
    with st.container(border=True):
        st.subheader("Select area")
        selected_abbr = st.selectbox("Borough/Municipality", sorted_abbrs, index=sorted_abbrs.index("CN") if "CN" in sorted_abbrs else 0)
        sel_level, sel_code, sel_name = abbr_to_unit[selected_abbr]
        st.caption(f"**{sel_name}** ({sel_level})")
        st.selectbox("Spatial scenario", DECENTRALIZATION_OPTIONS)
        st.selectbox("2050 Land Use and Mobility Plan", LU_MOBILITY_OPTIONS)
        st.caption("Illustrative selectors — not yet linked to data.")

    with st.container(border=True):
        agglo_pop = population_df.groupby(["Scenario", "Year"], as_index=False)["Population"].sum()
        fig = figures.population_timeseries(agglo_pop, None, "Montreal")
        st.plotly_chart(fig, use_container_width=True)

    with st.container(border=True):
        agglo_mariane = mariane_annual.groupby(["Year", "Matière corrigé"], as_index=False)["Net"].sum()
        fig = figures.waste_timeseries_annual(agglo_mariane, bilan_agglo, "Montreal")
        st.plotly_chart(fig, use_container_width=True)

with row1_left:
    with st.container(border=True):
        fig = figures.overview_map(admin_units, data["gardens"], selected_unit=(sel_level, sel_code))
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

col2a, col2b = st.columns(2)

with col2a:
    with st.container(border=True):
        pop_row = population_df[
            (population_df["Level"] == sel_level) & (population_df["Code"] == sel_code) &
            (population_df["Year"] == 2025) & (population_df["Scenario"].str.startswith("Référence"))
        ]
        pop_value = pop_row["Population"].iloc[0] if not pop_row.empty else None
        unit = next(u for u in admin_units if (u["Level"], u["Code"]) == (sel_level, sel_code))
        gardens_here = [g for g in data["gardens"] if g["unit"] == (sel_level, sel_code)]
        eco_here = [e for e in data["ecocenters"] if e["unit"] == (sel_level, sel_code)]
        parcels_here = data["parcels"].get((sel_level, sel_code), [])
        fig = figures.population_parcels_map(unit["geom"], parcels_here, gardens_here, eco_here, pop_value, selected_abbr)
        st.plotly_chart(fig, use_container_width=True)

with col2b:
    with st.container(border=True):
        lu_here = data["landuse"].get((sel_level, sel_code), [])
        dens_here = data["density"].get((sel_level, sel_code), [])
        fig = figures.landuse_density_map(lu_here, dens_here, unit["geom"], selected_abbr)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

col3a, col3b = st.columns(2)

with col3a:
    with st.container(border=True):
        borough_pop = population_df[
            (population_df["Level"] == sel_level) & (population_df["Code"] == sel_code)
        ][["Scenario", "Year", "Population"]]
        borough_hist = historical_df[historical_df["unit"] == (sel_level, sel_code)]
        fig = figures.population_timeseries(borough_pop, borough_hist, selected_abbr)
        st.plotly_chart(fig, use_container_width=True)

with col3b:
    with st.container(border=True):
        borough_mariane = mariane_annual[mariane_annual["unit"] == (sel_level, sel_code)]
        borough_bilan = bilan_by_unit[bilan_by_unit["unit"] == (sel_level, sel_code)]
        fig = figures.waste_timeseries_annual(borough_mariane, borough_bilan, selected_abbr)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
footnote = " · ".join(f"**{a}** {abbr_to_unit[a][2]}" for a in sorted(abbr_to_unit))
st.caption(f"Abbreviations: {footnote}")
