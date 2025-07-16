import streamlit as st
import pandas as pd

st.set_page_config(page_title="Surge Campaign Builder", layout="wide")
st.title("🚀 Surge Campaign Builder (Milestone Surges)")

# 1. Upload Seed/OB File
st.markdown("### 1️⃣ Upload Seed File")
uploaded_file = st.file_uploader("Upload your Seed/Onboarding file (CSV)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip().str.upper()
    st.success("Seed file uploaded! Preview below 👇")
    st.dataframe(df.head(20))

    # 2. Filter Options
    st.markdown("### 2️⃣ Filter Your Data (Optional)")
    week_options = sorted(df["WEEK"].unique())
    selected_weeks = st.multiselect("Select Weeks", week_options, default=week_options[-1:])
    city_options = sorted(df["CITY"].dropna().unique())
    selected_cities = st.multiselect("Select Cities", city_options, default=city_options)
    zone_options = sorted(df["ZONE NAME"].dropna().unique())
    selected_zones = st.multiselect("Select Zones", zone_options, default=zone_options)
    shift_options = sorted(df["SHIFT NAME"].dropna().unique())
    selected_shifts = st.multiselect("Select Shifts", shift_options, default=shift_options)

    filtered_df = df[
        df["WEEK"].isin(selected_weeks) &
        df["CITY"].isin(selected_cities) &
        df["ZONE NAME"].isin(selected_zones) &
        df["SHIFT NAME"].isin(selected_shifts)
    ].copy()

    st.markdown(f"**{len(filtered_df)} DEs match your filter**")

    # 3. Set Up Milestone Surges
    st.markdown("### 3️⃣ Define Milestone Surges")
    st.info("Set milestones (e.g. 1st, 5th, 10th order) and payout for each. Add/remove as needed.")
    default_milestones = [{"milestone": 1, "amount": 25}, {"milestone": 5, "amount": 50}, {"milestone": 10, "amount": 100}]
    milestones = st.session_state.get("milestones", default_milestones)

    col_milestone, col_amount = st.columns(2)
    for i, ms in enumerate(milestones):
        col1, col2 = st.columns([3,2])
        ms["milestone"] = col1.number_input(f"Milestone #{i+1} (Order Count)", min_value=1, step=1, value=ms["milestone"], key=f"ms{i}")
        ms["amount"] = col2.number_input(f"Payout ₹ for Milestone #{i+1}", min_value=1, step=1, value=ms["amount"], key=f"amt{i}")

    # Add/Remove milestone logic
    col_add, col_remove = st.columns(2)
    if col_add.button("➕ Add Milestone"):
        milestones.append({"milestone": 1, "amount": 25})
        st.session_state["milestones"] = milestones
        st.experimental_rerun()
    if len(milestones) > 1 and col_remove.button("➖ Remove Last Milestone"):
        milestones.pop()
        st.session_state["milestones"] = milestones
        st.experimental_rerun()
    st.session_state["milestones"] = milestones

    # 4. Calculate Surge Payouts
    st.markdown("### 4️⃣ Surge Eligibility & Payout Table")
    result = filtered_df.copy()
    for ms in milestones:
        result[f"Milestone_{ms['milestone']}_Eligible"] = result["TOTAL ORDERS"] >= ms["milestone"]
        result[f"Milestone_{ms['milestone']}_Payout"] = result[f"Milestone_{ms['milestone']}_Eligible"].apply(lambda x: ms["amount"] if x else 0)
    # Total surge calculation
    payout_cols = [f"Milestone_{ms['milestone']}_Payout" for ms in milestones]
    result["Total_Surge_Payout"] = result[payout_cols].sum(axis=1)

    # Final display columns
    display_cols = ["WEEK", "DE ID", "DE NAME", "ONBOARDING DATE", "CITY", "ZONE NAME", "SHIFT NAME", "TOTAL ORDERS"] + payout_cols + ["Total_Surge_Payout"]
    st.dataframe(result[display_cols].sort_values("Total_Surge_Payout", ascending=False), use_container_width=True)
    st.download_button("📥 Download Surge Payout Table (CSV)", result[display_cols].to_csv(index=False), "milestone_surge_payouts.csv", mime="text/csv")

else:
    st.info("👆 Please upload a valid seed/onboarding CSV to get started!")

