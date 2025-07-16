import streamlit as st
import pandas as pd

st.set_page_config(page_title="Surge Campaign Builder", layout="wide")
st.title("🚀 Surge Campaign Builder (with Planning File Upload)")

# --- 1. Upload Files ---
st.markdown("### 1️⃣ Upload Planning File (Zone-Weekly) & DE Data File (DE-wise)")
planning_file = st.file_uploader("Upload Planning File (Zone/City/Week level, CSV)", type=["csv"], key="plan_file")
de_file = st.file_uploader("Upload DE Data File (DE/Week level, CSV)", type=["csv"], key="de_file")

planning_df = None
de_df = None

if planning_file:
    planning_df = pd.read_csv(planning_file)
    planning_df.columns = planning_df.columns.str.strip().str.upper()
    st.success("Planning File uploaded! Preview below 👇")
    st.dataframe(planning_df.head(10), use_container_width=True)
if de_file:
    de_df = pd.read_csv(de_file)
    de_df.columns = de_df.columns.str.strip().str.upper()
    st.success("DE Data File uploaded! Preview below 👇")
    st.dataframe(de_df.head(10), use_container_width=True)

if planning_df is not None and de_df is not None:
    week_col = "WEEK"

    # ---- 2. Select Weeks ----
    week_plan_options = sorted(planning_df[week_col].unique())
    week_de_options = sorted(de_df[week_col].unique())

    st.markdown("### 2️⃣ Week Selection for Surge Planning")
    week_select_method = st.radio(
        "Choose which week's data to base your surge on:",
        ["Planning File weeks", "DE Data weeks", "Both"],
        index=2
    )

    if week_select_method == "Planning File weeks":
        selected_weeks = st.multiselect(
            "Select Week(s) from Planning File",
            week_plan_options,
            default=week_plan_options[-1:]
        )
    elif week_select_method == "DE Data weeks":
        selected_weeks = st.multiselect(
            "Select Week(s) from DE Data File",
            week_de_options,
            default=week_de_options[-1:]
        )
    else:
        all_weeks = sorted(set(week_plan_options) | set(week_de_options))
        selected_weeks = st.multiselect(
            "Select Week(s) (All available in both files)",
            all_weeks,
            default=all_weeks[-1:]
        )

    # --- Safe DE week filter ---
    safe_default_weeks = [w for w in selected_weeks if w in week_de_options]
    if not safe_default_weeks and week_de_options:
        safe_default_weeks = week_de_options[-1:]

    selected_de_weeks = st.multiselect(
        "Filter DEs by Week (for DE Data File)",
        week_de_options,
        default=safe_default_weeks,
        key="de_week_select"
    )

    # --- Filter data as needed ---
    filtered_de_df = de_df[de_df[week_col].isin(selected_de_weeks)].copy()
    filtered_planning_df = planning_df[planning_df[week_col].isin(selected_weeks)].copy()

    st.markdown(f"**{len(filtered_de_df)} DE rows for selected week(s)**")
    st.markdown(f"**{len(filtered_planning_df)} Planning rows for selected week(s)**")
    st.dataframe(filtered_de_df.head(10))
    st.dataframe(filtered_planning_df.head(10))

    # ---- 3. Example logic: show summary stats ----
    st.markdown("### 3️⃣ Zone-Weekly Summary (from Planning File)")
    if not filtered_planning_df.empty:
        zone_summary_cols = ["CITY", "ZONE", "WEEK", "DE_COUNT", "TOTAL_ORDERS"]
        for col in zone_summary_cols:
            if col not in filtered_planning_df.columns:
                zone_summary_cols.remove(col)
        st.dataframe(filtered_planning_df[zone_summary_cols], use_container_width=True)
    else:
        st.info("No rows in Planning file for selected week(s).")

    st.markdown("### 4️⃣ DE List (from DE Data File, Filtered by Week)")
    if not filtered_de_df.empty:
        de_list_cols = ["DE ID", "DE NAME", "WEEK", "CITY", "ZONE", "TOTAL ORDERS"]
        for col in de_list_cols:
            if col not in filtered_de_df.columns:
                de_list_cols.remove(col)
        st.dataframe(filtered_de_df[de_list_cols], use_container_width=True)
    else:
        st.info("No DE data for selected week(s).")

    st.markdown("---")
    st.info("🔧 Add your surge logic and milestone payout logic below using these filtered DataFrames.")

else:
    st.warning("Please upload BOTH Planning File and DE Data file to proceed.")

