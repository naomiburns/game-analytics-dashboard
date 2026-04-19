import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="Team Roster Analytics", layout="wide")

CORAL   = "#FF6F59"
SLATE   = "#696D7D"
POLLEN  = "#FFD166"
TEAL    = "#41EAD4"
PALETTE = [CORAL, TEAL, POLLEN, SLATE, "#A78BFA", "#F97316", "#38BDF8", "#FB7185"]

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;600;700&family=DM+Mono:wght@400;500&display=swap');
html, body, [class*="css"] {{ font-family: 'DM Sans', sans-serif; color: #1a1a2e; }}
.stApp {{ background-color: #f0f2f6; }}
.block-container {{ padding-top: 2rem !important; padding-left: 3rem !important; padding-right: 3rem !important; }}
section[data-testid="stSidebar"] {{ background-color: #ffffff; border-right: 1px solid #e4e5ea; }}
section[data-testid="stSidebar"] * {{ color: #1a1a2e !important; }}
section[data-testid="stSidebar"] label {{
    font-size: 0.7rem; text-transform: uppercase;
    letter-spacing: 0.08em; font-weight: 600; color: #1a1a2e !important;
}}
[data-testid="metric-container"] {{
    background: #ffffff; border: none; border-radius: 14px;
    padding: 20px 24px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04);
}}
[data-testid="stMetricValue"] {{
    font-family: 'DM Mono', monospace !important;
    color: #1a1a2e !important; font-size: 2.1rem !important; font-weight: 500 !important;
}}
[data-testid="stMetricLabel"] {{
    color: #1a1a2e !important; font-weight: 600 !important;
    font-size: 0.72rem !important; text-transform: uppercase !important; letter-spacing: 0.08em !important;
}}
[data-testid="stMetricDelta"] > div {{
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important; font-weight: 600 !important;
}}
span[data-baseweb="tag"] {{
    background-color: {TEAL} !important; border-radius: 20px !important;
    color: #1a1a2e !important; font-size: 0.78rem !important; font-weight: 600 !important;
}}
/* Pill radio buttons */
div[data-testid="stRadio"] > div {{ display: flex; flex-direction: column; gap: 6px; }}
div[data-testid="stRadio"] label {{
    background: rgba(65,234,212,0.08) !important;
    border: 1.5px solid rgba(65,234,212,0.35) !important;
    border-radius: 20px !important;
    padding: 7px 18px !important;
    font-size: 0.85rem !important; font-weight: 600 !important;
    color: #1a1a2e !important; cursor: pointer;
    text-transform: none !important; letter-spacing: 0 !important;
}}
div[data-testid="stRadio"] label:has(input:checked) {{
    background: rgba(65,234,212,0.25) !important;
    border-color: {TEAL} !important;
}}
div[data-testid="stRadio"] input {{ accent-color: {TEAL} !important; }}
h1, h2, h3 {{ color: #1a1a2e !important; font-weight: 700 !important; }}
/* Dataframe rounded corners */
[data-testid="stDataFrame"] {{ border-radius: 12px !important; overflow: hidden !important; }}
[data-testid="stDataFrame"] > div {{ border-radius: 12px !important; }}
/* Chart containers */
.stPlotlyChart {{
    background: #ffffff !important;
    border-radius: 16px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04) !important;
}}
/* White containers for table and session history */
[data-testid="stVerticalBlockBorderWrapper"] {{
    background: #ffffff !important;
    border-radius: 16px !important;
    border: none !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04) !important;
}}
[data-testid="stVerticalBlockBorderWrapper"] > div,
[data-testid="stVerticalBlockBorderWrapper"] > div > div {{
    background: #ffffff !important;
    border-radius: 16px !important;
}}
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

CARD = "background:#ffffff;border-radius:16px;padding:28px 32px 20px 32px;box-shadow:0 1px 4px rgba(0,0,0,0.08),0 4px 16px rgba(0,0,0,0.04);margin-bottom:20px;"

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="{CARD}">
    <div style="font-size:2.3rem;font-weight:700;color:#1a1a2e;letter-spacing:-0.03em;">Team Roster Dashboard</div>
    <div style="font-size:0.95rem;color:#1a1a2e;margin-top:8px;opacity:0.5;">Athlete performance tracking &nbsp;·&nbsp; Lower time = faster = better</div>
</div>
""", unsafe_allow_html=True)

if df_raw.empty:
    st.warning("No Results events found in live_events.json.")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    all_devices = sorted(df_raw["DeviceID"].unique())
    selected_devices = st.multiselect("Team (DeviceID)", all_devices, default=all_devices)
    st.markdown("**Date Range**")
    period_options = ["7 Days", "14 Days", "30 Days", "3 Months", "6 Months"]
    selected_period = st.radio("Select period", period_options, index=0, label_visibility="collapsed")
    period_map = {
        "7 Days":   (timedelta(days=6),   "Last 7 Days"),
        "14 Days":  (timedelta(days=13),  "Last 14 Days"),
        "30 Days":  (timedelta(days=29),  "Last 30 Days"),
        "3 Months": (timedelta(days=89),  "Last 3 Months"),
        "6 Months": (timedelta(days=179), "Last 6 Months"),
    }
    delta, period_label = period_map[selected_period]
    max_date = df_raw["event_time"].max().date()
    start_date = max_date - delta
    end_date = max_date

# ── Filter ────────────────────────────────────────────────────────────────────
df = df_raw[
    (df_raw["DeviceID"].isin(selected_devices)) &
    (df_raw["event_time"].dt.date >= start_date) &
    (df_raw["event_time"].dt.date <= end_date)
].copy()

if df.empty:
    st.info("No data for the selected filters.")
    st.stop()

# ── Build roster ──────────────────────────────────────────────────────────────
rows = []
for athlete in sorted(df["Athlete"].unique()):
    adf = df[df["Athlete"] == athlete].sort_values("event_time")
    times = adf["Time"].values
    sessions = len(times)
    avg_t, best_t, worst_t = float(times.mean()), float(times.min()), float(times.max())
    station = adf["StationID"].iloc[0]
    if sessions >= 2:
        mid = sessions // 2
        trend = round(float(times[mid:].mean()) - float(times[:mid].mean()), 2)
    else:
        trend = 0.0
    trend_display = "↑ 0.00" if sessions < 2 else (f"↓ {abs(trend):.2f}" if trend < 0 else f"↑ {abs(trend):.2f}")
    rows.append({
        "Athlete": athlete, "StationID": station, "Sessions": sessions,
        "Avg Time": f"{avg_t:.2f}", "Best Time": f"{best_t:.2f}", "Worst Time": f"{worst_t:.2f}",
        "Trend": trend_display,
        "_avg": avg_t, "_best": best_t, "_trend": trend, "_sessions": sessions,
    })
roster_df = pd.DataFrame(rows)

# ── KPIs ──────────────────────────────────────────────────────────────────────
fastest_row = roster_df.loc[roster_df["_best"].idxmin()]
has_trend   = roster_df[roster_df["_sessions"] >= 2]
if not has_trend.empty:
    best_imp  = has_trend.loc[has_trend["_trend"].idxmin()]
    imp_name  = best_imp["Athlete"]
    imp_delta = f"{best_imp['_trend']:+.2f}s"
else:
    imp_name, imp_delta = "No Data", None

st.markdown(f'<div style="font-size:1.1rem;font-weight:700;color:#1a1a2e;margin-bottom:12px;">{period_label}</div>', unsafe_allow_html=True)
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Sessions",  len(df))
k2.metric("Athletes Active", df["Athlete"].nunique())
k3.metric("Fastest Time",    f"{fastest_row['_best']:.2f}s", delta=fastest_row["Athlete"], delta_color="off")
k4.metric("Most Improved",   imp_name, delta=imp_delta, delta_color="inverse")

st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────────────────
athlete_order = roster_df.sort_values("_avg")["Athlete"].tolist()
color_map = {a: PALETTE[i % len(PALETTE)] for i, a in enumerate(sorted(df["Athlete"].unique()))}

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    bar_df = roster_df.sort_values("_avg", ascending=True)
    fig1 = go.Figure(go.Bar(
        x=bar_df["_avg"], y=bar_df["Athlete"], orientation="h",
        marker=dict(color=bar_df["_avg"], colorscale=[[0,TEAL],[0.5,POLLEN],[1,CORAL]], showscale=False),
        text=[f"{v:.2f}s" for v in bar_df["_avg"]], textposition="outside",
    ))
    fig1.update_layout(
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font=dict(family="DM Sans, sans-serif", color="#1a1a2e"),
        title=dict(text="Average Time by Athlete", font=dict(size=15, color="#1a1a2e"), x=0, xref="paper"),
        xaxis=dict(title="Time (seconds)", gridcolor="#f0f0f0", zeroline=False),
        yaxis=dict(title=""),
        margin=dict(l=10, r=70, t=44, b=10), height=400,
    )
    st.plotly_chart(fig1, use_container_width=True, config={"scrollZoom": False, "displayModeBar": False})

with chart_col2:
    fig2 = go.Figure()
    for athlete in athlete_order:
        adf = df[df["Athlete"] == athlete].sort_values("event_time").reset_index(drop=True)
        adf["session_num"] = range(1, len(adf) + 1)
        fig2.add_trace(go.Scatter(
            x=adf["session_num"], y=adf["Time"], mode="lines+markers", name=athlete,
            line=dict(width=2.5, color=color_map[athlete]),
            marker=dict(size=9, color=color_map[athlete], line=dict(width=1.5, color="white")),
            hovertemplate=f"<b>{athlete}</b><br>Session %{{x}}<br>Time: %{{y:.2f}}s<extra></extra>",
        ))
    fig2.update_layout(
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font=dict(family="DM Sans, sans-serif", color="#1a1a2e"),
        title=dict(text="Performance Trend Over Sessions", font=dict(size=15, color="#1a1a2e"), x=0, xref="paper"),
        xaxis=dict(title="Session Number", gridcolor="#f0f0f0", tickmode="linear", dtick=1),
        yaxis=dict(title="Time (seconds)", gridcolor="#f0f0f0"),
        legend=dict(bgcolor="#ffffff", bordercolor="#eeeeee", borderwidth=1),
        margin=dict(l=10, r=10, t=44, b=10), height=400,
        hovermode="x unified",
    )
    st.plotly_chart(fig2, use_container_width=True, config={"scrollZoom": False, "displayModeBar": False})

st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

# ── My Roster ─────────────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown('<p style="font-size:1.2rem;font-weight:700;color:#1a1a2e;margin-bottom:4px;">My Roster</p>', unsafe_allow_html=True)
    def style_trend(val):
        if not val: return ""
        if val.startswith("↓"): return f"color:{TEAL};font-weight:600"
        if val.startswith("↑") and "0.00" not in val: return f"color:{CORAL};font-weight:600"
        return "color:#cccccc;font-weight:400"
    display_cols = ["Athlete","StationID","Sessions","Avg Time","Best Time","Worst Time","Trend"]
    st.dataframe(roster_df[display_cols].style.map(style_trend, subset=["Trend"]), use_container_width=True, hide_index=True)
    st.markdown('<p style="font-size:0.75rem;color:#888;">↓ Trend = getting faster (good) &nbsp;·&nbsp; ↑ Trend = getting slower</p>', unsafe_allow_html=True)

st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

# ── Session History ───────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown('<p style="font-size:1.2rem;font-weight:700;color:#1a1a2e;margin-bottom:4px;">Session History by Athlete</p>', unsafe_allow_html=True)
    cols = st.columns(len(athlete_order))
    for col, athlete in zip(cols, athlete_order):
        adf = df[df["Athlete"] == athlete].sort_values("event_time")
        with col:
            st.markdown(f"**{athlete}**")
            st.caption(adf["StationID"].iloc[0])
            for _, row in adf.iterrows():
                st.markdown(f"`{row['event_time'].strftime('%m/%d %H:%M')}` — **{row['Time']:.2f}s**")

st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

with st.expander("Raw Results Data"):
    st.dataframe(
        df[["event_time","Athlete","StationID","DeviceID","Time","Profile"]]
        .sort_values("event_time", ascending=False).reset_index(drop=True),
        use_container_width=True
    )