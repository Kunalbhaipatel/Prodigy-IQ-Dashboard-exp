
import streamlit as st
import pandas as pd
import plotly.express as px
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
def full_filter_sidebar(df):
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

# ------------------------- PAGE 1 -------------------------
def render_multi_well(df):
    st.title("🚀 Prodigy IQ Multi-Well Dashboard")
    filtered_df = full_filter_sidebar(df)

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

# ------------------------- PAGE 2 -------------------------
def render_sales_analysis(df):
    st.title("📈 Prodigy IQ Sales Intelligence")
    filtered_df = full_filter_sidebar(df)

    st.subheader("🧭 Wells Over Time (Monthly Volume)")
    month_df = filtered_df.copy()
    month_df["Month"] = month_df["TD_Date"].dt.to_period("M").astype(str)
    volume = month_df.groupby("Month").size().reset_index(name="Well Count")
    fig_monthly = px.bar(volume, x="Month", y="Well Count", title="Wells Completed per Month")
    st.plotly_chart(fig_monthly, use_container_width=True)

    st.subheader("🧮 Avg Discard Ratio vs Contractor")
    if not filtered_df.empty:
        avg_discard = filtered_df.groupby("Contractor")["Discard Ratio"].mean().reset_index()
        fig_discard = px.bar(avg_discard, x="Contractor", y="Discard Ratio", color="Contractor",
                             title="Average Discard Ratio by Contractor")
        st.plotly_chart(fig_discard, use_container_width=True)

    st.subheader("🧃 Fluid Consumption by Operator")
    fluid_df = filtered_df.groupby("Operator")[["Base_Oil", "Water", "Chemicals"]].sum().reset_index()
    fluid_df = pd.melt(fluid_df, id_vars="Operator", var_name="Fluid", value_name="Volume")
    fig_fluid = px.bar(fluid_df, x="Operator", y="Volume", color="Fluid", barmode="group",
                       title="Total Fluid Usage by Operator")
    st.plotly_chart(fig_fluid, use_container_width=True)

    st.subheader("📍 Regional Penetration")
    region = filtered_df.groupby(["DI Basin", "AAPG Geologic Province"]).size().reset_index(name="Well Count")
    st.dataframe(region)

    st.subheader("🗺️ Location Map")
    fig_map = px.scatter_mapbox(
        filtered_df.dropna(subset=["Well_Coord_Lon", "Well_Coord_Lat"]),
        lat="Well_Coord_Lat", lon="Well_Coord_Lon", hover_name="Well_Name",
        zoom=4, height=500)
    fig_map.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig_map, use_container_width=True)

# ------------------------- PAGE 3 (COST ESTIMATOR) -------------------------

import streamlit as st
import pandas as pd

def render_cost_estimator(df):
    st.title("💰 Flowline Shaker Cost Estimator")

    # Shared Filters
    st.sidebar.header("Filters")
    operator = st.sidebar.selectbox("Operator", ["All"] + sorted(df["Operator"].dropna().unique()))
    contractor = st.sidebar.selectbox("Contractor", ["All"] + sorted(df["Contractor"].dropna().unique()))
    shaker = st.sidebar.selectbox("Shaker Type", ["All"] + sorted(df["flowline_Shakers"].dropna().astype(str).unique()))

    filtered = df.copy()
    if operator != "All":
        filtered = filtered[filtered["Operator"] == operator]
    if contractor != "All":
        filtered = filtered[filtered["Contractor"] == contractor]
    if shaker != "All":
        filtered = filtered[filtered["flowline_Shakers"].astype(str) == shaker]

    # Aggregate Values
    total_dil = filtered["Total_Dil"].sum()
    haul_off = filtered["Haul_OFF"].sum()
    int_length = filtered["IntLength"].sum()

    st.subheader("Calculated Inputs from Filtered Data")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Dilution", f"{total_dil:,.0f}")
    col2.metric("Total Haul-Off", f"{haul_off:,.0f}")
    col3.metric("Interval Length", f"{int_length:,.0f} ft")

    # Manual Overrides
    st.subheader("Custom Cost Parameters")
    col1, col2 = st.columns(2)
    with col1:
        dilution_rate = st.selectbox("Dilution Rate ($/unit)", [100, 200, 300, 500], index=0)
        haul_rate = st.selectbox("Haul-Off Rate ($/unit)", [20, 30, 50], index=0)
        equipment_cost = st.number_input("Equipment Cost", value=100000)
        rig_use_per_year = st.slider("Shakers used/year", 1, 12, 6)
        shaker_life = st.slider("Shaker Life Expectancy (years)", 1, 10, 7)

    with col2:
        screen_used = st.slider("Screens Used per Rig", 1, 10, 1)
        screen_price = st.number_input("Screen Price", value=500)
        eng_rate = st.number_input("Engineering Day Rate", value=1000)
        other_cost = st.number_input("Other Cost", value=500)

    # Calculations
    dilution_cost = dilution_rate * total_dil
    haul_cost = haul_rate * haul_off
    equip_cost = equipment_cost / (shaker_life * rig_use_per_year)
    screen_cost = screen_used * screen_price
    total_cost = dilution_cost + haul_cost + equip_cost + screen_cost + eng_rate + other_cost
    cost_per_foot = total_cost / int_length if int_length else 0

    st.subheader("📊 Cost Summary")
    colA, colB, colC = st.columns(3)
    colA.metric("Dilution Cost", f"${dilution_cost:,.0f}")
    colB.metric("Haul-Off Cost", f"${haul_cost:,.0f}")
    colC.metric("Equipment Cost", f"${equip_cost:,.0f}")
    colA.metric("Screen Cost", f"${screen_cost:,.0f}")
    colB.metric("Other Cost", f"${other_cost:,.0f}")
    colC.metric("Engineering Cost", f"${eng_rate:,.0f}")

    st.markdown("----")
    st.metric("Cumulative Cost", f"${total_cost:,.0f}")
    st.metric("Cost Per Foot", f"${cost_per_foot:,.2f}/ft")

    # Optional savings logic (compare vs baseline)
    baseline_cost = 260320
    savings = baseline_cost - total_cost
    color = "green" if savings > 0 else "red"
    st.markdown(f"### 💰 Estimated Savings vs. Baseline: <span style='color:{color}; font-weight:bold;'>${savings:,.0f}</span>", unsafe_allow_html=True)


# ------------------------- RUN APP -------------------------
st.set_page_config(page_title="Prodigy IQ Dashboard", layout="wide", page_icon="📊")
load_styles()
df = pd.read_csv("Refine Sample.csv")
df["TD_Date"] = pd.to_datetime(df["TD_Date"], errors='coerce')

page = st.sidebar.radio("📂 Navigate", ["Multi-Well Comparison", "Sales Analysis", "Cost Estimator"])
if page == "Multi-Well Comparison":
    render_multi_well(df)
elif page == "Sales Analysis":
    render_sales_analysis(df)
else:
    render_cost_estimator(df)
