import streamlit as st
import json
import pandas as pd
import plotly.express as px
from datetime import datetime, timezone, timedelta
from pathlib import Path

st.title("📡 Game Analytics Dashboard")
st.write("Hello! The app is working.")

# Load data
json_path = Path(__file__).parent / "live_events.json"
events = json.load(open(json_path))
df = pd.DataFrame(events)
df["event_time"] = pd.to_datetime(df["client_ts"], unit="s")

# Sidebar filters
devices = sorted(df["device"].dropna().unique())
selected_devices = st.sidebar.multiselect("Device", devices, default=devices)
show_chart = st.sidebar.checkbox("Show chart", value=True)

# Date filter — last 7 days by default
max_date = df["event_time"].max().date()
min_date = df["event_time"].min().date()
start_date, end_date = st.sidebar.date_input("Date range", value=[max_date - timedelta(days=6), max_date])

# Filter
filtered = df[
    (df["event_time"].dt.date >= start_date) &
    (df["event_time"].dt.date <= end_date) &
    (df["device"].isin(selected_devices))
]

# Chart
if show_chart:
    chart_df = (
        filtered.groupby([filtered["event_time"].dt.date, "device"])["user_id"]
        .nunique().reset_index()
        .rename(columns={"event_time": "date", "user_id": "unique_users"})
    )
    fig = px.line(chart_df, x="date", y="unique_users", color="device",
                  title="Unique Users by Device")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Filtered Data")
st.dataframe(filtered)