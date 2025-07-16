import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Smart Surge Planner", layout="wide")
st.title("⚡ Smart Surge Planner (Zone, Week & Milestone Based)")

# 1. Upload Zone-Wise Weekly Summary
st.header("📈 1️⃣ Upload Zone-wise Weekly Summary File")
zone_file = st.file_uploader("Upload your ZONE weekly summary (CSV)", type=["csv"], key="zone_file")
if zone_file:
    zone_df = pd.read_csv(zone_file)
    zone_df.columns = zone_df.columns.str.strip().str.upper()
    st.success("Zone file uploaded!")
    st.dataframe(zone_df.head(10))

    week_options = sorted(zone_df["WEEK"].unique())
    st.markdown("### 👇 Available Weeks in Zone File:")
    st.write(", ".join([str(w) for w in week_options]))

    # Week selection for surge logic
    week_choice = st.multiselect(
        "Select week(s) to base your surge plan on", 
        week_options, 
        default=[week_options[-1]]
    )

    # Aggregate for chosen weeks
    filtered_zone = zone_df[zone_df["WEEK"].isin(week_choice)].copy()

    # Show summary
    st.markdown("### 📊 Zone-wise Metrics (Selected Weeks)")
    st.dataframe(filtered_zone)

# 2. Upload DE/Seed/OB File
st.header("🧑‍💼 2️⃣ Upload Seed/DE/Onboarding File")
seed_file = st.file_uploader("Upload your DE seed/onboarding file (CSV)", type=["csv"], key="seed_file")
if seed_file:
    de_df = pd.read_csv(seed_file)
    de_df.columns = de_df.columns.str.strip().str.upper()
    st.success("Seed/DE file uploaded!")
    st.dataframe(de_df.head(10))

    # Filter DEs by selected weeks
    if zone_file:
        week_filter = st.multiselect(
            "Filter DEs by Week", 
            week_options, 
            default=week_choice,
            key="seed_week_select"
        )
        de_filtered = de_df[de_df["WEEK"].isin(week_filter)].copy()
    else:
        week_filter = sorted(de_df["WEEK"].unique())
        de_filtered = de_df.copy()

    # City/zone/shift filters
    city_options = sorted(de_filtered["CITY"].dropna().unique())
    selected_cities = st.multiselect("Cities", city_options, default=city_options)
    zone_options = sorted(de_filtered["ZONE"].dropna().unique() if "ZONE" in de_filtered.columns else de_filtered["ZONE NAME"].dropna().unique())
    zone_col = "ZONE" if "ZONE" in de_filtered.columns else "ZONE NAME"
    selected_zones = st.multiselect("Zones", zone_options, default=zone_options)
    shift_col = "SHIFT" if "SHIFT" in de_filtered.columns else ("SHIFT NAME" if "SHIFT NAME" in de_filtered.columns else None)
    if shift_col:
        shift_options = sorted(de_filtered[shift_col].dropna().unique())
        selected_shifts = st.multiselect("Shifts", shift_options, default=shift_options)
    else:
        selected_shifts = []

    # Order count filter
    min_order = int(de_filtered["TOTAL ORDERS"].min())
    max_order = int(de_filtered["TOTAL ORDERS"].max())
    order_range = st.slider(
        "Filter DEs by Total Orders", min_value=min_order, max_value=max_order, value=(min_order, max_order)
    )

    # Apply all filters
    mask = (
        de_filtered["CITY"].isin(selected_cities) &
        de_filtered[zone_col].isin(selected_zones) &
        (de_filtered["TOTAL ORDERS"] >= order_range[0]) &
        (de_filtered["TOTAL ORDERS"] <= order_range[1])
    )
    if shift_col:
        mask &= de_filtered[shift_col].isin(selected_shifts)
    de_final = de_filtered[mask].copy()
    st.markdown(f"**{len(de_final)} DEs match your filter**")
    st.dataframe(de_final.head(20))

    # 3. Milestone Planning (Auto suggest per zone)
    st.header("🎯 3️⃣ Milestone Surge Recommendation")
    st.info("App suggests milestone targets/payouts based on actual zone demand, but you can override below.")

    milestone_setup = []
    if zone_file:
        # Loop each (city,zone) in filtered_zone and recommend
        for _, row in filtered_zone.iterrows():
            city = row["CITY"]
            zone = row["ZONE"]
            total_orders = row["TOTAL_ORDERS"]
            de_count = row["DE_COUNT"] if "DE_COUNT" in row else row.get("DES", 0)
            median_orders = row["MEDIAN_ORDERS"] if "MEDIAN_ORDERS" in row else (row["TOTAL_ORDERS"] // max(row["DE_COUNT"],1))
            pct_10plus = (row["% DES >10 ORDERS"] if "% DES >10 ORDERS" in row else None)
            default_1st = 1
            default_5th = max(2, int(np.percentile([median_orders], 50)))  # fallback
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
    else:
        # Fallback: global milestone (old logic)
        st.warning("No zone summary uploaded, so single milestone for all DEs.")
        m1 = st.number_input("Milestone 1st Order Target", min_value=1, max_value=100, value=1, key="m1_global")
        p1 = st.number_input("1st Order Payout ₹", min_value=1, max_value=1000, value=25, key="p1_global")
        m2 = st.number_input("2nd Milestone Target", min_value=1, max_value=100, value=5, key="m2_global")
        p2 = st.number_input("2nd Payout ₹", min_value=1, max_value=1000, value=50, key="p2_global")
        m3 = st.number_input("3rd Milestone Target", min_value=1, max_value=100, value=10, key="m3_global")
        p3 = st.number_input("3rd Payout ₹", min_value=1, max_value=1000, value=100, key="p3_global")
        milestone_setup.append({
            "city": "All", "zone": "All",
            "milestones": [
                {"order": m1, "payout": p1},
                {"order": m2, "payout": p2},
                {"order": m3, "payout": p3},
            ]
        })

    # 4. Calculate Surge Eligibility/Payout for each DE, per milestone (zone logic)
    st.header("💰 4️⃣ Final Surge Payout Table")
    payout_records = []
    for _, de in de_final.iterrows():
        city = de["CITY"]
        zone = de[zone_col]
        orders = de["TOTAL ORDERS"]
        matched = None
        # find matching milestone config for this DE
        for setup in milestone_setup:
            if setup["city"] == city and setup["zone"] == zone:
                matched = setup["milestones"]
                break
        if not matched:
            matched = milestone_setup[0]["milestones"]  # fallback to first

        # For each milestone, mark eligibility and payout
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
    st.info("👆 Upload both files to unlock the full power of Smart Surge Planning.")

