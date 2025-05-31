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
                    selected = st.selectbox(col.replace("_", " "), options)
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
                    selected = st.selectbox("Depth Range", ["All"] + list(depth_bins.keys()))
                    if selected != "All":
                        low, high = depth_bins[selected]
                        df = df[(df["MD Depth"] >= low) & (df["MD Depth"] < high)]
                if "AMW" in df:
                    mw_bins = {
                        "<3": (0, 3), "3–6": (3, 6), "6–9": (6, 9), "9–12": (9, 12), ">12": (12, float("inf"))
                    }
                    selected = st.selectbox("Mud Weight", ["All"] + list(mw_bins.keys()))
                    if selected != "All":
                        low, high = mw_bins[selected]
                        df = df[(df["AMW"] >= low) & (df["AMW"] < high)]
    return df

# ------------------------- PAGES -------------------------
def render_multi_well(df):
    st.title("🚀 Prodigy IQ Multi-Well Dashboard")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("📏 IntLength", f"{df['IntLength'].mean():.1f}")
    col2.metric("🏃 ROP", f"{df['ROP'].mean():.1f}")
    col3.metric("🧪 Dilution Ratio", f"{df['Dilution_Ratio'].mean():.2f}")
    col4.metric("🧴 Discard Ratio", f"{df['Discard Ratio'].mean():.2f}")
    col5.metric("🚛 Haul OFF", f"{df['Haul_OFF'].mean():.1f}")
    col6.metric("🌡️ AMW", f"{df['AMW'].mean():.2f}")

    metric = st.selectbox("Select Metric", df.select_dtypes(include='number').columns.drop(["Well_Coord_Lon", "Well_Coord_Lat"]))
    if metric:
        fig = px.bar(df, x="Well_Name", y=metric, color="Operator")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("🗺️ Well Map")
    fig_map = px.scatter_mapbox(df.dropna(subset=["Well_Coord_Lon", "Well_Coord_Lat"]),
                                 lat="Well_Coord_Lat", lon="Well_Coord_Lon", hover_name="Well_Name",
                                 zoom=4, height=500)
    fig_map.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig_map, use_container_width=True)

def render_sales_analysis(df):
    st.title("📈 Prodigy IQ Sales Intelligence")
    df["Month"] = df["TD_Date"].dt.to_period("M").astype(str)
    volume = df.groupby("Month").size().reset_index(name="Well Count")
    st.plotly_chart(px.bar(volume, x="Month", y="Well Count"), use_container_width=True)

    avg_discard = df.groupby("Contractor")["Discard Ratio"].mean().reset_index()
    st.plotly_chart(px.bar(avg_discard, x="Contractor", y="Discard Ratio", color="Contractor"), use_container_width=True)

    fluid_df = df.groupby("Operator")[["Base_Oil", "Water", "Chemicals"]].sum().reset_index()
    fluid_df = fluid_df.melt(id_vars="Operator", var_name="Fluid", value_name="Volume")
    st.plotly_chart(px.bar(fluid_df, x="Operator", y="Volume", color="Fluid", barmode="group"), use_container_width=True)

def render_advanced_analysis(df):
    st.title("📌 Advanced Analysis Dashboard")
    total_flow_rate = st.sidebar.number_input("Total Flow Rate (GPM)", value=800)
    number_of_screens = st.sidebar.number_input("Screens Installed", value=3)
    screen_area = st.sidebar.number_input("Area per Screen (sq ft)", value=2.0)
    unit = st.sidebar.radio("Normalize by", ["None", "Feet", "Hours", "Days"])

    def safe_div(a, b): return a / b if b else 0

    rows = []
    for _, r in df.iterrows():
        rows.append({
            "Well_Name": r.get("Well_Name", ""),
            "Operator": r.get("Operator", ""),
            "STE": safe_div(r.get("Total_SCE", 0), r.get("Total_SCE", 0)) * 100,
            "CVR": safe_div(r.get("Haul_OFF", 0), r.get("IntLength", 0)),
            "SLI": safe_div(total_flow_rate, number_of_screens * screen_area),
            "FRC%": safe_div(r.get("Total_SCE", 0), r.get("Total_SCE", 0)) * 100,
            "DII": safe_div(r.get("ROP", 0), r.get("Hole_Size", 1)),
            "FLI": safe_div(r.get("Base_Oil", 0) + r.get("Water", 0) + r.get("Chemicals", 0), r.get("IntLength", 0)),
            "CDR": safe_div(r.get("Chemicals", 0), r.get("IntLength", 0)),
            "MRE%": 100 - safe_div(r.get("Total_SCE", 0), r.get("Total_SCE", 0)) * 100,
            "DSL": 100 - safe_div(r.get("Total_SCE", 0), r.get("Total_SCE", 0)) * 100
        })
    metric_df = pd.DataFrame(rows)

    if unit != "None":
        total = df["IntLength"].sum() if unit == "Feet" else df["Drilling_Hours"].sum() if unit == "Hours" else safe_div(df["Drilling_Hours"].sum(), 24)
        for col in metric_df.columns[2:]:
            metric_df[col] = metric_df[col].apply(lambda x: safe_div(x, total))

    st.subheader("📋 KPI Summary")
    kpi_cols = st.columns(3)
    for i, col in enumerate(metric_df.columns[2:]):
        with kpi_cols[i % 3]:
            st.metric(col, f"{metric_df[col].mean():.2f}")

    selected = st.selectbox("Select Metric", metric_df.columns[2:])
    st.plotly_chart(px.bar(metric_df, x="Well_Name", y=selected, color="Operator"), use_container_width=True)

