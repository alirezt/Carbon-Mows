import streamlit as st
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from lca.tech_matrix import TECH_MATRIX, SSP_PROPORTIONS, get_matrix_df

st.title("Technology Matrix")
st.caption("3×3 matrix of organic waste treatment options by scale and technology level")

SCALES = ["Domestic", "Local", "Centralized"]
LEVELS = ["Low", "Medium", "High"]

# --- Matrix definition table ---
st.subheader("Facility mapping")
rows = []
for scale in SCALES:
    for level in LEVELS:
        cell = TECH_MATRIX[scale][level]
        rows.append({
            "Scale": scale,
            "Tech Level": level,
            "Representative Facility": cell["facility"],
            "Status": cell["status"],
            "Brightway Dataset": cell["dataset"],
        })

import pandas as pd
df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()

# --- SSP proportion heatmaps ---
st.subheader("SSP proportions (initial conditions)")
st.caption("Proportion of total organic waste stream allocated to each cell. Sums to 1.0 per scenario.")

cols = st.columns(3)
for col, ssp in zip(cols, ["SSP1", "SSP2", "SSP3"]):
    with col:
        props = SSP_PROPORTIONS[ssp]
        z = [[props[scale][level] for level in LEVELS] for scale in SCALES]
        total = sum(v for row in z for v in row)

        fig = go.Figure(go.Heatmap(
            z=z, x=LEVELS, y=SCALES,
            colorscale="YlOrRd",
            zmin=0, zmax=0.35,
            text=[[f"{v:.2f}" for v in row] for row in z],
            texttemplate="%{text}",
            showscale=False,
        ))
        fig.update_layout(
            title=f"{ssp} (Σ={total:.2f})",
            xaxis_title="Technology Level",
            yaxis_title="",
            height=300,
            margin=dict(l=0, r=0, t=40, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- SSP narrative ---
st.subheader("Scenario rationale")
st.markdown("""
| Scenario | Narrative | Infrastructure tendency |
|---|---|---|
| **SSP1** | Sustainability — high governance, green investment | Decentralized, high-tech, near-zero landfill |
| **SSP2** | Middle of the road — current trends continue | Mostly centralized, moderate shift away from landfill |
| **SSP3** | Regional rivalry — fragmented governance, low investment | Centralized low-tech, high landfill share |

*Cell proportions are initial conditions fed into the system dynamics model, where they evolve via feedback mechanisms (infrastructure capacity, policy investment, participation rates).*
""")
