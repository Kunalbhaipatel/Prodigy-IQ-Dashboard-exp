
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

# ------------------------- SHARED FILTERS -------------------------
def apply_shared_filters(df):
    st.sidebar.header("Filters")
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

# ------------------------- PAGE: MULTI-WELL -------------------------
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

# ------------------------- PAGE: SALES ANALYSIS -------------------------
def render_sales_analysis(df):
    st.title("📈 Prodigy IQ Sales Intelligence")
    filtered_df = apply_shared_filters(df)

    st.subheader("🧭 Wells Over Time")
    month_df = filtered_df.copy()
    month_df["Month"] = month_df["TD_Date"].dt.to_period("M").astype(str)
    volume = month_df.groupby("Month").size().reset_index(name="Well Count")
    fig_monthly = px.bar(volume, x="Month", y="Well Count", title="Wells Completed per Month")
    st.plotly_chart(fig_monthly, use_container_width=True)

    st.subheader("🧮 Avg Discard Ratio vs Contractor")
    avg_discard = filtered_df.groupby("Contractor")["Discard Ratio"].mean().reset_index()
    fig_discard = px.bar(avg_discard, x="Contractor", y="Discard Ratio", color="Contractor")
    st.plotly_chart(fig_discard, use_container_width=True)

    st.subheader("🧃 Fluid Consumption by Operator")
    fluid_df = filtered_df.groupby("Operator")[["Base_Oil", "Water", "Chemicals"]].sum().reset_index()
    fluid_df = pd.melt(fluid_df, id_vars="Operator", var_name="Fluid", value_name="Volume")
    fig_fluid = px.bar(fluid_df, x="Operator", y="Volume", color="Fluid", barmode="group")
    st.plotly_chart(fig_fluid, use_container_width=True)

# ------------------------- PAGE: COST ESTIMATOR -------------------------
def calculate_costs(df):
    td = df["Total_Dil"].sum()
    ho = df["Haul_OFF"].sum()
    intlen = df["IntLength"].sum()
    depth = df["MD Depth"].max()
    dilution = td * 100
    haul = ho * 20
    screen = 500 * 1
    equipment = 100000 * 3 / 7
    eng = 1000
    other = 500
    total = dilution + haul + screen + equipment + eng + other
    cost_per_ft = total / intlen if intlen else 0
    return {
        "total": total,
        "cost_per_ft": cost_per_ft,
        "depth": depth,
        "breakdown": {
            "Dilution": dilution,
            "Haul": haul,
            "Screen": screen,
            "Equipment": equipment,
            "Engineering": eng,
            "Other": other
        }
    }

def render_cost_estimator(df):
    st.title("💰 Flowline Shaker Cost Comparison")
    filtered_df = apply_shared_filters(df)
    derrick_df = filtered_df[filtered_df["flowline_Shakers"] == "Derrick"]
    nond_df = filtered_df[filtered_df["flowline_Shakers"] == "Non-Derrick"]
    derrick_cost = calculate_costs(derrick_df)
    nond_cost = calculate_costs(nond_df)

    delta_total = nond_cost["total"] - derrick_cost["total"]
    delta_ft = nond_cost["cost_per_ft"] - derrick_cost["cost_per_ft"]
    color_total = "green" if delta_total >= 0 else "red"
    color_ft = "green" if delta_ft >= 0 else "red"

    st.markdown(f"<h4 style='color:{color_total}'>💵 Total Cost Saving: ${delta_total:,.0f}</h4>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='color:{color_ft}'>📏 Cost Per Foot Saving: ${delta_ft:,.2f}</h4>", unsafe_allow_html=True)

    pie1, pie2 = st.columns(2)

with pie1:
    fig1 = px.pie(
        values=list(derrick_cost["breakdown"].values()),
        names=list(derrick_cost["breakdown"].keys())
    )
    st.plotly_chart(fig1, use_container_width=True, key="derrick_pie")

with pie2:
    fig2 = px.pie(
        values=list(nond_cost["breakdown"].values()),
        names=list(nond_cost["breakdown"].keys())
    )
    st.plotly_chart(fig2, use_container_width=True, key="nond_pie")

# ------------------------- PAGE: ADVANCED ANALYSIS -------------------------
def calculate_advanced_metrics(df):
    return {
        "STE": df["STE"].mean() if "STE" in df.columns else 0,
        "CVR": df["CVR"].mean() if "CVR" in df.columns else 0,
        "SLI": df["SLI"].mean() if "SLI" in df.columns else 0,
        "FRC%": df["FRC%"].mean() * 100 if "FRC%" in df.columns else 0,
        "DII": df["DII"].mean() if "DII" in df.columns else 0,
        "FLI": df["FLI"].mean() if "FLI" in df.columns else 0,
        "CDR": df["CDR"].mean() if "CDR" in df.columns else 0,
        "MRE%": df["MRE%"].mean() * 100 if "MRE%" in df.columns else 0,
        "DSL": df["DSL"].mean() if "DSL" in df.columns else 0
    }

def render_kpi_board(metrics):
    cols = st.columns(3)
    for idx, (metric, value) in enumerate(metrics.items()):
        with cols[idx % 3]:
            st.metric(label=metric, value=f"{value:.2f}")

def render_advanced_analysis(df):
    st.title("📌 Advanced Analysis Dashboard")
    filtered_df = apply_shared_filters(df)
    metrics = calculate_advanced_metrics(filtered_df)
    render_kpi_board(metrics)
    st.subheader("📈 Metric Distribution")
    metric_options = list(metrics.keys())
    metric_choice = st.selectbox("Select Metric", metric_options)
    if metric_choice in filtered_df.columns:
        fig = px.box(filtered_df, x="flowline_Shakers", y=metric_choice)
        st.plotly_chart(fig, use_container_width=True)

# ------------------------- RUN APP -------------------------
st.set_page_config(page_title="Prodigy IQ Dashboard", layout="wide", page_icon="📊")
load_styles()
df = pd.read_csv("Refine Sample.csv")
df["TD_Date"] = pd.to_datetime(df["TD_Date"], errors='coerce')

page = st.sidebar.radio("📂 Navigate", ["Multi-Well Comparison", "Sales Analysis", "Advanced Analysis", "Cost Estimator"])
if page == "Multi-Well Comparison":
    render_multi_well(df)
elif page == "Sales Analysis":
    render_sales_analysis(df)
elif page == "Advanced Analysis":
    render_advanced_analysis(df)
elif page == "Cost Estimator":
    render_cost_estimator(df)
