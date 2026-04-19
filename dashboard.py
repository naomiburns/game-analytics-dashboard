"""
Line graph: Unique users per device over the last 7 days.
Data source: live_events.json  (fields: client_ts, device, user_id)
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ── 1. Load data ──────────────────────────────────────────────────────────────
json_path = Path(__file__).parent / "live_events.json"
events = json.load(open(json_path))

# ── 2. Determine the 7-day window (anchored to latest event in the data) ──────
all_ts = [r["client_ts"] for r in events]
window_end   = datetime.fromtimestamp(max(all_ts), tz=timezone.utc).replace(
                   hour=23, minute=59, second=59, microsecond=999999)
window_start = window_end - timedelta(days=6)   # 7 days inclusive

# ── 3. Aggregate: unique users per (date, device) ─────────────────────────────
# Structure: { device -> { date -> set(user_ids) } }
agg: dict[str, dict[str, set]] = defaultdict(lambda: defaultdict(set))

for r in events:
    ts = datetime.fromtimestamp(r["client_ts"], tz=timezone.utc)
    if window_start <= ts <= window_end:
        day   = ts.date().isoformat()          # "YYYY-MM-DD"
        dev   = r.get("device", "Unknown")
        uid   = r["user_id"]
        agg[dev][day].add(uid)

# ── 4. Build complete date range (fill missing days with 0) ───────────────────
date_range = [
    (window_start + timedelta(days=i)).date().isoformat()
    for i in range(7)
]

devices = sorted(agg.keys())

# ── 5. Plot ───────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))

colors = plt.cm.tab10.colors
for idx, device in enumerate(devices):
    counts = [len(agg[device].get(d, set())) for d in date_range]
    ax.plot(date_range, counts,
            marker="o", linewidth=2, markersize=6,
            color=colors[idx % len(colors)],
            label=device)

ax.set_title("Unique Users by Device — Last 7 Days", fontsize=14, fontweight="bold")
ax.set_xlabel("Date")
ax.set_ylabel("Unique Users (COUNT DISTINCT user_id)")
ax.set_xticks(date_range)
ax.tick_params(axis="x", rotation=30)
ax.yaxis.get_major_locator().set_params(integer=True)
ax.legend(title="Device", loc="upper left")
ax.grid(True, alpha=0.3, linestyle="--")
ax.set_ylim(bottom=0)

plt.tight_layout()

out_path = Path(__file__).parent / "unique_users_by_device.png"
plt.savefig(out_path, dpi=130)
print(f"Saved: {out_path}")
plt.show()
