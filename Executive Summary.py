def render_executive_summary(df):
    st.title("📄 Executive Summary")

    filtered_df = apply_shared_filters(df)
    total_wells = filtered_df["Well_Name"].nunique()
    avg_rop = filtered_df["ROP"].mean()
    avg_amw = filtered_df["AMW"].mean()
    avg_dil = filtered_df["Dilution_Ratio"].mean()
    avg_discard = filtered_df["Discard Ratio"].mean()

    top_well = filtered_df.loc[filtered_df["ROP"].idxmax()]
    low_well = filtered_df.loc[filtered_df["ROP"].idxmin()]

    st.markdown(f\"\"\"\n### 🛠️ Drilling Performance Overview\n- Total Wells: **{total_wells}**\n- Average ROP: **{avg_rop:.1f} ft/hr**\n- Average Mud Weight: **{avg_amw:.2f} ppg**\n- Avg Dilution Ratio: **{avg_dil:.2f}**\n- Avg Discard Ratio: **{avg_discard:.2f}**\n\n### 🔍 ROP Extremes\n- **Fastest Well**: `{top_well['Well_Name']}` @ **{top_well['ROP']:.1f} ft/hr**\n- **Slowest Well**: `{low_well['Well_Name']}` @ **{low_well['ROP']:.1f} ft/hr**\n\"\"\")

    # Optional: Export
    summary_text = f\"Exec Summary for {total_wells} wells\\nAvg ROP: {avg_rop:.1f}\\n...\"\n    st.download_button(\"📥 Download Summary\", summary_text, file_name=\"executive_summary.txt\")\n```

---

## 🔄 Optional Add-ons
- 📤 **Email integration** (via SMTP or SendGrid)
- 📎 **PDF export** (with logos and branded formatting)
- ⏰ **Auto-generate per week/month** and attach to report emails

---

Would you like me to build this into your app as a new page called **“Executive Summary”** right now? I can add it as the 5th tab.
