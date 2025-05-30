
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

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
    kpi_icons = {
        "STE": "📈", "CVR": "🧱", "SLI": "📊", "FRC%": "💧", "DII": "⛏️",
        "FLI": "🔄", "CDR": "🧪", "MRE%": "♻️", "DSL": "🚧"
    }
    units = {
        "FRC%": "%", "MRE%": "%"
    }

    cols = st.columns(3)
    for idx, (metric, value) in enumerate(metrics.items()):
        color = "green" if value >= 0 else "red"
        label = f"{kpi_icons.get(metric, '')} {metric}"
        display_val = f"{value:.2f}{units.get(metric, '')}"
        with cols[idx % 3]:
            st.markdown(f"""
                <div style="border: 2px solid #ccc; border-radius: 12px; box-shadow: 2px 2px 8px rgba(0,0,0,0.1); padding: 16px; background-color: #f9f9f9;">
                    <h4 style="margin-bottom:8px;">{label}</h4>
                    <span style="color:{color}; font-size: 22px; font-weight:bold;">{display_val}</span>
                </div>
            """, unsafe_allow_html=True)

def render_advanced_charts(df):
    st.subheader("📈 Advanced Metric Visuals")

    metric_options = ["STE", "CVR", "SLI", "FRC%", "DII", "FLI", "CDR", "MRE%", "DSL"]
    metric_choice = st.selectbox("Select Metric to Compare", metric_options)

    if metric_choice in df.columns:
        fig1 = px.box(df, x="flowline_Shakers", y=metric_choice, color="flowline_Shakers", title=f"{metric_choice} by Shaker")
        fig2 = px.box(df, x="Well_Name", y=metric_choice, color="Well_Name", title=f"{metric_choice} by Well")

        col1, col2 = st.columns(2)
        col1.plotly_chart(fig1, use_container_width=True)
        col2.plotly_chart(fig2, use_container_width=True)

def render_advanced_analysis(df):
    st.title("📌 Advanced Analysis Dashboard")

    st.sidebar.header("🔍 Filter Data")
    selected_shakers = st.sidebar.multiselect("Shakers", df["flowline_Shakers"].dropna().unique())
    selected_wells = st.sidebar.multiselect("Well Names", df["Well_Name"].dropna().unique())

    filtered_df = df.copy()
    if selected_shakers:
        filtered_df = filtered_df[filtered_df["flowline_Shakers"].isin(selected_shakers)]
    if selected_wells:
        filtered_df = filtered_df[filtered_df["Well_Name"].isin(selected_wells)]

    metrics = calculate_advanced_metrics(filtered_df)
    render_kpi_board(metrics)

    render_advanced_charts(filtered_df)

    st.subheader("📤 Export Options")
    if st.button("Download Filtered Data as CSV"):
        st.download_button("Download", filtered_df.to_csv(index=False), "filtered_data.csv", "text/csv")
