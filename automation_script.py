import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.dates import DateFormatter
from dotenv import load_dotenv

load_dotenv()

INPUT_CSV   = os.getenv("INPUT_CSV", "gantt.csv")
OUTPUT_CSV  = os.getenv("OUTPUT_CSV", "gant.csv")
GANTT_PNG   = os.getenv("GANTT_PNG", "automation_gantt_chart.png")
KANBAN_PNG  = os.getenv("KANBAN_PNG", "automation_kanban_board.png")

df_raw = pd.read_csv(INPUT_CSV)

if {"title", "start", "end", "status"}.issubset(df_raw.columns):
    df = pd.DataFrame({
        "Task":   df_raw["title"].fillna("").astype(str),
        "Start":  df_raw["start"],
        "Finish": df_raw["end"],
        "Status": df_raw["status"].fillna("").astype(str),
    })
else:
    df = df_raw.rename(columns={
        "task":   "Task",
        "start":  "Start",
        "end":    "Finish",
        "status": "Status",
    })

df = df[df["Task"].str.strip() != ""].copy()

status_map = {
    "done":        "Completed",
    "completed":   "Completed",
    "todo":        "To Do",
    "to do":       "To Do",
    "backlog":     "To Do",
    "in progress": "In Progress",
}

df["Status"] = (
    df["Status"]
    .str.strip()
    .str.lower()
    .map(status_map)
    .fillna("To Do")
)

df.to_csv(OUTPUT_CSV, index=False)

for col in ["Start", "Finish"]:
    df[col] = pd.to_datetime(df[col], errors="coerce")

df_gantt = df.dropna(subset=["Start", "Finish"]).copy()
df_gantt["Duration"] = (df_gantt["Finish"] - df_gantt["Start"]).dt.days.clip(lower=1)
df_sorted = df_gantt.sort_values("Start").reset_index(drop=True)

status_colors = {
    "Completed":   "#4CAF50",
    "In Progress": "#FFC107",
    "To Do":       "#03A9F4",
}

fig, ax = plt.subplots(figsize=(10, 6))
for _, row in df_sorted.iterrows():
    ax.barh(
        y=row["Task"],
        width=row["Duration"],
        left=row["Start"],
        color=status_colors.get(row["Status"], "#757575"),
        edgecolor="black",
    )
ax.set_xlabel("Date")
ax.set_title("Gantt Chart — Aletheia")
ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
fig.savefig(GANTT_PNG)
plt.close()

statuses   = ["To Do", "In Progress", "Completed"]
col_width  = 1.0 / len(statuses)
y_start    = 0.9
y_step     = 0.1

fig2, ax2 = plt.subplots(figsize=(8, 5))
ax2.axis("off")

for idx, status in enumerate(statuses):
    tasks = df[df["Status"] == status]["Task"].tolist()
    header_x = idx * col_width + col_width / 2
    ax2.text(header_x, 1.0, status, ha="center", va="top", fontsize=12, weight="bold")
    y = y_start
    for task in tasks:
        rect_x = idx * col_width + 0.02
        rect_y = y - y_step + 0.02
        rect_w = col_width - 0.04
        rect_h = y_step - 0.04
        rect = FancyBboxPatch(
            (rect_x, rect_y), rect_w, rect_h,
            boxstyle="round,pad=0.02",
            edgecolor="black",
            facecolor="#E0F7FA",
        )
        ax2.add_patch(rect)
        ax2.text(rect_x + 0.01, rect_y + rect_h / 2, task, va="center", fontsize=8)
        y -= y_step

plt.tight_layout()
fig2.savefig(KANBAN_PNG, bbox_inches="tight")
plt.close()

print(f"✅ Gerado: {OUTPUT_CSV}, {GANTT_PNG}, {KANBAN_PNG}")
