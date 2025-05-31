import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# ✅ Set page config ONCE at the top
st.set_page_config(page_title="Prodigy IQ Dashboard", layout="wide", page_icon="📊")

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

# ------------------------- SHARED FILTERS -------------------------
def apply_shared_filters(df):
    st.sidebar.header("📊 Shared Filters")
    search_term = st.sidebar.text_input("🔍 Search Anything").lower()
    filtered = df.copy()

    if search_term:
        filtered = filtered[filtered.apply(lambda row: row.astype(str).str.lower().str.contains(search_term).any(), axis=1)]

    for col in ["Operator", "Contractor", "flowline_Shakers", "Hole_Size"]:
        if col in filtered.columns:
            options = sorted(filtered[col].dropna().astype(str).unique().tolist())
            selected = st.sidebar.selectbox(col, ["All"] + options, key=col)
            if selected != "All":
                filtered = filtered[filtered[col].astype(str) == selected]

    if "TD_Date" in filtered.columns:
        filtered["TD_Date"] = pd.to_datetime(filtered["TD_Date"], errors="coerce")
        year_range = st.sidebar.slider("TD Date Range", 2020, 2026, (2020, 2026))
        filtered = filtered[(filtered["TD_Date"].dt.year >= year_range[0]) & (filtered["TD_Date"].dt.year <= year_range[1])]

    if "MD Depth" in filtered.columns:
        depth_bins = {
            "<5000 ft": (0, 5000), "5000–10000 ft": (5000, 10000),
            "10000–15000 ft": (10000, 15000), "15000–20000 ft": (15000, 20000),
            "20000–25000 ft": (20000, 25000), ">25000 ft": (25000, float("inf"))
        }
        selected_depth = st.sidebar.selectbox("Depth", ["All"] + list(depth_bins.keys()))
        if selected_depth != "All":
            low, high = depth_bins[selected_depth]
            filtered = filtered[(filtered["MD Depth"] >= low) & (filtered["MD Depth"] < high)]

    if "AMW" in filtered.columns:
        mw_bins = {
            "<3": (0, 3), "3–6": (3, 6), "6–9": (6, 9),
            "9–11": (9, 11), "11–14": (11, 14), "14–30": (14, 30)
        }
        selected_mw = st.sidebar.selectbox("Average Mud Weight", ["All"] + list(mw_bins.keys()))
        if selected_mw != "All":
            low, high = mw_bins[selected_mw]
            filtered = filtered[(filtered["AMW"] >= low) & (filtered["AMW"] < high)]

    return filtered

# ------------------------- PAGE: MULTI-WELL COMPARISON -------------------------
def render_multi_well(df):
    st.title("🚀 Prodigy IQ Multi-Well Dashboard")
    filtered_df = apply_shared_filters(df)

    st.subheader("Summary Metrics")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("📏 IntLength", f"{filtered_df['IntLength'].mean():.1f}")
    col2.metric("🏃 ROP", f"{filtered_df['ROP'].mean():.1f}")
    col3.metric("🧪 Dilution Ratio", f"{filtered_df['Dilution_Ratio'].mean():.2f}")
    col4.metric("🧴 Discard Ratio", f"{filtered_df['Discard Ratio'].mean():.2f}")
    col5.metric("🚛 Haul OFF", f"{filtered_df['Haul_OFF'].mean():.1f}")
    col6.metric("🌡️ AMW", f"{filtered_df['AMW'].mean():.2f}")

    st.subheader("📊 Compare Metrics")
    numeric_cols = filtered_df.select_dtypes(include='number').columns.tolist()
    exclude = ['No', 'Well_Job_ID', 'Well_Coord_Lon', 'Well_Coord_Lat', 'Hole_Size', 'IsReviewed', 'State Code', 'County Code']
    metric_options = [col for col in numeric_cols if col not in exclude]
    selected_metric = st.selectbox("Select Metric", metric_options)

    if selected_metric:
        fig = px.bar(filtered_df, x="Well_Name", y=selected_metric, color="Operator")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("🗺️ Well Map")
    fig_map = px.scatter_mapbox(
        filtered_df.dropna(subset=["Well_Coord_Lon", "Well_Coord_Lat"]),
        lat="Well_Coord_Lat", lon="Well_Coord_Lon", hover_name="Well_Name",
        zoom=4, height=500)
    fig_map.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig_map, use_container_width=True)

# ------------------------- LOAD DATA -------------------------
load_styles()
df = pd.read_csv("Refine Sample.csv")
df["TD_Date"] = pd.to_datetime(df["TD_Date"], errors='coerce')

# ------------------------- MAIN NAVIGATION -------------------------
page = st.sidebar.radio("📂 Navigate", ["Multi-Well Comparison", "Sales Analysis", "Advanced Analysis", "Cost Estimator"])

# ------------------------- CALL PAGE FUNCTIONS -------------------------
if page == "Multi-Well Comparison":
    render_multi_well(df)
elif page == "Sales Analysis":
    st.title("Sales Analysis")
    st.write("(Sales Analysis content will be rendered here...)")
elif page == "Advanced Analysis":
    st.title("Advanced Analysis")
    st.write("(Advanced Analysis content will be rendered here...)")
elif page == "Cost Estimator":
    st.title("💰 Prodigy IQ Cost Estimator")
    st.write("(Cost Estimator content will be rendered here...)")