def render_cost_estimator(df):
    st.title("💰 Flowline Shaker Cost Comparison")
    col1, col2 = st.columns(2)
    with col1:
        derrick_config = get_cost_input("d")
    with col2:
        non_config = get_cost_input("nd")

    derrick_cost = calc_cost(df, derrick_config, "Derrick")
    nond_cost = calc_cost(df, non_config, "Non-Derrick")
    summary = pd.DataFrame([derrick_cost, nond_cost])

    st.metric("💰 Total Saving", f"${nond_cost['Total Cost'] - derrick_cost['Total Cost']:.0f}")
    st.metric("📏 Cost/ft Saving", f"${nond_cost['Cost/ft'] - derrick_cost['Cost/ft']:.2f}")

    st.plotly_chart(px.pie(summary.query("Label == 'Derrick'"), names=["Dilution", "Haul", "Screen", "Equipment"], values=[derrick_cost[k] for k in ["Dilution", "Haul", "Screen", "Equipment"]]), use_container_width=True)
    st.plotly_chart(px.pie(summary.query("Label == 'Non-Derrick'"), names=["Dilution", "Haul", "Screen", "Equipment"], values=[nond_cost[k] for k in ["Dilution", "Haul", "Screen", "Equipment"]]), use_container_width=True)

def get_cost_input(prefix):
    return {
        "dil_rate": st.number_input("Dilution Cost $", value=100, key=prefix+"_dil"),
        "haul_rate": st.number_input("Haul Cost $", value=20, key=prefix+"_haul"),
        "screen_price": st.number_input("Screen Price $", value=500, key=prefix+"_scr"),
        "num_screens": st.number_input("Screens Count", value=2, key=prefix+"_sc"),
        "equip_cost": st.number_input("Equip Cost $", value=100000, key=prefix+"_eq"),
        "num_shakers": st.number_input("Shakers Installed", value=3, key=prefix+"_shk"),
        "shaker_life": st.number_input("Shaker Life (Yrs)", value=7, key=prefix+"_life"),
        "eng_cost": st.number_input("Engineer Day Rate $", value=1000, key=prefix+"_eng"),
        "other_cost": st.number_input("Other Cost $", value=500, key=prefix+"_oth")
    }

def calc_cost(df, cfg, label):
    intlen = df["IntLength"].fillna(0).sum()
    td = df["Total_Dil"].fillna(0).sum()
    ho = df["Haul_OFF"].fillna(0).sum()
    total = cfg["dil_rate"] * td + cfg["haul_rate"] * ho + cfg["screen_price"] * cfg["num_screens"] + (cfg["equip_cost"] * cfg["num_shakers"] / cfg["shaker_life"]) + cfg["eng_cost"] + cfg["other_cost"]
    return {"Label": label, "Total Cost": total, "Cost/ft": total/intlen if intlen else 0, "Dilution": td, "Haul": ho, "Screen": cfg["screen_price"] * cfg["num_screens"], "Equipment": cfg["equip_cost"]}

# ------------------------- LOAD DATA -------------------------
load_styles()
df = pd.read_csv("Refine Sample.csv")
df["TD_Date"] = pd.to_datetime(df["TD_Date"], errors='coerce')

# ------------------------- MAIN NAV -------------------------
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
