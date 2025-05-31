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
    .filter-tabs { background: #fafafa; padding: 0.5em; border-radius: 10px; margin-bottom: 1em; }
    .filter-tabs button {
        margin: 0 0.25em;
        padding: 0.4em 0.8em;
        border: none;
        border-radius: 8px;
        background-color: #d6d8db;
        font-weight: 600;
        cursor: pointer;
    }
    .filter-tabs button:hover {
        background-color: #c0c2c5;
    }
    .filter-tabs .active {
        background-color: #6c757d;
        color: white;
    }
    </style>""", unsafe_allow_html=True)

# ------------------------- FILTER PANEL WITH TOGGLE -------------------------
def render_filter_panel(df):
    with st.sidebar:
        filter_mode = st.radio("🧰 Filter Mode", ["Global", "Common", "Advanced"], horizontal=True)

        if filter_mode == "Global":
            with st.expander("🌐 Global Filters", expanded=True):
                well_filter = st.multiselect("Select Well(s)", sorted(df["Well_Name"].dropna().unique()), key="f1")
                if well_filter:
                    df = df[df["Well_Name"].isin(well_filter)]

        elif filter_mode == "Common":
            with st.expander("🔁 Common Filters", expanded=True):
                shaker_filter = st.selectbox("Flowline Shaker", ["All"] + sorted(df["flowline_Shakers"].dropna().unique()), key="f2")
                if shaker_filter != "All":
                    df = df[df["flowline_Shakers"] == shaker_filter]

                operator_filter = st.selectbox("Operator", ["All"] + sorted(df["Operator"].dropna().unique()), key="f3")
                if operator_filter != "All":
                    df = df[df["Operator"] == operator_filter]

                contractor_filter = st.selectbox("Contractor", ["All"] + sorted(df["Contractor"].dropna().unique()), key="f4")
                if contractor_filter != "All":
                    df = df[df["Contractor"] == contractor_filter]

        elif filter_mode == "Advanced":
            with st.expander("⚙️ Advanced Filters", expanded=True):
                year_range = st.slider("TD Date Range", 2020, 2026, (2020, 2026))
                df["TD_Date"] = pd.to_datetime(df["TD_Date"], errors='coerce')
                df = df[df["TD_Date"].dt.year.between(year_range[0], year_range[1])]

    return df
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

# ------------------------- PAGE: COST ESTIMATOR -------------------------
def render_cost_estimator(df):
    st.title("💰 Flowline Shaker Cost Comparison")
    df = render_filter_panel(df)

    col_d, col_nd = st.columns(2)
    with col_d:
        st.markdown("#### 🟩 Derrick Setup")
    with col_nd:
        st.markdown("#### 🟣 Non-Derrick Setup")

    derrick_config, nond_config = {}, {}

    with st.expander("🎯 Derrick Configuration"):
        derrick_config = get_config("d")
    with st.expander("🎯 Non-Derrick Configuration"):
        nond_config = get_config("nd")

    derrick_cost = calc_cost(df, derrick_config, "Derrick")
    nond_cost = calc_cost(df, nond_config, "Non-Derrick")
    summary = pd.DataFrame([derrick_cost, nond_cost])

    delta_total = nond_cost['Total Cost'] - derrick_cost['Total Cost']
    delta_ft = nond_cost['Cost/ft'] - derrick_cost['Cost/ft']

    st.markdown("### 💡 Summary KPIs")
    k1, k2 = st.columns(2)
    with k1:
        st.metric("💵 Total Cost Saving", f"${delta_total:,.0f}", delta_color="inverse")
    with k2:
        st.metric("📏 Cost/ft Saving", f"${delta_ft:,.2f}", delta_color="inverse")

    st.markdown("### 📊 KPI Breakdown")
    st.dataframe(summary.style.format("{:.2f}"))

    pie1, pie2 = st.columns(2)
    with pie1:
        fig_d = px.pie(summary.query("Label == 'Derrick'"), names=["Dilution", "Haul", "Screen", "Equipment", "Engineering", "Other"], 
                       values=[derrick_cost[k] for k in ["Dilution", "Haul", "Screen", "Equipment", "Engineering", "Other"]],
                       title="Derrick Breakdown")
        st.plotly_chart(fig_d, use_container_width=True)
    with pie2:
        fig_nd = px.pie(summary.query("Label == 'Non-Derrick'"), names=["Dilution", "Haul", "Screen", "Equipment", "Engineering", "Other"],
                        values=[nond_cost[k] for k in ["Dilution", "Haul", "Screen", "Equipment", "Engineering", "Other"]],
                        title="Non-Derrick Breakdown")
        st.plotly_chart(fig_nd, use_container_width=True)

    st.markdown("### 📈 Charts")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.bar(summary, x="Label", y="Cost/ft", color="Label", title="Cost per Foot"), use_container_width=True)
    with c2:
        st.plotly_chart(px.bar(summary, x="Label", y="Depth", color="Label", title="Total Depth"), use_container_width=True)

# ------------------------- CONFIG FUNCTION -------------------------
def get_config(prefix):
    return {
        "dil_rate": st.number_input("Dilution Cost Rate ($/unit)", value=100, key=f"{prefix}_dil"),
        "haul_rate": st.number_input("Haul-Off Cost Rate ($/unit)", value=20, key=f"{prefix}_haul"),
        "screen_price": st.number_input("Screen Price", value=500, key=f"{prefix}_scr_price"),
        "num_screens": st.number_input("Screens used per rig", value=1, key=f"{prefix}_scr_cnt"),
        "equip_cost": st.number_input("Total Equipment Cost", value=100000, key=f"{prefix}_equip"),
        "num_shakers": st.number_input("Number of Shakers Installed", value=3, key=f"{prefix}_shkrs"),
        "shaker_life": st.number_input("Shaker Life (Years)", value=7, key=f"{prefix}_life"),
        "eng_cost": st.number_input("Engineering Day Rate", value=1000, key=f"{prefix}_eng"),
        "other_cost": st.number_input("Other Cost", value=500, key=f"{prefix}_other")
    }

# ------------------------- CALC FUNCTION -------------------------
def calc_cost(sub_df, config, label):
    try:
        td = sub_df["Total_Dil"].fillna(0).sum()
        ho = sub_df["Haul_OFF"].fillna(0).sum()
        intlen = sub_df["IntLength"].fillna(0).sum()
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
    except Exception as e:
        st.error(f"Calculation error for {label}: {e}")
        return {"Label": label, "Cost/ft": 0, "Total Cost": 0, "Dilution": 0, "Haul": 0, "Screen": 0, "Equipment": 0,
                "Engineering": 0, "Other": 0, "Avg LGS%": 0, "DSRE%": 0, "Depth": 0}

# ------------------------- LOAD DATA -------------------------
load_styles()
df = pd.read_csv("Refine Sample.csv")
df["TD_Date"] = pd.to_datetime(df["TD_Date"], errors='coerce')

# ------------------------- MAIN NAVIGATION -------------------------
page = st.sidebar.radio("📂 Navigate", ["Multi-Well Comparison", "Sales Analysis", "Advanced Analysis", "Cost Estimator"])

if page == "Cost Estimator":
    render_cost_estimator(df)
elif page == "Multi-Well Comparison":
    df_filtered = render_filter_panel(df)
    render_multi_well(df_filtered)
elif page == "Sales Analysis":
    df_filtered = render_filter_panel(df)
    render_sales_analysis(df_filtered)
elif page == "Advanced Analysis":
    df_filtered = render_filter_panel(df)
    render_advanced_analysis(df_filtered)

# NOTE: All pages now use consistent filters and layout styling.
