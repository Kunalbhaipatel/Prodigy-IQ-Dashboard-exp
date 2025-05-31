import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

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
    section[data-testid="stSidebar"] div[role="radiogroup"] > label {
        background: #f8f9fa;
        border-radius: 10px;
        margin: 0.2em 0;
        padding: 0.5em;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        background: #e9ecef;
    }
    .global-box {
        background-color: #f0f2f6;
        padding: 1em;
        border-radius: 12px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    </style>""", unsafe_allow_html=True)

# ------------------------- FILTER PANEL -------------------------
def render_filter_panel(df):
    with st.sidebar:
        filter_mode = st.radio("🧰 Filter Mode", ["Global", "Common", "Advanced"], horizontal=True)

        if filter_mode == "Global":
            with st.expander("🌐 Global Filters", expanded=True):
                st.markdown("<div class='global-box'>", unsafe_allow_html=True)
                search_term = st.text_input("🔍 Search Anything").lower()
                if search_term:
                    df = df[df.apply(lambda row: row.astype(str).str.lower().str.contains(search_term).any(), axis=1)]
                wells = st.multiselect("Well Name", sorted(df["Well_Name"].dropna().unique()))
                if wells:
                    df = df[df["Well_Name"].isin(wells)]
                st.markdown("</div>", unsafe_allow_html=True)

        if filter_mode == "Common":
            with st.expander("🔁 Common Filters", expanded=True):
                for col in ["flowline_Shakers", "Operator", "Contractor"]:
                    options = ["All"] + sorted(df[col].dropna().astype(str).unique())
                    selected = st.selectbox(col.replace("_", " "), options, key=col)
                    if selected != "All":
                        df = df[df[col].astype(str) == selected]

        if filter_mode == "Advanced":
            with st.expander("⚙️ Advanced Filters", expanded=True):
                df["TD_Date"] = pd.to_datetime(df["TD_Date"], errors="coerce")
                year_range = st.slider("TD Date Range", 2020, 2026, (2020, 2026))
                df = df[(df["TD_Date"].dt.year >= year_range[0]) & (df["TD_Date"].dt.year <= year_range[1])]
                if "MD Depth" in df:
                    depth_bins = {
                        "<5000 ft": (0, 5000), "5000–10000 ft": (5000, 10000),
                        "10000–15000 ft": (10000, 15000), ">15000 ft": (15000, float("inf"))
                    }
                    selected = st.selectbox("Depth Range", ["All"] + list(depth_bins.keys()), key="depth")
                    if selected != "All":
                        low, high = depth_bins[selected]
                        df = df[(df["MD Depth"] >= low) & (df["MD Depth"] < high)]
                if "AMW" in df:
                    mw_bins = {
                        "<3": (0, 3), "3–6": (3, 6), "6–9": (6, 9), "9–12": (9, 12), ">12": (12, float("inf"))
                    }
                    selected = st.selectbox("Mud Weight", ["All"] + list(mw_bins.keys()), key="mud")
                    if selected != "All":
                        low, high = mw_bins[selected]
                        df = df[(df["AMW"] >= low) & (df["AMW"] < high)]
    return df

# ------------------------- PAGE: MULTI-WELL COMPARISON -------------------------
def render_multi_well(df):
    st.title("🚀 Prodigy IQ Multi-Well Dashboard")
    st.subheader("Summary Metrics")
    col1, col2 = st.columns(2)
    col1.metric("Total Wells", len(df))
    col2.metric("Avg ROP", f"{df['ROP'].mean():.2f}")

    st.subheader("📊 ROP by Well")
    if "Well_Name" in df and "ROP" in df:
        fig = px.bar(df, x="Well_Name", y="ROP", color="Operator")
        st.plotly_chart(fig, use_container_width=True)

# ------------------------- PAGE: SALES ANALYSIS -------------------------
def render_sales_analysis(df):
    st.title("📈 Prodigy IQ Sales Analysis")
    df["Month"] = df["TD_Date"].dt.to_period("M").astype(str)
    volume = df.groupby("Month").size().reset_index(name="Well Count")
    st.subheader("🧭 Wells Completed per Month")
    fig = px.line(volume, x="Month", y="Well Count", markers=True)
    st.plotly_chart(fig, use_container_width=True)

# ------------------------- PAGE: ADVANCED ANALYSIS -------------------------
def render_advanced_analysis(df):
    st.title("📌 Prodigy IQ Advanced Analysis")
    st.subheader("Advanced KPI Summary")
    if "Total_SCE" in df and "IntLength" in df:
        df["STE"] = df["Total_SCE"] / df["IntLength"]
        st.metric("Shaker Throughput Efficiency (avg)", f"{df['STE'].mean():.2f}")
        fig = px.bar(df, x="Well_Name", y="STE", color="Operator")
        st.plotly_chart(fig, use_container_width=True)

# ------------------------- PAGE: COST ESTIMATOR -------------------------
def render_cost_estimator(df):
    st.title("💰 Prodigy IQ Cost Estimator")
    st.subheader("Summary Cost Comparison")
    # Simplified example. Add real calculation logic as needed.
    st.write("(Cost Estimator logic will go here, e.g., dilution, haul-off, equipment, per-ft cost breakdown etc.)")

# ------------------------- LOAD DATA -------------------------
load_styles()
df = pd.read_csv("Refine Sample.csv")
df["TD_Date"] = pd.to_datetime(df["TD_Date"], errors='coerce')

# ------------------------- MAIN NAVIGATION -------------------------
page = st.sidebar.radio("📂 Navigate", ["Multi-Well Comparison", "Sales Analysis", "Advanced Analysis", "Cost Estimator"])
df_filtered = render_filter_panel(df)

if page == "Multi-Well Comparison":
    render_multi_well(df_filtered)
elif page == "Sales Analysis":
    render_sales_analysis(df_filtered)
elif page == "Advanced Analysis":
    render_advanced_analysis(df_filtered)
elif page == "Cost Estimator":
    render_cost_estimator(df_filtered)
