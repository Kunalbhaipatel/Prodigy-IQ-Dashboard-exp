
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Inject custom CSS ---
def load_styles():
    st.markdown("""<style>
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 15px;
    }
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        padding: 1.2em;
        border-radius: 15px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1);
        margin: 0.5em 0.5em;
        text-align: center;
    }
    section[data-testid="stSidebar"] {
        padding: 1.5rem;
    }
    h2 {
        color: #2c3e50;
        margin-top: 1.5rem;
    }
    h3 {
        color: #007635;
        font-weight: 600;
    }
    </style>""", unsafe_allow_html=True)

# --- Multi-Well Page ---
def render_multi_well_page(df):
    st.title("🚀 Prodigy IQ Multi-Well Dashboard")
    st.markdown("Use filters to explore drilling efficiency, fluid usage, and solids control KPIs.")

    st.sidebar.title("Filters")
    operator = st.sidebar.selectbox("Operator", ["All"] + sorted(df["Operator"].dropna().unique().tolist()))
    contractor = st.sidebar.selectbox("Contractor", ["All"] + sorted(df["Contractor"].dropna().unique().tolist()))
    flowline = st.sidebar.selectbox("Flowline", ["All"] + sorted(df["flowline_Shakers"].dropna().astype(str).unique().tolist()))
    hole_size = st.sidebar.selectbox("Hole Size", ["All"] + sorted(df["Hole_Size"].dropna().unique().tolist()))

    depth_map = {
        "<5000 ft": (0, 5000), "5000–10000 ft": (5000, 10000),
        "10000–15000 ft": (10000, 15000), "15000–20000 ft": (15000, 20000),
        "20000–25000 ft": (20000, 25000), "25000 ft and above": (25000, float("inf"))
    }
    depth_range = st.sidebar.selectbox("Depth Range", ["All"] + list(depth_map.keys()))

    mw_map = {
        "<3": (0, 3), "3–6": (3, 6), "6–9": (6, 9),
        "9–11": (9, 11), "11–14": (11, 14), "14–30": (14, 30)
    }
    amw_range = st.sidebar.selectbox("Avg. Mud Weight", ["All"] + list(mw_map.keys()))

    year_range = st.sidebar.slider("Date Range (TD Date)", 2020, 2026, (2020, 2026))
    search = st.sidebar.text_input("Search Anything").lower()

    df["TD_Date"] = pd.to_datetime(df["TD_Date"], errors='coerce')
    df = df[df["TD_Date"].dt.year.between(year_range[0], year_range[1])]

    if operator != "All":
        df = df[df["Operator"] == operator]
    if contractor != "All":
        df = df[df["Contractor"] == contractor]
    if flowline != "All":
        df = df[df["flowline_Shakers"].astype(str) == flowline]
    if hole_size != "All":
        df = df[df["Hole_Size"] == hole_size]
    if depth_range != "All":
        low, high = depth_map[depth_range]
        df = df[(df["MD Depth"] >= low) & (df["MD Depth"] < high)]
    if amw_range != "All":
        low, high = mw_map[amw_range]
        df = df[(df["AMW"] >= low) & (df["AMW"] < high)]
    if search:
        df = df[df.apply(lambda row: row.astype(str).str.lower().str.contains(search).any(), axis=1)]

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("📏 IntLength", f"{df['IntLength'].mean():.1f}")
    col2.metric("🏃 ROP", f"{df['ROP'].mean():.1f}")
    col3.metric("🧪 Dilution Ratio", f"{df['Dilution_Ratio'].mean():.2f}")
    col4.metric("🧴 Discard Ratio", f"{df['Discard Ratio'].mean():.2f}")
    col5.metric("🚛 Haul OFF", f"{df['Haul_OFF'].mean():.1f}")
    col6.metric("🌡️ AMW", f"{df['AMW'].mean():.2f}")

    st.subheader("📊 Compare Metrics Across Wells")
    param = st.selectbox("Select Parameter", df.select_dtypes(include='number').columns.tolist())
    fig = px.bar(df, x="Well_Job_ID", y=param, color="Operator", title=f"{param} by Well")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🗺️ Well Locations")
    fig_map = px.scatter_mapbox(df.dropna(subset=["Well_Coord_Lon", "Well_Coord_Lat"]),
                                lat="Well_Coord_Lat", lon="Well_Coord_Lon", hover_name="Well_Name",
                                zoom=4, height=500)
    fig_map.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig_map, use_container_width=True)

# --- Sales Analysis Page ---
def render_sales_analysis_page(df):
    st.title("📈 Sales Analysis Dashboard")

    st.sidebar.header("Filters")
    operator = st.sidebar.selectbox("Operator", ["All"] + sorted(df["Operator"].dropna().unique().tolist()))
    contractor = st.sidebar.selectbox("Contractor", ["All"] + sorted(df["Contractor"].dropna().unique().tolist()))

    if operator != "All":
        df = df[df["Operator"] == operator]
    if contractor != "All":
        df = df[df["Contractor"] == contractor]

    st.subheader("📊 Metric Trends Over Time")
    ts_metrics = ["DSRE", "Dilution_Ratio", "Discard Ratio", "MD Depth"]
    fig_ts = px.line(df, x="TD_Date", y=ts_metrics, title="Metric Trends")
    st.plotly_chart(fig_ts, use_container_width=True)

    st.subheader("🥧 Flowline Shaker Distribution")
    fig_pie = px.pie(df, names="flowline_Shakers", title="Flowline Shakers by Count")
    st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("📦 Summary Performance")
    month_now = pd.Timestamp.now().month
    year_now = pd.Timestamp.now().year
    month_data = df[df["TD_Date"].dt.month == month_now]
    year_data = df[df["TD_Date"].dt.year == year_now]

    col1, col2, col3 = st.columns(3)
    col1.metric("📆 MoM Wells", len(month_data))
    col2.metric("📅 YoY Wells", len(year_data))
    col3.metric("🛢️ Total Wells", len(df))

    st.subheader("🌍 Regional Summary")
    region_df = df.groupby(["DI Basin", "AAPG Geologic Province"]).size().reset_index(name="Well Count")
    st.dataframe(region_df)

    st.subheader("🗺️ Well Location Map")
    fig_map = px.scatter_mapbox(
        df.dropna(subset=["Well_Coord_Lon", "Well_Coord_Lat"]),
        lat="Well_Coord_Lat", lon="Well_Coord_Lon", hover_name="Well_Name",
        zoom=4, height=500
    )
    fig_map.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig_map, use_container_width=True)

# --- Run App ---
st.set_page_config(page_title="Prodigy IQ Dashboard", layout="wide", page_icon="📊")
load_styles()

df = pd.read_csv("Refine Sample.csv")
df["TD_Date"] = pd.to_datetime(df["TD_Date"], errors='coerce')

page = st.sidebar.radio("📂 Navigate", ["Multi-Well Comparison", "Sales Analysis"])

if page == "Multi-Well Comparison":
    render_multi_well_page(df)
elif page == "Sales Analysis":
    render_sales_analysis_page(df)
