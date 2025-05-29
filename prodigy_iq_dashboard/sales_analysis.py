import streamlit as st
import pandas as pd
import plotly.express as px

def render_sales_analysis():
    df = pd.read_csv("Refine Sample.csv")
    df["TD_Date"] = pd.to_datetime(df["TD_Date"], errors='coerce')

    st.title("📈 Sales Analysis Dashboard")

    # Filters
    st.sidebar.header("Filters")
    operator = st.sidebar.selectbox("Operator", ["All"] + sorted(df["Operator"].dropna().unique().tolist()))
    contractor = st.sidebar.selectbox("Contractor", ["All"] + sorted(df["Contractor"].dropna().unique().tolist()))

    if operator != "All":
        df = df[df["Operator"] == operator]
    if contractor != "All":
        df = df[df["Contractor"] == contractor]

    # Time Series Chart
    st.subheader("📊 Metric Trends Over Time")
    ts_metrics = ["DSRE", "Dilution_Ratio", "Discard Ratio", "MD Depth"]
    fig_ts = px.line(df, x="TD_Date", y=ts_metrics, title="Metric Trends")
    st.plotly_chart(fig_ts, use_container_width=True)

    # Pie Chart
    st.subheader("🥧 Flowline Shaker Distribution")
    fig_pie = px.pie(df, names="flowline_Shakers", title="Flowline Shakers by Count")
    st.plotly_chart(fig_pie, use_container_width=True)

    # Box Cards
    st.subheader("📦 Summary Performance")
    month_now = pd.Timestamp.now().month
    year_now = pd.Timestamp.now().year
    month_data = df[df["TD_Date"].dt.month == month_now]
    year_data = df[df["TD_Date"].dt.year == year_now]

    col1, col2, col3 = st.columns(3)
    col1.metric("📆 MoM Wells", len(month_data))
    col2.metric("📅 YoY Wells", len(year_data))
    col3.metric("🛢️ Total Wells", len(df))

    # Regional Table
    st.subheader("🌍 Regional Summary")
    region_df = df.groupby(["DI Basin", "AAPG Geologic Province"]).size().reset_index(name="Well Count")
    st.dataframe(region_df)

    # Map Chart
    st.subheader("🗺️ Well Location Map")
    fig_map = px.scatter_mapbox(
        df.dropna(subset=["Well_Coord_Lon", "Well_Coord_Lat"]),
        lat="Well_Coord_Lat", lon="Well_Coord_Lon", hover_name="Well_Name",
        zoom=4, height=500
    )
    fig_map.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig_map, use_container_width=True)
