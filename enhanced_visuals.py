# ==================== ENHANCED VISUALS MODULE ====================
# These functions extend your Prodigy IQ Dashboard with more advanced charts

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd

def radar_chart_multi_kpi(filtered_df):
    st.subheader("🕸️ Multi-KPI Radar Comparison")
    radar_metrics = ["ROP", "Dilution_Ratio", "Discard Ratio", "AMW", "Haul_OFF"]
    radar_df = filtered_df.groupby("Well_Name")[radar_metrics].mean().reset_index()
    selected_wells = st.multiselect("Select Wells for Radar Chart", radar_df["Well_Name"].unique(), default=radar_df["Well_Name"].unique()[:3])
    radar_data = radar_df[radar_df["Well_Name"].isin(selected_wells)]
    fig = go.Figure()
    for _, row in radar_data.iterrows():
        fig.add_trace(go.Scatterpolar(r=row[radar_metrics].values, theta=radar_metrics, fill='toself', name=row["Well_Name"]))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

def cumulative_wells_chart(volume):
    st.subheader("📈 Cumulative Wells Over Time")
    volume["Cumulative Wells"] = volume["Well Count"].cumsum()
    fig = px.line(volume, x="Month", y="Cumulative Wells", markers=True, title="Cumulative Wells Drilled")
    st.plotly_chart(fig, use_container_width=True)

def fluid_pie_chart_by_operator(fluid_df):
    op_choice = st.selectbox("Select Operator", fluid_df["Operator"].unique())
    op_data = fluid_df[fluid_df["Operator"] == op_choice].groupby("Fluid")["Volume"].sum().reset_index()
    fig = px.pie(op_data, names="Fluid", values="Volume", title=f"Fluid Composition for {op_choice}")
    st.plotly_chart(fig, use_container_width=True)

def kpi_heatmap(metric_df):
    st.subheader("🌡️ KPI Heatmap Across Wells")
    heat_df = metric_df.set_index("Well_Name").select_dtypes(include='number')
    fig = px.imshow(heat_df.T, aspect="auto", color_continuous_scale="Viridis")
    fig.update_layout(yaxis_title="KPIs", xaxis_title="Well Name")
    st.plotly_chart(fig, use_container_width=True)

def kpi_boxplot(metric_df):
    st.subheader("📦 KPI Distribution by Operator")
    selected_kpi = st.selectbox("Select KPI for Box Plot", metric_df.columns[2:], key="box_kpi")
    fig = px.box(metric_df, x="Operator", y=selected_kpi, points="all", title=f"{selected_kpi} by Operator")
    st.plotly_chart(fig, use_container_width=True)

def stacked_cost_chart(summary):
    st.subheader("🔄 Stacked Cost Structure")
    cost_melt = summary.melt(id_vars="Label", value_vars=["Dilution", "Haul", "Screen", "Equipment", "Engineering", "Other"], 
                             var_name="Component", value_name="Amount")
    fig = px.bar(cost_melt, x="Label", y="Amount", color="Component", title="Cost Component Breakdown (Stacked)",
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig, use_container_width=True)

# ==================== PAGE INTEGRATION (TO CALL INSIDE EXISTING PAGES) ====================
# Inside render_multi_well(df):
#     radar_chart_multi_kpi(filtered_df)

# Inside render_sales_analysis(df):
#     cumulative_wells_chart(volume)
#     fluid_pie_chart_by_operator(fluid_df)

# Inside render_advanced_analysis(df):
#     kpi_heatmap(metric_df)
#     kpi_boxplot(metric_df)

# Inside render_cost_estimator(df):
#     stacked_cost_chart(summary)
