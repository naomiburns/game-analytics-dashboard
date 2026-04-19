import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="Team Roster Analytics", layout="wide")

# ── Brand colors ──────────────────────────────────────────────────────────────
CORAL    = "#FF6F59"
DUSK     = "#696D7D"
POLLEN   = "#FFD166"
EMERALD  = "#41EAD4"
MINT_BG  = "#E8FAF5"
PALETTE  = [CORAL, DUSK, POLLEN, EMERALD, "#A78BFA", "#F97316", "#38BDF8", "#FB7185"]

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;600;700&family=DM+Mono:wght@400;500&display=swap');
html, body, [class*="css"] {{ font-family: 'DM Sans', sans-serif; }}
.stApp {{ background-color: #ffffff; }}
section[data-testid="stSidebar"] {{ background-color: #f7fffe; border-right: 1px solid #d0f0e8; }}
[data-testid="metric-container"] {{
    background: #f7fffe;
    border: 1.5px solid #06D6A0;
    border-radius: 12px;
    padding: 18px 22px;
}}
[data-testid="stMetricValue"] {{
    font-family: 'DM Mono', monospace !important;
    color: #26547C !important;
    font-size: 2rem !important;
}}
[data-testid="stMetricLabel"] {{
    color: #26547C !important;
    font-weight: 600;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}}
[data-testid="stMetricDelta"] {{
    font-family: 'DM Mono', monospace !important;
    font-size: 0.8rem !important;
}}
h1 {{ color: #26547C !important; font-weight: 700 !important; letter-spacing: -0.02em; }}
h2, h3 {{ color: #26547C !important; font-weight: 600 !important; }}
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
                "event_time": datetime.fromtimestamp(r["client_ts"], tz=timezone.utc).replace(tzinfo=None),
                "StationID":  cf.get("StationID", "Unknown"),
                "DeviceID":   cf.get("DeviceID", "Unknown"),
                "Time":       cf.get("Time"),
                "Profile":    cf.get("Profile"),
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
st.caption("Athlete performance tracking · Lower time = faster = better")
st.divider()

if df_raw.empty:
    st.warning("No Results events found in live_events.json.")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
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

# ── Compute roster rows ───────────────────────────────────────────────────────
rows = []
for athlete in sorted(df["Athlete"].unique()):
    adf = df[df["Athlete"] == athlete].sort_values("event_time")
    times = adf["Time"].values
    sessions = len(times)
    avg_t = float(times.mean())
    best_t = float(times.min())
    worst_t = float(times.max())
    station = adf["StationID"].iloc[0]
    if sessions >= 2:
        mid = sessions // 2
        trend = round(float(times[mid:].mean()) - float(times[:mid].mean()), 3)
        trend_str = f"{trend:+.3f}"
    else:
        trend = None
        trend_str = "—"
    rows.append({
        "Athlete": athlete, "StationID": station,
        "Sessions": sessions,
        "Avg Time": f"{avg_t:.2f}", "Best Time": f"{best_t:.2f}", "Worst Time": f"{worst_t:.2f}",
        "Trend": trend_str,
        "_avg": avg_t, "_best": best_t, "_trend": trend,
    })
roster_df = pd.DataFrame(rows)

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_sessions   = len(df)
athletes_active  = df["Athlete"].nunique()
fastest_row      = roster_df.loc[roster_df["_best"].idxmin()]
fastest_time     = f"{fastest_row['_best']:.2f}s"
fastest_name     = fastest_row["Athlete"]

# Most improved = largest negative trend (most time drop)
improved = roster_df.dropna(subset=["_trend"])
if not improved.empty:
    best_improved = improved.loc[improved["_trend"].idxmin()]
    most_improved = f"{best_improved['Athlete']} ({best_improved['_trend']:+.2f}s)"
else:
    most_improved = "Not enough data"

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Sessions", total_sessions)
k2.metric("Athletes Active", athletes_active)
k3.metric("Fastest Time", fastest_time, delta=fastest_name, delta_color="off")
k4.metric("Most Improved", most_improved if "(" not in most_improved else most_improved.split(" (")[0],
          delta=most_improved.split("(")[-1].replace(")", "") if "(" in most_improved else None,
          delta_color="inverse")

st.divider()

# ── My Roster table ───────────────────────────────────────────────────────────
st.subheader("My Roster")

display_cols = ["Athlete", "StationID", "Sessions", "Avg Time", "Best Time", "Worst Time", "Trend"]

def style_trend(val):
    if val == "—":
        return "color: #aaa"
    try:
        num = float(val)
        if num < 0:
            return f"color: {EMERALD}; font-weight: 600"
        elif num > 0:
            return f"color: {CORAL}; font-weight: 600"
    except:
        pass
    return ""

styled = roster_df[display_cols].style.map(style_trend, subset=["Trend"])
st.dataframe(styled, use_container_width=True, hide_index=True)
st.caption("Negative trend = getting faster (good)  ·  Positive trend = getting slower")
st.divider()

# ── Chart 1: Avg Time per Athlete (horizontal bar) ───────────────────────────
st.subheader("Average Time by Athlete")
bar_df = roster_df.sort_values("_avg", ascending=True)
fig1 = go.Figure(go.Bar(
    x=bar_df["_avg"],
    y=bar_df["Athlete"],
    orientation="h",
    marker=dict(
        color=bar_df["_avg"],
        colorscale=[[0, EMERALD], [0.5, POLLEN], [1, CORAL]],
        showscale=False,
    ),
    text=[f"{v:.2f}s" for v in bar_df["_avg"]],
    textposition="outside",
))
fig1.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color=DUSK),
    xaxis=dict(title="Time (seconds)", gridcolor="#e8eaf0", zeroline=False),
    yaxis=dict(title=""),
    margin=dict(l=10, r=60, t=10, b=10),
    height=300,
)
st.plotly_chart(fig1, use_container_width=True)
st.divider()

# ── Chart 2: Session dot plot (time per session per athlete) ──────────────────
st.subheader("Session Times — Individual Results")
athlete_order = roster_df.sort_values("_avg")["Athlete"].tolist()
color_map = {a: PALETTE[i % len(PALETTE)] for i, a in enumerate(sorted(df["Athlete"].unique()))}

fig2 = go.Figure()
for athlete in athlete_order:
    adf = df[df["Athlete"] == athlete].sort_values("event_time").reset_index(drop=True)
    adf["session_num"] = range(1, len(adf) + 1)
    fig2.add_trace(go.Scatter(
        x=adf["session_num"],
        y=adf["Time"],
        mode="markers",
        name=athlete,
        marker=dict(size=14, color=color_map[athlete], line=dict(width=1.5, color="white")),
        hovertemplate=f"<b>{athlete}</b><br>Session %{{x}}<br>Time: %{{y:.2f}}s<extra></extra>",
    ))
fig2.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color=DUSK),
    xaxis=dict(title="Session Number", gridcolor="#e8eaf0", tickmode="linear", dtick=1),
    yaxis=dict(title="Time (seconds)", gridcolor="#e8eaf0"),
    legend=dict(title="Athlete", bgcolor="rgba(255,255,255,0.8)", bordercolor="#e8eaf0", borderwidth=1),
    margin=dict(l=10, r=10, t=10, b=10),
    height=350,
    hovermode="closest",
)
st.plotly_chart(fig2, use_container_width=True)
st.divider()

# ── Chart 3: Time trend line per athlete ──────────────────────────────────────
st.subheader("Performance Trend Over Sessions")
fig3 = go.Figure()
for athlete in athlete_order:
    adf = df[df["Athlete"] == athlete].sort_values("event_time").reset_index(drop=True)
    adf["session_num"] = range(1, len(adf) + 1)
    fig3.add_trace(go.Scatter(
        x=adf["session_num"],
        y=adf["Time"],
        mode="lines+markers",
        name=athlete,
        line=dict(width=2.5, color=color_map[athlete]),
        marker=dict(size=8, color=color_map[athlete], line=dict(width=1.5, color="white")),
        hovertemplate=f"<b>{athlete}</b><br>Session %{{x}}<br>Time: %{{y:.2f}}s<extra></extra>",
    ))
fig3.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color=DUSK),
    xaxis=dict(title="Session Number", gridcolor="#e8eaf0", tickmode="linear", dtick=1),
    yaxis=dict(title="Time (seconds)", gridcolor="#e8eaf0"),
    legend=dict(title="Athlete", bgcolor="rgba(255,255,255,0.8)", bordercolor="#e8eaf0", borderwidth=1),
    margin=dict(l=10, r=10, t=10, b=10),
    height=350,
    hovermode="x unified",
)
st.caption("Lines will appear once athletes have 2+ sessions recorded")
st.plotly_chart(fig3, use_container_width=True)
st.divider()

# ── Session history ───────────────────────────────────────────────────────────
st.subheader("Session History by Athlete")
cols = st.columns(len(athlete_order))
for col, athlete in zip(cols, athlete_order):
    adf = df[df["Athlete"] == athlete].sort_values("event_time")
    with col:
        st.markdown(f"**{athlete}**")
        st.caption(adf["StationID"].iloc[0])
        for _, row in adf.iterrows():
            st.markdown(f"`{row['event_time'].strftime('%m/%d %H:%M')}` — **{row['Time']:.2f}s**")

st.divider()

with st.expander("Raw Results Data"):
    st.dataframe(
        df[["event_time", "Athlete", "StationID", "DeviceID", "Time", "Profile"]]
        .sort_values("event_time", ascending=False).reset_index(drop=True),
        use_container_width=True
    )