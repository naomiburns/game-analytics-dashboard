import streamlit as st
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="Team Roster Analytics", layout="wide")

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

DUMMY_NAMES = ["Jane", "Jill", "Sophie", "Ellie", "Alex", "Maya", "Zoe", "Ava"]

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

st.title("Team Roster Dashboard")
st.caption("Tracking athlete performance by StationID · Lower time = faster = better")
st.divider()

if df_raw.empty:
    st.warning("No Results events found in live_events.json.")
    st.stop()

with st.sidebar:
    st.header("Filters")
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

df = df_raw[
    (df_raw["DeviceID"].isin(selected_devices)) &
    (df_raw["event_time"].dt.date >= start_date) &
    (df_raw["event_time"].dt.date <= end_date)
].copy()

if df.empty:
    st.info("No data for the selected filters.")
    st.stop()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Sessions", len(df))
k2.metric("Athletes Tracked", df["StationID"].nunique())
k3.metric("Teams", df["DeviceID"].nunique())
k4.metric("Avg Time", f"{df['Time'].mean():.2f}")
st.divider()

st.subheader("My Roster")

rows = []
for athlete in sorted(df["Athlete"].unique()):
    adf = df[df["Athlete"] == athlete].sort_values("event_time")
    times = adf["Time"].values
    sessions = len(times)
    avg_t = f"{float(times.mean()):.2f}"
    best_t = f"{float(times.min()):.2f}"
    worst_t = f"{float(times.max()):.2f}"
    station = adf["StationID"].iloc[0]

    if sessions >= 2:
        mid = sessions // 2
        trend = round(float(times[mid:].mean()) - float(times[:mid].mean()), 3)
        trend_str = f"{trend:+.3f}"
    else:
        trend = None
        trend_str = "—"

    rows.append({
        "Athlete": athlete,
        "StationID": station,
        "Sessions": sessions,
        "Avg Time": avg_t,
        "Best Time": best_t,
        "Worst Time": worst_t,
        "Trend": trend_str,
    })

roster_df = pd.DataFrame(rows)

def style_trend(val):
    if val == "—":
        return "color: #888"
    try:
        num = float(val)
        if num < 0:
            return "color: #2ea043; font-weight: 600"
        elif num > 0:
            return "color: #da3633; font-weight: 600"
    except:
        pass
    return ""

styled = roster_df.style.map(style_trend, subset=["Trend"])
st.dataframe(styled, use_container_width=True, hide_index=True)
st.caption("Negative trend = getting faster (good)  ·  Positive trend = getting slower")
st.divider()

st.subheader("Session History by Athlete")
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

with st.expander("Raw Results Data"):
    st.dataframe(
        df[["event_time", "Athlete", "StationID", "DeviceID", "Time", "Profile"]]
        .sort_values("event_time", ascending=False)
        .reset_index(drop=True),
        use_container_width=True
    )