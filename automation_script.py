import os, json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

INPUT_CSV  = os.getenv("INPUT_CSV",  "gantt.csv")
GANTT_PNG  = os.getenv("GANTT_PNG",  "automation_gantt_chart.png")
ORG_NAME   = os.getenv("GITHUB_ORG", "Aletheia-BB")
TODAY      = os.getenv("TODAY", datetime.today().strftime("%Y-%m-%d"))

df_raw = pd.read_csv(INPUT_CSV)
df = pd.DataFrame({
    "Task":   df_raw["title"].fillna("").astype(str),
    "Start":  pd.to_datetime(df_raw["start"], errors="coerce"),
    "Finish": pd.to_datetime(df_raw["end"],   errors="coerce"),
    "Status": df_raw["status"].fillna("").str.strip().str.lower(),
})

status_map = {
    "done":"Completed","completed":"Completed",
    "todo":"To Do","to do":"To Do","backlog":"To Do",
    "in progress":"In Progress",
}
df["Status"] = df["Status"].map(status_map).fillna("To Do")
df = df[df["Task"].str.strip() != ""].copy()
df_g = df.dropna(subset=["Start","Finish"]).copy()
df_g["Duration"] = (df_g["Finish"] - df_g["Start"]).dt.days.clip(lower=1)
df_g = df_g.sort_values(["Status","Start"]).reset_index(drop=True)

def clean(text, mx=36):
    for p in ["[BUG / FEATURE]","[BUG / POLÍTICA]","[FEATURE / PRODUTO]",
              "[BUG]","[FEATURE]","[UX]","[UI]","[CONFIG]","[SEGURANÇA]","[PESQUISA]"]:
        if text.startswith(p):
            text = text[len(p):].strip(); break
    return (text[:mx]+"…") if len(text) > mx else text

df_g["Label"] = df_g["Task"].apply(clean)

# ── Design tokens (GitHub dark) ────────────────────────────────────────
BG     = "#0d1117"
PANEL  = "#161b22"
GRID   = "#21262d"
TEXT   = "#e6edf3"
MUTED  = "#7d8590"
BORDER = "#30363d"
TODAY_C= "#fbbf24"

SC = {
    "Completed":   ("#238636", "#2ea043"),
    "In Progress": ("#9e6a03", "#d29922"),
    "To Do":       ("#1f6feb", "#388bfd"),
}

n     = len(df_g)
min_d = df_g["Start"].min()
max_d = df_g["Finish"].max()
pad   = pd.Timedelta(days=1)
today = pd.Timestamp(TODAY)
ROW   = 0.52
STEP  = 1.0

fig_h = max(7, n * 0.70 + 3.0)
fig, ax = plt.subplots(figsize=(20, fig_h), facecolor=BG)
ax.set_facecolor(PANEL)
fig.subplots_adjust(left=0.30, right=0.96, top=0.88, bottom=0.10)

xlmin = mdates.date2num((min_d - pad).to_pydatetime())
xlmax = mdates.date2num((max_d + pad + pd.Timedelta(days=1)).to_pydatetime())
ax.set_xlim(xlmin, xlmax)
ax.set_ylim(-STEP/2, (n - 0.5) * STEP)
ax.invert_yaxis()

# daily vertical grid
for d in pd.date_range(min_d - pad, max_d + pad + pd.Timedelta(days=1), freq="D"):
    ax.axvline(mdates.date2num(d.to_pydatetime()), color=GRID, lw=0.7, zorder=1)

# alternating row bands
for i in range(n):
    ax.axhspan(i*STEP - STEP/2 + 0.03, i*STEP + STEP/2 - 0.03,
               color="#ffffff", alpha=0.018 if i%2==0 else 0, zorder=0)

# group separator between statuses
s_list = df_g["Status"].tolist()
for i in range(1, n):
    if s_list[i] != s_list[i-1]:
        ax.axhline((i-0.5)*STEP, color=BORDER, lw=1.0, ls="--", alpha=0.9, zorder=2)

# today line
if min_d <= today <= max_d + pd.Timedelta(days=4):
    tx = mdates.date2num(today.to_pydatetime())
    ax.axvline(tx, color=TODAY_C, lw=1.8, ls="--", zorder=6, alpha=0.85)
    ax.text(tx + 0.08, (n-0.5)*STEP - 0.2, "Today",
            color=TODAY_C, fontsize=8.5, fontweight="bold",
            va="bottom", ha="left", zorder=7)

# bars
for i, row in df_g.iterrows():
    y    = i * STEP
    edge, face = SC.get(row["Status"], ("#4b5563","#6b7280"))
    start = mdates.date2num(row["Start"].to_pydatetime())
    dur   = row["Duration"]

    ax.barh(y, dur, left=start, height=ROW+0.12,
            color=face, alpha=0.12, zorder=2)

    ax.add_patch(FancyBboxPatch(
        (start, y - ROW/2), dur, ROW,
        boxstyle="round,pad=0.03",
        facecolor=face, edgecolor=edge,
        lw=1.3, zorder=3, alpha=0.92,
    ))

    ax.text(start + 0.14, y,
            f"{row['Start'].strftime('%b %d')} → {row['Finish'].strftime('%b %d')}",
            va="center", ha="left", fontsize=8.2,
            color="white", fontfamily="monospace",
            fontweight="bold", zorder=5)

    # ax.text(start + dur + 0.12, y, f"{dur}d",
    #         va="center", ha="left", fontsize=8,
    #         color=face, fontfamily="monospace",
    #         fontweight="bold", zorder=5)

# y-axis task labels
ax.set_yticks([i*STEP for i in range(n)])
ax.set_yticklabels(df_g["Label"], fontsize=11, color=TEXT)
ax.yaxis.set_tick_params(length=0, pad=12)

# x-axis every 2 days
ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
plt.setp(ax.xaxis.get_majorticklabels(),
         rotation=35, ha="right", fontsize=9.5, color=TEXT)
ax.xaxis.set_tick_params(length=4, color=BORDER)

for s in ax.spines.values():
    s.set_edgecolor(BORDER); s.set_linewidth(0.8)
ax.spines["left"].set_visible(False)

# legend
present = df_g["Status"].unique()
patches = [
    mpatches.Patch(facecolor=SC[s][1], edgecolor=SC[s][0], lw=1.2, label=s)
    for s in ["To Do","In Progress","Completed"] if s in present
]
fig.legend(handles=patches, loc="upper center",
           bbox_to_anchor=(0.63, 0.97), ncol=len(patches),
           frameon=True, framealpha=0.25,
           facecolor="#1c2128", edgecolor=BORDER,
           fontsize=11.5, handlelength=1.5,
           handleheight=0.95, labelcolor=TEXT)

fig.text(0.63, 1.002,
         f"Gantt Chart — {ORG_NAME}",
         ha="center", va="bottom",
         fontsize=17, fontweight="bold", color=TEXT,
         transform=ax.transAxes)
fig.text(0.63, 0.962,
         f"Timeline  {min_d.strftime('%b %d')} – {max_d.strftime('%b %d, %Y')}  ·  {n} tasks with scheduled dates",
         ha="center", va="bottom",
         fontsize=10, color=MUTED,
         transform=ax.transAxes)

plt.savefig(GANTT_PNG, dpi=180, bbox_inches="tight",
            facecolor=BG, edgecolor="none")
plt.close()
print(f"✅ {GANTT_PNG} gerado com {n} tarefas  ({min_d.strftime('%b %d')} – {max_d.strftime('%b %d, %Y')})")
