
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

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

def dynamic_filter_sidebar(df):
    st.sidebar.header("Dynamic Filters")
    filtered = df.copy()

    operators = sorted(filtered["Operator"].dropna().unique().tolist())
    selected_operator = st.sidebar.selectbox("Operator", ["All"] + operators)
    if selected_operator != "All":
        filtered = filtered[filtered["Operator"] == selected_operator]

    contractors = sorted(filtered["Contractor"].dropna().unique().tolist())
    selected_contractor = st.sidebar.selectbox("Contractor", ["All"] + contractors)
    if selected_contractor != "All":
        filtered = filtered[filtered["Contractor"] == selected_contractor]

    flowlines = sorted(filtered["flowline_Shakers"].dropna().astype(str).unique().tolist())
    selected_flowline = st.sidebar.selectbox("Flowline", ["All"] + flowlines)
    if selected_flowline != "All":
        filtered = filtered[filtered["flowline_Shakers"].astype(str) == selected_flowline]

    hole_sizes = sorted(filtered["Hole_Size"].dropna().unique().tolist())
    selected_hole = st.sidebar.selectbox("Hole Size", ["All"] + hole_sizes)
    if selected_hole != "All":
        filtered = filtered[filtered["Hole_Size"] == selected_hole]

    return filtered

def render_multi_well(df):
    st.title("🚀 Prodigy IQ Multi-Well Dashboard")
    filtered_df = dynamic_filter_sidebar(df)

    st.subheader("Summary Metrics")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("📏 IntLength", f"{filtered_df['IntLength'].mean():.1f}")
    col2.metric("🏃 ROP", f"{filtered_df['ROP'].mean():.1f}")
    col3.metric("🧪 Dilution Ratio", f"{filtered_df['Dilution_Ratio'].mean():.2f}")
    col4.metric("🧴 Discard Ratio", f"{filtered_df['Discard Ratio'].mean():.2f}")
    col5.metric("🚛 Haul OFF", f"{filtered_df['Haul_OFF'].mean():.1f}")
    col6.metric("🌡️ AMW", f"{filtered_df['AMW'].mean():.2f}")

    st.subheader("📊 Compare Metrics")
    selected_metric = st.selectbox("Select Metric", filtered_df.select_dtypes(include='number').columns.tolist())
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

def render_sales_analysis(df):
    st.title("📈 Sales Analysis")
    filtered_df = dynamic_filter_sidebar(df)

    st.subheader("📊 Time Series - Number of Wells by Date")
    daily_wells = filtered_df.groupby("TD_Date").size().reset_index(name="Well Count")
    fig = px.line(daily_wells, x="TD_Date", y="Well Count", title="Wells Over Time")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🥧 Flowline Shaker Split")
    pie = px.pie(filtered_df, names="flowline_Shakers")
    st.plotly_chart(pie, use_container_width=True)

    st.subheader("📦 Performance Summary")
    month_now = pd.Timestamp.now().month
    year_now = pd.Timestamp.now().year
    col1, col2, col3 = st.columns(3)
    col1.metric("MoM Wells", len(filtered_df[filtered_df['TD_Date'].dt.month == month_now]))
    col2.metric("YoY Wells", len(filtered_df[filtered_df['TD_Date'].dt.year == year_now]))
    col3.metric("Total Wells", len(filtered_df))

    st.subheader("📍 Region Table")
    st.dataframe(filtered_df.groupby(["DI Basin", "AAPG Geologic Province"]).size().reset_index(name="Wells"))

    st.subheader("🗺️ Locations")
    fig_map = px.scatter_mapbox(
        filtered_df.dropna(subset=["Well_Coord_Lon", "Well_Coord_Lat"]),
        lat="Well_Coord_Lat", lon="Well_Coord_Lon", hover_name="Well_Name",
        zoom=4, height=500)
    fig_map.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig_map, use_container_width=True)

# MAIN
st.set_page_config(page_title="Prodigy IQ Dashboard", layout="wide", page_icon="📊")
load_styles()
df = pd.read_csv("Refine Sample.csv")
df["TD_Date"] = pd.to_datetime(df["TD_Date"], errors='coerce')

page = st.sidebar.radio("📂 Navigate", ["Multi-Well Comparison", "Sales Analysis"])
if page == "Multi-Well Comparison":
    render_multi_well(df)
else:
    render_sales_analysis(df)
