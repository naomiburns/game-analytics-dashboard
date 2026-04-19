import streamlit as st
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="Team Roster Analytics", page_icon="🏃", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;600&family=DM+Mono&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
[data-testid="metric-container"] {
    background: #f8f9fc;
    border: 1px solid #e8eaf0;
    border-radius: 10px;
    padding: 16px 20px;
}
[data-testid="stMetricValue"] { font-family: 'DM Mono', monospace; color: #1a1a2e !important; }
</style>
""", unsafe_allow_html=True)

# ── Dummy name mapping ────────────────────────────────────────────────────────
DUMMY_NAMES = ["Jane", "Jill", "Sophie", "Ellie", "Alex", "Maya", "Zoe", "Ava"]

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data():
    path = Path(__file__).parent / "live_events.json"
    if not path.exists():
        return pd.DataFrame()
    data = json.load(open(path))

    results = []
    for r in data:
        if r.get("event_id") == "Results" and "custom_fields" in r:
            cf = r["custom_fields"]
            results.append({
                "ts": r["client_ts"],
                "event_time": datetime.fromtimestamp(r["client_ts"], tz=timezone.utc).replace(tzinfo=None),
                "StationID": cf.get("StationID", "Unknown"),
                "DeviceID": cf.get("DeviceID", "Unknown"),
                "Time": cf.get("Time"),
                "Profile": cf.get("Profile"),
            })

    df = pd.DataFrame(results)
    if df.empty:
        return df

    station_ids = sorted(df["StationID"].unique())
    name_map = {sid: DUMMY_NAMES[i % len(DUMMY_NAMES)] for i, sid in enumerate(station_ids)}
    df["Athlete"] = df["StationID"].map(name_map)
    return df

df_raw = load_data()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🏃 Team Roster Dashboard")
st.caption("Tracking athlete performance by StationID · Lower time = faster = better")
st.divider()

if df_raw.empty:
    st.warning("No Results events found in live_events.json.")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Filters")
    all_devices = sorted(df_raw["DeviceID"].unique())
    selected_devices = st.multiselect("Team (DeviceID)", all_devices, default=all_devices)
    max_date = df_raw["event_time"].max().date()
    min_date = df_raw["event_time"].min().date()
    default_start = max_date - timedelta(days=6)
    start_date, end_date = st.date_input(
        "Date range",
        value=[max(min_date, default_start), max_date],
        min_value=min_date,
        max_value=max_date
    )

# ── Filter ────────────────────────────────────────────────────────────────────
df = df_raw[
    (df_raw["DeviceID"].isin(selected_devices)) &
    (df_raw["event_time"].dt.date >= start_date) &
    (df_raw["event_time"].dt.date <= end_date)
].copy()

if df.empty:
    st.info("No data for the selected filters.")
    st.stop()

# ── Top KPIs ──────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Sessions", len(df))
k2.metric("Athletes Tracked", df["StationID"].nunique())
k3.metric("Teams", df["DeviceID"].nunique())
k4.metric("Avg Time (s)", f"{df['Time'].mean():.2f}")
st.divider()

# ── Roster table ──────────────────────────────────────────────────────────────
st.subheader("📋 Athlete Roster")

roster = (
    df.sort_values("event_time")
    .groupby(["Athlete", "StationID", "DeviceID"])
    .agg(
        Sessions=("Time", "count"),
        Avg_Time=("Time", "mean"),
        Best_Time=("Time", "min"),
        Worst_Time=("Time", "max"),
    )
    .reset_index()
)

def rate_of_change(group):
    times = group.sort_values("event_time")["Time"].values
    if len(times) < 2:
        return None
    mid = len(times) // 2
    first_avg = times[:mid].mean() if mid > 0 else times[0]
    second_avg = times[mid:].mean()
    return round(second_avg - first_avg, 3)

roc = df.groupby("Athlete").apply(rate_of_change, include_groups=False).reset_index()
roc.columns = ["Athlete", "Trend (s)"]
roster = roster.merge(roc, on="Athlete", how="left")
roster["Avg_Time"] = roster["Avg_Time"].round(2)
roster["Best_Time"] = roster["Best_Time"].round(2)
roster["Worst_Time"] = roster["Worst_Time"].round(2)

roster_display = roster.rename(columns={
    "Avg_Time": "Avg Time (s)",
    "Best_Time": "Best Time (s)",
    "Worst_Time": "Worst Time (s)",
})

def style_trend(val):
    if val is None:
        return ""
    if val < 0:
        return "color: #2ea043; font-weight: 600"
    elif val > 0:
        return "color: #da3633; font-weight: 600"
    return ""

styled = roster_display.style.applymap(style_trend, subset=["Trend (s)"])
st.dataframe(styled, use_container_width=True, hide_index=True)
st.caption("💚 Negative trend = getting faster (good!)  ·  ❤️ Positive trend = getting slower")
st.divider()

# ── Per-athlete session history ───────────────────────────────────────────────
st.subheader("📈 Session History by Athlete")
athletes = sorted(df["Athlete"].unique())
cols = st.columns(len(athletes))
for col, athlete in zip(cols, athletes):
    athlete_df = df[df["Athlete"] == athlete].sort_values("event_time")
    with col:
        st.markdown(f"**{athlete}**")
        st.caption(athlete_df["StationID"].iloc[0])
        for _, row in athlete_df.iterrows():
            st.markdown(f"`{row['event_time'].strftime('%m/%d %H:%M')}` — **{row['Time']:.2f}s**")

st.divider()

# ── Raw data ──────────────────────────────────────────────────────────────────
with st.expander("🔍 Raw Results Data"):
    st.dataframe(
        df[["event_time", "Athlete", "StationID", "DeviceID", "Time", "Profile"]]
        .sort_values("event_time", ascending=False)
        .reset_index(drop=True),
        use_container_width=True
    )