import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import warnings
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from lca.tech_matrix import SSP_PROPORTIONS, get_matrix_df, SCALES, LEVELS
from lca.run_lca import ALL_SSPS, ALL_YEARS

ALL_SSP_COLORS = {
    "SSP1": "#2ecc71",
    "SSP2": "#f39c12",
    "SSP3": "#e74c3c",
    "SSP4": "#9b59b6",
    "SSP5": "#1a252f",
}

st.title("LCA Analysis")
st.caption("Environmental profiles of organic waste treatment under SSP scenarios")

# --- Controls ---
col1, col2, col3 = st.columns(3)
with col1:
    selected_ssps = st.multiselect(
        "SSP Scenarios",
        ALL_SSPS,
        default=ALL_SSPS,
    )
with col2:
    selected_year = st.select_slider("Year", options=[2030, 2050, 2080, 2100], value=2030)
with col3:
    view = st.radio("View", ["Aggregate (city)", "Per cell (matrix)"], horizontal=True)

st.divider()

if not selected_ssps:
    st.info("Select at least one SSP scenario.")
    st.stop()

# --- Technology Matrix Proportions ---
st.subheader("Technology Matrix Proportions")
tabs = st.tabs(selected_ssps)
for tab, ssp in zip(tabs, selected_ssps):
    with tab:
        df = get_matrix_df(ssp)
        st.dataframe(
            df.style.background_gradient(cmap="YlOrRd", axis=None).format("{:.2f}"),
            use_container_width=True,
        )

st.divider()

# --- LCA Results ---
st.subheader("GWP Results (kg CO₂-eq / tonne OFMSW)")

@st.cache_data(show_spinner=False)
def _run_lca(ssp: str, year: int):
    from lca.run_lca import run_matrix_lca
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        df = run_matrix_lca(ssp, year)
    return df, [str(w.message) for w in caught]

def _get_results(ssp, year):
    try:
        return _run_lca(ssp, year)
    except Exception as e:
        return None, [str(e)]

all_results = {}
prospective_flags = {}
bw_available = True

with st.status("Loading LCA results from Brightway...", expanded=False) as status:
    for ssp in selected_ssps:
        df, warns = _get_results(ssp, selected_year)
        if df is None:
            bw_available = False
            st.warning(f"Brightway not available: {warns[0]}")
            break
        all_results[ssp] = df
        prospective_flags[ssp] = df["prospective"].iloc[0]
        for w in warns:
            if "not found" in w.lower():
                st.warning(w)
    status.update(
        label="LCA results loaded" if bw_available else "Using placeholder data",
        state="complete" if bw_available else "error",
    )

if bw_available:
    using_premise = any(prospective_flags.values())
    if using_premise:
        st.success("Using premise-generated prospective databases.")
    else:
        st.warning(
            "Premise databases not found for this year — using static ecoinvent 3.9.1. "
            "Run `prospective/generate_prospective_dbs.ipynb` to generate them."
        )
else:
    st.info("Brightway unavailable — showing placeholder data for layout preview.")

# Placeholder fallback
PLACEHOLDER_BASE = {"SSP1": 30, "SSP2": 45, "SSP3": 65, "SSP4": 55, "SSP5": 70}
PLACEHOLDER = {
    ssp: {
        f"{scale}/{level}": PLACEHOLDER_BASE[ssp] * (1 + 0.1 * i)
        for i, (scale, level) in enumerate(
            (s, l) for s in SCALES for l in LEVELS
        )
    }
    for ssp in ALL_SSPS
}

def _cell_gwp(ssp, scale, level):
    if ssp in all_results:
        row = all_results[ssp]
        match = row[(row["scale"] == scale) & (row["level"] == level)]
        if not match.empty:
            return float(match["gwp"].iloc[0])
    return PLACEHOLDER[ssp][f"{scale}/{level}"]

if view == "Per cell (matrix)":
    for ssp in selected_ssps:
        z = [[_cell_gwp(ssp, scale, level) for level in LEVELS] for scale in SCALES]
        fig = go.Figure(go.Heatmap(
            z=z, x=LEVELS, y=SCALES,
            colorscale="RdYlGn_r",
            text=[[f"{v:.1f}" for v in row] for row in z],
            texttemplate="%{text}",
            showscale=True,
            colorbar=dict(title="kg CO₂-eq/t"),
        ))
        fig.update_layout(
            title=f"{ssp} — GWP per cell ({selected_year})",
            xaxis_title="Technology Level",
            height=300,
            margin=dict(l=0, r=0, t=40, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

else:
    rows = []
    for ssp in selected_ssps:
        props = SSP_PROPORTIONS[ssp]
        weighted = sum(
            props[scale][level] * _cell_gwp(ssp, scale, level)
            for scale in SCALES for level in LEVELS
        )
        rows.append({"SSP": ssp, "Year": selected_year, "GWP (kg CO₂-eq/t)": round(weighted, 1)})

    df_agg = pd.DataFrame(rows)
    color_map = {ssp: ALL_SSP_COLORS[ssp] for ssp in selected_ssps}
    fig = px.bar(
        df_agg, x="SSP", y="GWP (kg CO₂-eq/t)", color="SSP",
        color_discrete_map=color_map,
        text_auto=True, height=400,
        title=f"Aggregate GWP by SSP — Montreal {selected_year}",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False, yaxis_title="kg CO₂-eq / tonne OFMSW")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df_agg, use_container_width=True, hide_index=True)
