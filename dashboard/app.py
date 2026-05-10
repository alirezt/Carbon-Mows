import streamlit as st

st.set_page_config(
    page_title="Carbon-Mows",
    page_icon="♻",
    layout="wide",
)

pg = st.navigation([
    st.Page("pages/lca.py",        title="LCA Analysis",       icon="🧪"),
    st.Page("pages/estimation.py", title="Waste Estimation",   icon="📊"),
    st.Page("pages/matrix.py",     title="Technology Matrix",  icon="⚙️"),
])

pg.run()
