import streamlit as st
import pandas as pd

st.set_page_config(page_title="Surge Planner by Zone", layout="wide")
st.title("🚀 Surge Planner: Zone-wise Surge Slab Design")

# --- Upload both files ---
st.markdown("### 1️⃣ Upload Files")
planning_file = st.file_uploader("Upload Planning File (zone-week summary, CSV)", type=["csv"])
de_file = st.file_uploader("Upload DE Data File (DE-wise, CSV)", type=["csv"])

if not (planning_file and de_file):
    st.info("Upload both Planning and DE Data files to begin.")
    st.stop()

planning_df = pd.read_csv(planning_file)
planning_df.columns = planning_df.columns.str.upper().str.strip()
de_df = pd.read_csv(de_file)
de_df.columns = de_df.columns.str.upper().str.strip()

# --- Select reference week ---
week_options = sorted(planning_df["WEEK"].unique())
selected_week = st.selectbox("Select the week to plan surge for:", week_options, index=len(week_options)-1)

# Filter planning & DE file for selected week only
plan_week_df = planning_df[planning_df["WEEK"] == selected_week].copy()
de_week_df = de_df[de_df["WEEK"] == selected_week].copy()

st.markdown(f"### 2️⃣ Demand stats for Week {selected_week}")

if "ZONE" not in plan_week_df.columns or "ZONE" not in de_week_df.columns:
    st.error("Both files must have 'ZONE' and 'CITY' columns.")
    st.stop()

# List all zones for that week
zones = plan_week_df["ZONE"].unique()
zone_slab_dict = {}

for zone in zones:
    zone_stats = plan_week_df[plan_week_df["ZONE"] == zone]
    if zone_stats.empty:
        continue
    city = zone_stats["CITY"].iloc[0]
    de_list = de_week_df[(de_week_df["ZONE"] == zone) & (de_week_df["CITY"] == city)]
    with st.expander(f"Zone: {zone} ({city}) - Click to expand"):
        st.write("**Zone Stats:**")
        st.dataframe(zone_stats, use_container_width=True)
        st.write("**DEs in this Zone/Week:**")
        st.dataframe(de_list[["DE ID", "DE NAME", "TOTAL ORDERS"]], use_container_width=True)
        # Input for surge slabs per zone
        slabs = st.text_input(
            f"Enter slabs for {zone} as comma-separated order:payout (e.g. 1:25,5:50,10:100)",
            value="1:25,5:50,10:100",
            key=f"slab_{zone}"
        )
        # Parse into list of (order, payout)
        try:
            slab_pairs = [tuple(map(int, x.split(":"))) for x in slabs.split(",") if ":" in x]
            zone_slab_dict[zone] = sorted(slab_pairs)
        except Exception:
            st.warning(f"Invalid slab format for {zone}. Skipping.")

st.markdown("---")

# --- Compute payouts for each DE in each zone ---
st.markdown("### 3️⃣ Payout Table Preview")

payout_rows = []
for zone in zones:
    city = plan_week_df[plan_week_df["ZONE"] == zone]["CITY"].iloc[0]
    de_list = de_week_df[(de_week_df["ZONE"] == zone) & (de_week_df["CITY"] == city)]
    slabs = zone_slab_dict.get(zone, [])
    for _, row in de_list.iterrows():
        orders = row["TOTAL ORDERS"]
        payout = 0
        achieved = []
        for o, amt in slabs:
            if orders >= o:
                payout = amt
                achieved.append(str(o))
        payout_rows.append({
            "DE ID": row["DE ID"],
            "DE NAME": row["DE NAME"],
            "CITY": city,
            "ZONE": zone,
            "TOTAL ORDERS": orders,
            "Slab_Achieved": ",".join(achieved) if achieved else "None",
            "Payout": payout
        })

payout_df = pd.DataFrame(payout_rows)
st.dataframe(payout_df, use_container_width=True)
st.download_button(
    "📥 Download Payout Table (CSV)",
    payout_df.to_csv(index=False),
    file_name=f"surge_payout_week_{selected_week}.csv",
    mime="text/csv"
)
