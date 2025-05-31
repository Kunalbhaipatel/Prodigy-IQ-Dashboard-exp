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

    filtered["TD_Date"] = pd.to_datetime(filtered["TD_Date"], errors="coerce")
    if "TD_Date" in filtered.columns:
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

# ------------------------- PAGE: ADVANCED ANALYSIS -------------------------
def render_advanced_analysis(df):
    st.title("📌 Advanced Analysis Dashboard")
    filtered_df = apply_shared_filters(df)

    st.sidebar.header("🛠️ Manual Input (If Data Missing)")
    total_flow_rate = st.sidebar.number_input("Total Flow Rate (GPM)", value=800)
    number_of_screens = st.sidebar.number_input("Number of Screens Installed", value=3)
    screen_area = st.sidebar.number_input("Area per Screen (sq ft)", value=2.0)
    unit = st.sidebar.radio("Normalize by", ["None", "Feet", "Hours", "Days"])

    def safe_div(n, d): return n / d if d else 0

    metrics = []
    for _, row in filtered_df.iterrows():
        haul = row.get("Haul_OFF", 0)
        intlen = row.get("IntLength", 0)
        hole = row.get("Hole_Size", 1)
        sce = row.get("Total_SCE", 0)
        bo, water, chem = row.get("Base_Oil", 0), row.get("Water", 0), row.get("Chemicals", 0)
        rop = row.get("ROP", 0)
        hr = row.get("Drilling_Hours", 0)

        metrics.append({
            "Well_Name": row.get("Well_Name", ""),
            "Operator": row.get("Operator", ""),
            "Shaker Throughput Efficiency": safe_div(sce, sce) * 100,
            "Cuttings Volume Ratio": safe_div(haul, intlen),
            "Screen Loading Index": safe_div(total_flow_rate, number_of_screens * screen_area),
            "Fluid Retention on Cuttings (%)": safe_div(sce, sce) * 100,
            "Drilling Intensity Index": safe_div(rop, hole),
            "Fluid Loading Index": safe_div(bo + water + chem, intlen),
            "Chemical Demand Rate": safe_div(chem, intlen),
            "Mud Retention Efficiency (%)": 100 - safe_div(sce, sce) * 100,
            "Downstream Solids Loss": 100 - safe_div(sce, sce) * 100
        })

    metric_df = pd.DataFrame(metrics)
    if unit == "Feet":
        divisor = filtered_df["IntLength"].sum()
    elif unit == "Hours":
        divisor = filtered_df["Drilling_Hours"].sum()
    elif unit == "Days":
        divisor = safe_div(filtered_df["Drilling_Hours"].sum(), 24)
    else:
        divisor = None

    if divisor:
        for col in metric_df.columns[2:]:
            metric_df[col] = metric_df[col].apply(lambda x: safe_div(x, divisor))

    st.subheader("📋 KPI Summary")
    kpi_cols = st.columns(3)
    for i, col in enumerate(metric_df.columns[2:]):
        with kpi_cols[i % 3]:
            st.metric(col, f"{metric_df[col].mean():.2f}")

    st.subheader("📊 Compare Metrics")
    selected_metric = st.selectbox("Select Metric", metric_df.columns[2:])
    if selected_metric:
        fig = px.bar(metric_df, x="Well_Name", y=selected_metric, color="Operator", title=f"{selected_metric} across Wells")
        fig.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("📤 Export Filtered Data")
    st.download_button("Download CSV", metric_df.to_csv(index=False), "filtered_advanced_metrics.csv", "text/csv")
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

    filtered["TD_Date"] = pd.to_datetime(filtered["TD_Date"], errors="coerce")
    if "TD_Date" in filtered.columns:
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

