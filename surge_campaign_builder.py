import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Smart Surge Planner", layout="wide")
st.title("⚡ Smart Surge Planner (Zone & Week Surge, Auto Milestone Logic)")

# 1. Upload Planning File (Zone-wise weekly summary)
st.header("📑 1️⃣ Upload Planning File (Zone/Week Summary)")
planning_file = st.file_uploader("Upload PLANNING (Zone-wise, weekly) file (CSV)", type=["csv"], key="plan_file")

if planning_file:
    plan_df = pd.read_csv(planning_file)
    plan_df.columns = plan_df.columns.str.strip().str.upper()
    st.success("Planning file uploaded! (Past week zone summary)")
    st.dataframe(plan_df.head(10))

    # Select week(s) to use for logic
    week_options = sorted(plan_df["WEEK"].unique())
    selected_weeks = st.multiselect(
        "Select Week(s) for Surge Basis", week_options, default=[week_options[-1]]
    )
    plan_df_filtered = plan_df[plan_df["WEEK"].isin(selected_weeks)].copy()

    st.markdown("### 📊 Zone-wise Metrics for Selected Weeks")
    st.dataframe(plan_df_filtered)

    # 2. Upload DE Data File (Seed/OB)
    st.header("🧑‍💼 2️⃣ Upload DE Data File (Seed/OB/Onboarding)")
    de_file = st.file_uploader("Upload DE DATA file (CSV)", type=["csv"], key="de_file")
    if de_file:
        de_df = pd.read_csv(de_file)
        de_df.columns = de_df.columns.str.strip().str.upper()
        st.success("DE file uploaded! (Onboarding/seed)")
        st.dataframe(de_df.head(10))

        # Filter DEs by selected weeks (ensure logic match)
        week_col = "WEEK"
        week_de_options = sorted(de_df[week_col].unique())
        selected_de_weeks = st.multiselect(
            "Filter DEs by Week", week_de_options, default=selected_weeks, key="de_week_select"
        )
        de_df = de_df[de_df[week_col].isin(selected_de_weeks)].copy()

        # City/zone/shift/order filters
        city_options = sorted(de_df["CITY"].dropna().unique())
        selected_cities = st.multiselect("Cities", city_options, default=city_options)
        zone_col = "ZONE" if "ZONE" in de_df.columns else "ZONE NAME"
        zone_options = sorted(de_df[zone_col].dropna().unique())
        selected_zones = st.multiselect("Zones", zone_options, default=zone_options)
        shift_col = "SHIFT" if "SHIFT" in de_df.columns else ("SHIFT NAME" if "SHIFT NAME" in de_df.columns else None)
        if shift_col:
            shift_options = sorted(de_df[shift_col].dropna().unique())
            selected_shifts = st.multiselect("Shifts", shift_options, default=shift_options)
        else:
            selected_shifts = []

        min_order = int(de_df["TOTAL ORDERS"].min())
        max_order = int(de_df["TOTAL ORDERS"].max())
        order_range = st.slider(
            "Filter DEs by Total Orders", min_value=min_order, max_value=max_order, value=(min_order, max_order)
        )

        # Apply all filters
        mask = (
            de_df["CITY"].isin(selected_cities) &
            de_df[zone_col].isin(selected_zones) &
            (de_df["TOTAL ORDERS"] >= order_range[0]) &
            (de_df["TOTAL ORDERS"] <= order_range[1])
        )
        if shift_col:
            mask &= de_df[shift_col].isin(selected_shifts)
        de_df_final = de_df[mask].copy()
        st.markdown(f"**{len(de_df_final)} DEs match your filter**")
        st.dataframe(de_df_final.head(20))

        # 3. Milestone Suggestion (per zone, from planning file)
        st.header("🎯 3️⃣ Milestone Surge Recommendation (Zone-Based)")
        st.info("App auto-suggests 1st/5th/10th order targets & payout by zone (edit as needed).")

        milestone_setup = []
        for _, row in plan_df_filtered.iterrows():
            city = row["CITY"]
            zone = row["ZONE"]
            total_orders = row.get("TOTAL_ORDERS", 0)
            de_count = row.get("DE_COUNT", 1)
            median_orders = row.get("MEDIAN_ORDERS", max(1, total_orders // max(de_count, 1)))
            pct_10plus = row.get("% DES >10 ORDERS", None)
            default_1st = 1
            default_5th = max(2, int(np.percentile([median_orders], 50)))
            default_10th = 10 if pct_10plus and pct_10plus > 10 else max(5, median_orders + 1)
            with st.expander(f"{city} – {zone}", expanded=False):
                m1 = st.number_input(f"[{city}-{zone}] Milestone 1st Order Target", min_value=1, max_value=100, value=default_1st, key=f"{city}_{zone}_m1")
                p1 = st.number_input(f"[{city}-{zone}] 1st Order Payout ₹", min_value=1, max_value=1000, value=25, key=f"{city}_{zone}_p1")
                m2 = st.number_input(f"[{city}-{zone}] 2nd Milestone Target", min_value=1, max_value=100, value=default_5th, key=f"{city}_{zone}_m2")
                p2 = st.number_input(f"[{city}-{zone}] 2nd Payout ₹", min_value=1, max_value=1000, value=50, key=f"{city}_{zone}_p2")
                m3 = st.number_input(f"[{city}-{zone}] 3rd Milestone Target", min_value=1, max_value=100, value=default_10th, key=f"{city}_{zone}_m3")
                p3 = st.number_input(f"[{city}-{zone}] 3rd Payout ₹", min_value=1, max_value=1000, value=100, key=f"{city}_{zone}_p3")
                milestone_setup.append({
                    "city": city, "zone": zone,
                    "milestones": [
                        {"order": m1, "payout": p1},
                        {"order": m2, "payout": p2},
                        {"order": m3, "payout": p3},
                    ]
                })

        # 4. Calculate Payouts
        st.header("💰 4️⃣ Final Surge Payout Table")
        payout_records = []
        for _, de in de_df_final.iterrows():
            city = de["CITY"]
            zone = de[zone_col]
            orders = de["TOTAL ORDERS"]
            matched = None
            for setup in milestone_setup:
                if setup["city"] == city and setup["zone"] == zone:
                    matched = setup["milestones"]
                    break
            if not matched:
                matched = milestone_setup[0]["milestones"]  # fallback
            de_row = dict(de)
            total_payout = 0
            for i, ms in enumerate(matched):
                eligible = orders >= ms["order"]
                payout = ms["payout"] if eligible else 0
                de_row[f"Milestone_{ms['order']}_Eligible"] = eligible
                de_row[f"Milestone_{ms['order']}_Payout"] = payout
                total_payout += payout
            de_row["Total_Surge_Payout"] = total_payout
            payout_records.append(de_row)
        if payout_records:
            payout_df = pd.DataFrame(payout_records)
            payout_cols = [c for c in payout_df.columns if c.startswith("Milestone_") and c.endswith("_Payout")]
            display_cols = [
                "WEEK", "DE ID", "DE NAME", "ONBOARDING DATE", "CITY", zone_col,
                "SHIFT" if "SHIFT" in payout_df.columns else ("SHIFT NAME" if "SHIFT NAME" in payout_df.columns else None),
                "TOTAL ORDERS"
            ] + payout_cols + ["Total_Surge_Payout"]
            display_cols = [c for c in display_cols if c is not None and c in payout_df.columns]
            st.dataframe(payout_df[display_cols].sort_values("Total_Surge_Payout", ascending=False), use_container_width=True)
            st.download_button(
                "📥 Download Surge Payout Table (CSV)",
                payout_df[display_cols].to_csv(index=False),
                "surge_payout_plan.csv",
                mime="text/csv"
            )
    else:
        st.info("👉 Please upload the DE/seed/onboarding file to proceed.")
else:
    st.info("👆 Upload the Planning File (Zone/Week) to get started!")

