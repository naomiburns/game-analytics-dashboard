import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="Ver Vision Training Dashboard", layout="wide")

CORAL   = "#FF6F59"
SLATE   = "#696D7D"
POLLEN  = "#FFD166"
TEAL    = "#41EAD4"
PALETTE = [CORAL, TEAL, POLLEN, SLATE, "#A78BFA", "#F97316", "#38BDF8", "#FB7185",
           "#34D399", "#F472B6", "#60A5FA", "#FBBF24"]

# 12 dummy names for profiles 1-12
PROFILE_NAMES = {
    1:  "Jane",
    2:  "Jill",
    3:  "Sophie",
    4:  "Ellie",
    5:  "Alex",
    6:  "Maya",
    7:  "Zoe",
    8:  "Ava",
    9:  "Mia",
    10: "Lily",
    11: "Grace",
    12: "Chloe",
}
TOTAL_PROFILES = 12

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;600;700&family=DM+Mono:wght@400;500&display=swap');
html, body, [class*="css"] {{ font-family: 'DM Sans', sans-serif; color: #1a1a2e; }}
.stApp {{ background-color: #f0f2f6; }}
.block-container {{ padding-top: 60px !important; padding-left: 3rem !important; padding-right: 3rem !important; }}
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
div[data-testid="stRadio"] > div {{ display: flex; flex-direction: column; gap: 6px; }}
div[data-testid="stRadio"] label {{
    background: rgba(65,234,212,0.08) !important;
    border: 1.5px solid rgba(65,234,212,0.35) !important;
    border-radius: 20px !important; padding: 7px 18px !important;
    font-size: 0.85rem !important; font-weight: 600 !important;
    color: #1a1a2e !important; cursor: pointer;
    text-transform: none !important; letter-spacing: 0 !important;
}}
div[data-testid="stRadio"] label:has(input:checked) {{
    background: rgba(65,234,212,0.25) !important; border-color: {TEAL} !important;
}}
div[data-testid="stRadio"] input {{ accent-color: {TEAL} !important; }}
h1, h2, h3 {{ color: #1a1a2e !important; font-weight: 700 !important; }}
[data-testid="stDataFrame"] {{ border-radius: 12px !important; overflow: hidden !important; }}
[data-testid="stDataFrame"] > div {{ border-radius: 12px !important; }}
.stPlotlyChart {{
    border-radius: 16px !important;
    border: 1.5px solid #1a1a2e !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04) !important;
    overflow: hidden !important;
}}
.stPlotlyChart > div {{ overflow: hidden !important; border-radius: 16px !important; }}
.stPlotlyChart iframe {{ display: block !important; border-radius: 16px !important; }}
[data-testid="stVerticalBlockBorderWrapper"] {{
    background: #ffffff !important; border-radius: 16px !important;
    border: none !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04) !important;
}}
[data-testid="stVerticalBlockBorderWrapper"] > div,
[data-testid="stVerticalBlockBorderWrapper"] > div > div {{
    background: #ffffff !important; border-radius: 16px !important;
}}
</style>
""", unsafe_allow_html=True)

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
                "ProfileNum": int(cf.get("Profile", 0)),
            })
    df = pd.DataFrame(results)
    if df.empty:
        return df
    df["Athlete"] = df["ProfileNum"].map(lambda x: PROFILE_NAMES.get(x, f"Athlete {x}"))
    return df

df_raw = load_data()

CARD = "background:#ffffff;border-radius:16px;padding:28px 32px 20px 32px;box-shadow:0 1px 4px rgba(0,0,0,0.08),0 4px 16px rgba(0,0,0,0.04);margin-bottom:20px;"

st.markdown(f"""
<div style="{CARD}">
    <div style="font-size:2.3rem;font-weight:700;color:#1a1a2e;letter-spacing:-0.03em;">Ver Vision Training Dashboard</div>
    <div style="font-size:0.95rem;color:#1a1a2e;margin-top:8px;opacity:0.5;">Your athletes are logging vision training reps through the Ver app. Monitor who's showing up, how often, and whether their reaction times are improving.</div>
</div>
""", unsafe_allow_html=True)

if df_raw.empty:
    st.warning("No Results events found in live_events.json.")
    st.stop()

with st.sidebar:
    st.header("Customize View")
    all_devices = sorted(df_raw["DeviceID"].unique())
    selected_devices = st.multiselect("Headset", all_devices, default=all_devices)
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

df = df_raw[
    (df_raw["DeviceID"].isin(selected_devices)) &
    (df_raw["event_time"].dt.date >= start_date) &
    (df_raw["event_time"].dt.date <= end_date)
].copy()

if df.empty:
    st.info("No data for the selected filters.")
    st.stop()

# ── Build full roster (all 12 profiles) ──────────────────────────────────────
rows = []
active_profiles = df["ProfileNum"].unique() if not df.empty else []

for profile_num in range(1, TOTAL_PROFILES + 1):
    athlete = PROFILE_NAMES.get(profile_num, f"Athlete {profile_num}")
    adf = df[df["ProfileNum"] == profile_num].sort_values("event_time")
    times = adf["Time"].values
    sessions = len(times)

    if sessions > 0:
        avg_t   = float(times.mean())
        best_t  = float(times.min())
        worst_t = float(times.max())
        if sessions >= 2:
            mid   = sessions // 2
            trend = round(float(times[mid:].mean()) - float(times[:mid].mean()), 2)
        else:
            trend = 0.0
        trend_display = "↑ 0.00" if sessions < 2 else (f"↓ {abs(trend):.2f}" if trend < 0 else f"↑ {abs(trend):.2f}")
        avg_str   = f"{avg_t:.2f}"
        best_str  = f"{best_t:.2f}"
        worst_str = f"{worst_t:.2f}"
    else:
        avg_t = best_t = worst_t = trend = 0.0
        trend_display = "—"
        avg_str = best_str = worst_str = "—"

    rows.append({
        "Athlete":    athlete,
        "Profile":    str(profile_num),
        "_profile_num": profile_num,
        "Sessions":   sessions,
        "Avg Time":   avg_str,
        "Best Time":  best_str,
        "Worst Time": worst_str,
        "Trend":      trend_display,
        "_avg":       avg_t,
        "_best":      best_t,
        "_trend":     trend,
        "_sessions":  sessions,
    })

roster_df = pd.DataFrame(rows)
active_roster = roster_df[roster_df["_sessions"] > 0]

# ── KPIs ──────────────────────────────────────────────────────────────────────
fastest_row = active_roster.loc[active_roster["_best"].idxmin()] if not active_roster.empty else None
has_trend   = active_roster[active_roster["_sessions"] >= 2]
if not has_trend.empty:
    best_imp  = has_trend.loc[has_trend["_trend"].idxmin()]
    imp_name  = best_imp["Athlete"]
    imp_delta = f"{best_imp['_trend']:+.2f}s"
else:
    imp_name, imp_delta = "No Data", None

st.markdown(f'<div style="font-size:1.1rem;font-weight:700;color:#1a1a2e;margin-bottom:12px;">{period_label}</div>', unsafe_allow_html=True)
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Sessions",  len(df))
k2.metric("Athletes Active", len(active_roster))
k3.metric("Fastest Time",    f"{fastest_row['_best']:.2f}s" if fastest_row is not None else "—",
          delta=fastest_row["Athlete"] if fastest_row is not None else None, delta_color="off")
k4.metric("Most Gains", imp_name, delta=imp_delta, delta_color="inverse")

st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────────────────
athlete_order = active_roster.sort_values("_avg")["Athlete"].tolist()
color_map = {PROFILE_NAMES[i]: PALETTE[(i-1) % len(PALETTE)] for i in range(1, TOTAL_PROFILES+1)}

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    bar_df = active_roster.sort_values("_avg", ascending=True)
    fig1 = go.Figure(go.Bar(
        x=bar_df["_avg"], y=bar_df["Athlete"], orientation="h",
        marker=dict(color=bar_df["_avg"], colorscale=[[0,TEAL],[0.5,POLLEN],[1,CORAL]], showscale=False),
        text=[f"{v:.2f}s" for v in bar_df["_avg"]], textposition="outside",
    ))
    fig1.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color="#1a1a2e"),
        title=dict(text="Score Breakdown by Athlete", font=dict(size=20, color="#1a1a2e"), x=0, xref="paper"),
        xaxis=dict(title="Time (seconds)", gridcolor="#f0f0f0", zeroline=False,
                   range=[0, active_roster["_avg"].max() * 1.25] if not active_roster.empty else [0, 100]),
        yaxis=dict(title=""),
        margin=dict(l=10, r=120, t=70, b=10), height=380,
    )
    st.plotly_chart(fig1, use_container_width=True, config={"scrollZoom": False, "displayModeBar": False})

with chart_col2:
    fig2 = go.Figure()
    for athlete in athlete_order:
        profile_num = next(k for k, v in PROFILE_NAMES.items() if v == athlete)
        adf = df[df["ProfileNum"] == profile_num].sort_values("event_time").reset_index(drop=True)
        adf["session_num"] = range(1, len(adf) + 1)
        fig2.add_trace(go.Scatter(
            x=adf["session_num"], y=adf["Time"], mode="lines+markers", name=athlete,
            line=dict(width=2.5, color=color_map[athlete]),
            marker=dict(size=9, color=color_map[athlete], line=dict(width=1.5, color="white")),
            hovertemplate=f"<b>{athlete}</b><br>Session %{{x}}<br>Time: %{{y:.2f}}s<extra></extra>",
        ))
    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color="#1a1a2e"),
        title=dict(text="Progress Over Time", font=dict(size=20, color="#1a1a2e"), x=0, xref="paper"),
        xaxis=dict(title="Session Number", gridcolor="#f0f0f0", tickmode="linear", dtick=1),
        yaxis=dict(title="Time (seconds)", gridcolor="#f0f0f0"),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)", borderwidth=0),
        margin=dict(l=10, r=10, t=70, b=10), height=380,
        hovermode="x unified",
    )
    st.plotly_chart(fig2, use_container_width=True, config={"scrollZoom": False, "displayModeBar": False})

st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

# ── Give em a Nudge ───────────────────────────────────────────────────────────
nudge_athletes = []
for _, row in roster_df.iterrows():
    reasons = []
    if row["_sessions"] == 0:
        reasons.append("No sessions logged yet")
    else:
        # Check if last session was more than 7 days ago
        profile_num = row["_profile_num"]
        adf = df[df["ProfileNum"] == profile_num]
        if not adf.empty:
            last_session = adf["event_time"].max().date()
            days_since = (end_date - last_session).days
            if days_since > 7:
                reasons.append(f"Last session {days_since} days ago")
    if reasons:
        nudge_athletes.append({"Athlete": row["Athlete"], "Profile": row["Profile"], "Reasons": reasons})

with st.container(border=True):
    st.markdown("<p style=\"font-size:1.2rem;font-weight:700;color:#1a1a2e;margin-bottom:4px;\">Give 'em a Nudge</p>", unsafe_allow_html=True)
    st.markdown("<p style=\"font-size:0.85rem;color:#888;margin-bottom:12px;\">These athletes could use a little encouragement to get their reps in.</p>", unsafe_allow_html=True)
    if not nudge_athletes:
        st.markdown(f'<p style="color:{TEAL};font-weight:600;">&#10003; Everyone is on track — great work!</p>', unsafe_allow_html=True)
    else:
        # Show in rows of 6
        for i in range(0, len(nudge_athletes), 6):
            chunk = nudge_athletes[i:i+6]
            cols = st.columns(6)
            for col, athlete in zip(cols, chunk):
                with col:
                    st.markdown(f"""
<div style="background:rgba(255,111,89,0.08);border:1.5px solid rgba(255,111,89,0.3);border-radius:12px;padding:14px 16px;margin-bottom:8px;">
    <div style="font-weight:700;font-size:0.95rem;color:#1a1a2e;margin-bottom:4px;">{athlete['Athlete']}</div>
    <div style="font-size:0.75rem;color:#888;margin-bottom:8px;">Profile {athlete['Profile']}</div>
    {"".join(f'<div style="font-size:0.8rem;color:{CORAL};margin-bottom:3px;">· {r}</div>' for r in athlete["Reasons"])}
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

# ── My Roster (sorted by profile number) ─────────────────────────────────────
with st.container(border=True):
    st.markdown('<p style="font-size:1.2rem;font-weight:700;color:#1a1a2e;margin-bottom:4px;">My Roster</p>', unsafe_allow_html=True)
    def style_trend(val):
        if not val or val == "—": return "color:#cccccc;font-weight:400"
        if val.startswith("↓"): return f"color:{TEAL};font-weight:600"
        if val.startswith("↑") and "0.00" not in val: return f"color:{CORAL};font-weight:600"
        return "color:#cccccc;font-weight:400"
    display_cols = ["Athlete","Profile","Sessions","Avg Time","Best Time","Worst Time","Trend"]
    sorted_roster = roster_df.sort_values("_profile_num")[display_cols]
    st.dataframe(sorted_roster.style.map(style_trend, subset=["Trend"]), use_container_width=True, hide_index=True, height=(len(roster_df) + 1) * 35 + 10)
    st.markdown('<p style="font-size:0.75rem;color:#888;">↓ Trend = getting faster (good) &nbsp;·&nbsp; ↑ Trend = getting slower</p>', unsafe_allow_html=True)

st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

# ── Training Log (sorted by profile number) ───────────────────────────────────
with st.container(border=True):
    st.markdown('<p style="font-size:1.2rem;font-weight:700;color:#1a1a2e;margin-bottom:12px;">Training Log</p>', unsafe_allow_html=True)
    sorted_profiles = sorted([p for p in range(1, TOTAL_PROFILES+1) if p in df["ProfileNum"].values])
    cols = st.columns(len(sorted_profiles)) if sorted_profiles else st.columns(1)
    for col, profile_num in zip(cols, sorted_profiles):
        athlete = PROFILE_NAMES.get(profile_num, f"Athlete {profile_num}")
        adf = df[df["ProfileNum"] == profile_num].sort_values("event_time")
        with col:
            st.markdown(f"**{athlete}**")
            st.caption(f"Profile {profile_num}")
            for _, row in adf.iterrows():
                st.markdown(f"**{row['event_time'].strftime('%m/%d')}** &nbsp; <span style='background:rgba(65,234,212,0.12);border:1.5px solid #41EAD4;border-radius:20px;padding:3px 12px;font-weight:600;font-size:0.85rem;color:#1a1a2e;'>{row['Time']:.2f}s</span>", unsafe_allow_html=True)

st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

with st.expander("I Want to See the Raw Data"):
    st.dataframe(
        df[["event_time","Athlete","ProfileNum","DeviceID","Time"]]
        .sort_values("event_time", ascending=False).reset_index(drop=True),
        use_container_width=True
    )