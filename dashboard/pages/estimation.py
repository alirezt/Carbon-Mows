import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from estimation.montreal import load_population, estimate_waste

st.title("Waste Estimation — Montreal")
st.caption("SSP-based organic waste projections at ADA level (246 dissemination areas)")

# --- Controls ---
col1, col2 = st.columns(2)
with col1:
    selected_ssps = st.multiselect("SSP Scenarios", ["SSP1", "SSP2", "SSP3"], default=["SSP1", "SSP2", "SSP3"])
with col2:
    selected_years = st.multiselect("Years", [2020, 2025, 2030, 2035, 2040, 2045, 2050], default=[2020, 2030, 2040, 2050])

st.divider()

if not selected_ssps or not selected_years:
    st.info("Select at least one SSP and one year.")
    st.stop()

pop_df = load_population()
waste_df = estimate_waste(pop_df)

# City-level totals
city = (
    waste_df[waste_df["ssp"].isin(selected_ssps) & waste_df["year"].isin(selected_years)]
    .groupby(["ssp", "year"])[["population", "waste_tonnes"]]
    .sum()
    .reset_index()
)

st.subheader("City-level organic waste projection")
fig = px.line(
    city, x="year", y="waste_tonnes", color="ssp",
    markers=True,
    color_discrete_map={"SSP1": "#2ecc71", "SSP2": "#f39c12", "SSP3": "#e74c3c"},
    labels={"waste_tonnes": "Organic Waste (tonnes/yr)", "year": "Year", "ssp": "Scenario"},
    title="Montreal Agglomeration — Organic Waste by SSP",
    height=420,
)
fig.update_layout(hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Summary table")
pivot = city.pivot_table(index="year", columns="ssp", values="waste_tonnes").round(0)
st.dataframe(pivot.style.format("{:,.0f}"), use_container_width=True)

st.divider()

st.subheader("ADA-level distribution")
selected_ssp_map = st.selectbox("SSP for map view", selected_ssps)
selected_year_map = st.select_slider("Year for map view", options=sorted(selected_years))

ada_data = waste_df[
    (waste_df["ssp"] == selected_ssp_map) & (waste_df["year"] == selected_year_map)
].copy()

fig2 = px.histogram(
    ada_data, x="waste_tonnes", nbins=30,
    title=f"ADA waste distribution — {selected_ssp_map} {selected_year_map}",
    labels={"waste_tonnes": "Waste per ADA (tonnes/yr)"},
    height=350,
)
st.plotly_chart(fig2, use_container_width=True)

col1, col2, col3 = st.columns(3)
col1.metric("Total waste (tonnes/yr)", f"{ada_data['waste_tonnes'].sum():,.0f}")
col2.metric("ADAs covered", f"{ada_data['DGUID'].nunique()}")
col3.metric("Avg per ADA (tonnes/yr)", f"{ada_data['waste_tonnes'].mean():,.0f}")
