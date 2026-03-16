import os
import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
import json, textwrap
from datetime import datetime

load_dotenv()

INPUT_CSV  = os.getenv("INPUT_CSV",  "gantt.csv")
GANTT_PNG  = os.getenv("GANTT_PNG",  "automation_gantt_chart.png")
KANBAN_PNG = os.getenv("KANBAN_PNG", "automation_kanban_board.png")
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

def short_label(text, max_len=48):
    for p in ["[BUG / FEATURE]","[BUG / POLÍTICA]","[FEATURE / PRODUTO]",
              "[BUG]","[FEATURE]","[UX]","[UI]","[CONFIG]","[SEGURANÇA]","[PESQUISA]"]:
        if text.startswith(p):
            text = text[len(p):].strip()
            break
    return (text[:max_len] + "…") if len(text) > max_len else text

df_g["Label"] = df_g["Task"].apply(short_label)

color_map  = {"Completed":"#22c55e","In Progress":"#f59e0b","To Do":"#60a5fa"}
border_map = {"Completed":"#16a34a","In Progress":"#d97706","To Do":"#2563eb"}

min_date = df_g["Start"].min()
max_date = df_g["Finish"].max()
pad      = pd.Timedelta(days=1)
today    = pd.Timestamp(TODAY)

def to_ms(dt):  return int(dt.timestamp() * 1000)
def days_ms(d): return d * 86400000

fig = go.Figure()
n = len(df_g)

for i in range(n):
    fig.add_shape(
        type="rect", xref="paper", yref="y",
        x0=0, x1=1, y0=i - 0.5, y1=i + 0.5,
        fillcolor="rgba(255,255,255,0.025)" if i % 2 == 0 else "rgba(0,0,0,0)",
        line_width=0, layer="below",
    )

if min_date <= today <= max_date + pd.Timedelta(days=5):
    fig.add_shape(
        type="line", xref="x", yref="paper",
        x0=to_ms(today), x1=to_ms(today), y0=0, y1=1,
        line=dict(dash="dash", color="rgba(251,191,36,0.65)", width=2),
        layer="above",
    )
    fig.add_annotation(
        x=to_ms(today), y=1.01, xref="x", yref="paper",
        text="Today", showarrow=False,
        font=dict(color="rgba(251,191,36,0.9)", size=11),
        xanchor="center",
    )

legend_added = set()
for i, row in df_g.iterrows():
    color  = color_map.get(row["Status"], "#9ca3af")
    border = border_map.get(row["Status"], "#6b7280")
    show   = row["Status"] not in legend_added
    s_str  = row["Start"].strftime("%b %d")
    e_str  = row["Finish"].strftime("%b %d")
    fig.add_trace(go.Bar(
        orientation="h",
        x=[days_ms(row["Duration"])],
        y=[row["Label"]],
        base=[to_ms(row["Start"])],
        marker=dict(color=color, line=dict(color=border, width=1.5), opacity=0.92),
        name=row["Status"],
        legendgroup=row["Status"],
        showlegend=show,
        hovertemplate=(
            f"<b>{row['Task']}</b><br>"
            f"Status: <b>{row['Status']}</b><br>"
            f"Start: {row['Start'].strftime('%b %d, %Y')}<br>"
            f"End: {row['Finish'].strftime('%b %d, %Y')}<br>"
            f"Duration: {row['Duration']} day(s)<extra></extra>"
        ),
        text=f"  {s_str} → {e_str}",
        textposition="inside", insidetextanchor="start",
        textfont=dict(color="white", size=10, family="'Courier New', monospace"),
        width=0.55,
    ))
    legend_added.add(row["Status"])

fig.update_xaxes(
    type="date",
    range=[(min_date - pad).strftime("%Y-%m-%d"), (max_date + pad).strftime("%Y-%m-%d")],
    tickformat="%b %d", dtick="D1", tickangle=0,
    title_text="",
    gridcolor="rgba(255,255,255,0.07)", showgrid=True, zeroline=False,
    tickfont=dict(size=10), ticks="outside", ticklen=4,
)
fig.update_yaxes(autorange="reversed", title_text="", tickfont=dict(size=11), showgrid=True)
fig.update_layout(
    title=dict(text=(
        f"Gantt Chart — {ORG_NAME}"
        "<br><span style='font-size:14px;font-weight:normal;opacity:0.75;'>"
        f"{min_date.strftime('%b %d')} – {max_date.strftime('%b %d, %Y')}  ·  {n} tasks"
        "</span>"
    )),
    barmode="overlay", bargap=0.32,
    legend=dict(orientation="h", yanchor="bottom", y=1.07, xanchor="center", x=0.5,
                bgcolor="rgba(0,0,0,0)", font=dict(size=13)),
    margin=dict(l=10, r=20, t=130, b=50),
    height=max(480, n * 52 + 185),
    plot_bgcolor="rgba(0,0,0,0)",
)
fig.write_image(GANTT_PNG, scale=2, width=1100, height=max(480, n * 52 + 185))
print(f"✅ {GANTT_PNG} gerado com {n} tarefas")