# ------------------------- PAGE: COST ESTIMATOR -------------------------
def render_cost_estimator(df):
    st.title("💰 Flowline Shaker Cost Comparison")

    col_d, col_nd = st.columns(2)

    with col_d:
        st.subheader("🟩 Derrick")
        derrick_df = df.copy()
        derrick_shaker = st.selectbox("Select Flowline Shaker", sorted(derrick_df["flowline_Shakers"].dropna().unique()), key="d_shaker")
        derrick_df = derrick_df[derrick_df["flowline_Shakers"] == derrick_shaker]

        derrick_ops = sorted(derrick_df["Operator"].dropna().unique())
        derrick_operator = st.selectbox("Select Operator", ["All"] + derrick_ops, key="d_operator")
        if derrick_operator != "All":
            derrick_df = derrick_df[derrick_df["Operator"] == derrick_operator]

        derrick_contracts = sorted(derrick_df["Contractor"].dropna().unique())
        derrick_contractor = st.selectbox("Select Contractor", ["All"] + derrick_contracts, key="d_contract")
        if derrick_contractor != "All":
            derrick_df = derrick_df[derrick_df["Contractor"] == derrick_contractor]

        derrick_wells = sorted(derrick_df["Well_Name"].dropna().unique())
        derrick_well = st.selectbox("Select Well Name", ["All"] + derrick_wells, key="d_well")
        if derrick_well != "All":
            derrick_df = derrick_df[derrick_df["Well_Name"] == derrick_well]

    with col_nd:
        st.subheader("🟣 Non-Derrick")
        nond_df = df.copy()
        nond_shaker = st.selectbox("Select Flowline Shaker", sorted(nond_df["flowline_Shakers"].dropna().unique()), key="nd_shaker")
        nond_df = nond_df[nond_df["flowline_Shakers"] == nond_shaker]

        nond_ops = sorted(nond_df["Operator"].dropna().unique())
        nond_operator = st.selectbox("Select Operator", ["All"] + nond_ops, key="nd_operator")
        if nond_operator != "All":
            nond_df = nond_df[nond_df["Operator"] == nond_operator]

        nond_contracts = sorted(nond_df["Contractor"].dropna().unique())
        nond_contractor = st.selectbox("Select Contractor", ["All"] + nond_contracts, key="nd_contract")
        if nond_contractor != "All":
            nond_df = nond_df[nond_df["Contractor"] == nond_contractor]

        nond_wells = sorted(nond_df["Well_Name"].dropna().unique())
        nond_well = st.selectbox("Select Well Name", ["All"] + nond_wells, key="nd_well")
        if nond_well != "All":
            nond_df = nond_df[nond_df["Well_Name"] == nond_well]

    derrick_config, nond_config = {}, {}

    with st.expander("🎯 Derrick Configuration"):
        derrick_config["dil_rate"] = st.number_input("Dilution Cost Rate ($/unit)", value=100, key="d_dil")
        derrick_config["haul_rate"] = st.number_input("Haul-Off Cost Rate ($/unit)", value=20, key="d_haul")
        derrick_config["screen_price"] = st.number_input("Screen Price", value=500, key="d_scr_price")
        derrick_config["num_screens"] = st.number_input("Screens used per rig", value=1, key="d_scr_cnt")
        derrick_config["equip_cost"] = st.number_input("Total Equipment Cost", value=100000, key="d_equip")
        derrick_config["num_shakers"] = st.number_input("Number of Shakers Installed", value=3, key="d_shkrs")
        derrick_config["shaker_life"] = st.number_input("Shaker Life (Years)", value=7, key="d_life")
        derrick_config["eng_cost"] = st.number_input("Engineering Day Rate", value=1000, key="d_eng")
        derrick_config["other_cost"] = st.number_input("Other Cost", value=500, key="d_other")

    with st.expander("🎯 Non-Derrick Configuration"):
        nond_config["dil_rate"] = st.number_input("Dilution Cost Rate ($/unit)", value=100, key="nd_dil")
        nond_config["haul_rate"] = st.number_input("Haul-Off Cost Rate ($/unit)", value=20, key="nd_haul")
        nond_config["screen_price"] = st.number_input("Screen Price", value=500, key="nd_scr_price")
        nond_config["num_screens"] = st.number_input("Screens used per rig", value=1, key="nd_scr_cnt")
        nond_config["equip_cost"] = st.number_input("Total Equipment Cost", value=100000, key="nd_equip")
        nond_config["num_shakers"] = st.number_input("Number of Shakers Installed", value=3, key="nd_shkrs")
        nond_config["shaker_life"] = st.number_input("Shaker Life (Years)", value=7, key="nd_life")
        nond_config["eng_cost"] = st.number_input("Engineering Day Rate", value=1000, key="nd_eng")
        nond_config["other_cost"] = st.number_input("Other Cost", value=500, key="nd_other")

    def calc_cost(sub_df, config, label):
        td = sub_df["Total_Dil"].sum()
        ho = sub_df["Haul_OFF"].sum()
        intlen = sub_df["IntLength"].sum()
        dilution = config["dil_rate"] * td
        haul = config["haul_rate"] * ho
        screen = config["screen_price"] * config["num_screens"]
        equipment = (config["equip_cost"] * config["num_shakers"]) / config["shaker_life"]
        total = dilution + haul + screen + equipment + config["eng_cost"] + config["other_cost"]
        per_ft = total / intlen if intlen else 0

        return {
            "Label": label,
            "Cost/ft": per_ft,
            "Total Cost": total,
            "Dilution": dilution,
            "Haul": haul,
            "Screen": screen,
            "Equipment": equipment,
            "Engineering": config["eng_cost"],
            "Other": config["other_cost"],
            "Avg LGS%": (sub_df["LGS"].mean() * 100) if "LGS" in sub_df.columns else 0,
            "DSRE%": (sub_df["DSRE"].mean() * 100) if "DSRE" in sub_df.columns else 0,
            "Depth": sub_df["MD Depth"].max() if "MD Depth" in sub_df.columns else 0,
        }

    derrick_cost = calc_cost(derrick_df, derrick_config, "Derrick")
    nond_cost = calc_cost(nond_df, nond_config, "Non-Derrick")
    summary = pd.DataFrame([derrick_cost, nond_cost])

    fig_cost = px.bar(summary, x="Label", y="Cost/ft", color="Label", title="Cost per Foot Comparison")
    fig_depth = px.bar(summary, x="Label", y="Depth", color="Label", title="Total Depth Drilled")

    st.plotly_chart(fig_cost, use_container_width=True)
    st.plotly_chart(fig_depth, use_container_width=True
# ------------------------- LOAD DATA -------------------------
load_styles()
df = pd.read_csv("Refine Sample.csv")
df["TD_Date"] = pd.to_datetime(df["TD_Date"], errors='coerce')

# ------------------------- MAIN NAVIGATION -------------------------
page = st.sidebar.radio("📂 Navigate", ["Multi-Well Comparison", "Sales Analysis", "Advanced Analysis","Cost Estimator"])

if page == "Multi-Well Comparison":
    render_multi_well(df)
elif page == "Sales Analysis":
    render_sales_analysis(df)
elif page == "Advanced Analysis":
    render_advanced_analysis(df)
elif page == "Cost Estimator":
    render_cost_estimator(df)

