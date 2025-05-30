import streamlit as st
import pandas as pd
from multi_well_comparison import render_multi_well_page
from sales_analysis import render_sales_analysis
from advanced_analysis import render_advanced_analysis

# ------------------------- STYLING -------------------------
def load_styles():
    st.markdown("""
        <style>
        div[data-testid="metric-container"] {
            background-color: #fff;
            padding: 1.2em;
            border-radius: 15px;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1);
            margin: 0.5em;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

# ------------------------- MAIN APP -------------------------
st.set_page_config(page_title="Prodigy IQ Dashboard", layout="wide", page_icon="📊")
load_styles()

df = pd.read_csv("Refine Sample.csv")
df["TD_Date"] = pd.to_datetime(df["TD_Date"], errors='coerce')

# Sidebar Navigation
page = st.sidebar.radio("📂 Navigate", [
    "Multi-Well Comparison",
    "Sales Analysis",
    "Advanced Analysis"
])

if page == "Multi-Well Comparison":
    render_multi_well_page()
elif page == "Sales Analysis":
    render_sales_analysis()
elif page == "Advanced Analysis":
    render_advanced_analysis(df)

# ------------------------- PAGE 1: MULTI-WELL -------------------------
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

# ------------------------- PAGE 2: SALES -------------------------
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

# ------------------------- PAGE 3: COST ESTIMATOR -------------------------

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

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

    delta_total = nond_cost['Total Cost'] - derrick_cost['Total Cost']
    delta_ft = nond_cost['Cost/ft'] - derrick_cost['Cost/ft']

    bg_color_total = "#d4edda" if delta_total >= 0 else "#f8d7da"
    text_color_total = "green" if delta_total >= 0 else "red"
    bg_color_ft = "#d4edda" if delta_ft >= 0 else "#f8d7da"
    text_color_ft = "green" if delta_ft >= 0 else "red"

    st.markdown(f"""
        <div style='display: flex; gap: 2rem; margin-top: 1rem;'>
            <div style='flex: 1; padding: 1rem; border: 2px solid #ccc; border-radius: 10px; box-shadow: 2px 2px 6px rgba(0,0,0,0.2); background-color: {bg_color_total};'>
                <h4 style='margin: 0 0 0.5rem 0; color: {text_color_total};'>💵 Total Cost Saving</h4>
                <div style='font-size: 24px; font-weight: bold; color: {text_color_total};'>${delta_total:,.0f}</div>
            </div>
            <div style='flex: 1; padding: 1rem; border: 2px solid #ccc; border-radius: 10px; box-shadow: 2px 2px 6px rgba(0,0,0,0.2); background-color: {bg_color_ft};'>
                <h4 style='margin: 0 0 0.5rem 0; color: {text_color_ft};'>📏 Cost Per Foot Saving</h4>
                <div style='font-size: 24px; font-weight: bold; color: {text_color_ft};'>${delta_ft:,.2f}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 📊 Cost Breakdown Pie Charts")
    pie1, pie2 = st.columns(2)

    with pie1:
        derrick_fig = px.pie(
            names=["Dilution", "Haul", "Screen", "Equipment", "Engineering", "Other"],
            values=[derrick_cost[k] for k in ["Dilution", "Haul", "Screen", "Equipment", "Engineering", "Other"]],
            title="Derrick Cost Breakdown",
            color_discrete_sequence=["#1b5e20", "#2e7d32", "#388e3c", "#43a047", "#4caf50", "#66bb6a"]
        )
        derrick_fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(derrick_fig, use_container_width=True)

    with pie2:
        nond_fig = px.pie(
            names=["Dilution", "Haul", "Screen", "Equipment", "Engineering", "Other"],
            values=[nond_cost[k] for k in ["Dilution", "Haul", "Screen", "Equipment", "Engineering", "Other"]],
            title="Non-Derrick Cost Breakdown",
            color_discrete_sequence=["#424242", "#616161", "#757575", "#9e9e9e", "#bdbdbd", "#e0e0e0"]
        )
        nond_fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(nond_fig, use_container_width=True)

    st.markdown("#### 📉 Cost per Foot and Depth Comparison")
    bar1, bar2 = st.columns(2)

    with bar1:
        fig_cost = px.bar(summary, x="Label", y="Cost/ft", color="Label", title="Cost per Foot Comparison",
                          color_discrete_map={"Derrick": "#007635", "Non-Derrick": "grey"})
        st.plotly_chart(fig_cost, use_container_width=True)

    with bar2:
        fig_depth = px.bar(summary, x="Label", y="Depth", color="Label", title="Total Depth Drilled",
                           color_discrete_map={"Derrick": "#007635", "Non-Derrick": "grey"})
        st.plotly_chart(fig_depth, use_container_width=True)

# ------------------------- PAGE 4: Advanced Analysis -------------------------

from sales_analysis import render_sales_analysis
from multi_well_comparison import render_multi_well
from advanced_analysis import render_advanced_analysis

page = st.sidebar.radio("📂 Navigate", ["Multi-Well Comparison", "Sales Analysis", "Advanced Analysis", "Cost Estimator"])

if page == "Multi-Well Comparison":
    render_multi_well(df)
elif page == "Sales Analysis":
    render_sales_analysis(df)
elif page == "Advanced Analysis":
    render_advanced_analysis(df)
else:
    render_cost_estimator(df)

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
