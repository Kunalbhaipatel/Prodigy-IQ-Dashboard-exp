
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# ------------------------- STYLING -------------------------
def load_styles():
    st.markdown("""<style>
    div[data-testid="metric-container"] {
        background-color: #fff;
        padding: 1.2em;
        border-radius: 15px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1);
        margin: 0.5em;
        text-align: center;
    }
    </style>""", unsafe_allow_html=True)

# ------------------------- FILTERS -------------------------
def apply_shared_filters(df):
    search_term = st.sidebar.text_input("🔍 Search Anything").lower()
    filtered = df.copy()

    if search_term:
        filtered = filtered[filtered.apply(lambda row: row.astype(str).str.lower().str.contains(search_term).any(), axis=1)]

    for col in ["Operator", "Contractor", "flowline_Shakers", "Hole_Size"]:
        options = sorted(filtered[col].dropna().astype(str).unique().tolist())
        selected = st.sidebar.selectbox(col, ["All"] + options, key=col)
        if selected != "All":
            filtered = filtered[filtered[col].astype(str) == selected]

    filtered["TD_Date"] = pd.to_datetime(filtered["TD_Date"], errors="coerce")
    year_range = st.sidebar.slider("TD Date Range", 2020, 2026, (2020, 2026))
    filtered = filtered[(filtered["TD_Date"].dt.year >= year_range[0]) & (filtered["TD_Date"].dt.year <= year_range[1])]

    depth_bins = {
        "<5000 ft": (0, 5000), "5000–10000 ft": (5000, 10000),
        "10000–15000 ft": (10000, 15000), "15000–20000 ft": (15000, 20000),
        "20000–25000 ft": (20000, 25000), ">25000 ft": (25000, float("inf"))
    }
    selected_depth = st.sidebar.selectbox("Depth", ["All"] + list(depth_bins.keys()))
    if selected_depth != "All":
        low, high = depth_bins[selected_depth]
        filtered = filtered[(filtered["MD Depth"] >= low) & (filtered["MD Depth"] < high)]

    mw_bins = {
        "<3": (0, 3), "3–6": (3, 6), "6–9": (6, 9),
        "9–11": (9, 11), "11–14": (11, 14), "14–30": (14, 30)
    }
    selected_mw = st.sidebar.selectbox("Average Mud Weight", ["All"] + list(mw_bins.keys()))
    if selected_mw != "All":
        low, high = mw_bins[selected_mw]
        filtered = filtered[(filtered["AMW"] >= low) & (filtered["AMW"] < high)]

    return filtered

# ------------------------- IMPORT PAGE MODULES -------------------------
from multi_well_comparison import render_multi_well
from sales_analysis import render_sales_analysis
from advanced_analysis import render_advanced_analysis
from cost_estimator import render_cost_estimator
# ------------------------- RUN APP -------------------------
st.set_page_config(page_title="Prodigy IQ Dashboard", layout="wide", page_icon="📊")
load_styles()

df = pd.read_csv("Refine Sample.csv")
df["TD_Date"] = pd.to_datetime(df["TD_Date"], errors='coerce')

page = st.sidebar.radio("📂 Navigate", [
    "Multi-Well Comparison",
    "Sales Analysis",
    "Advanced Analysis",
    "Cost Estimator"
])

if page == "Multi-Well Comparison":
    render_multi_well(df)
elif page == "Sales Analysis":
    render_sales_analysis(df)
elif page == "Advanced Analysis":
    render_advanced_analysis(df)
elif page == "Cost Estimator":
    render_cost_estimator(df)
