# Dash-app: OS-landstatistik (standard: Frankrike)
# ------------------------------------------------
# Funktioner:
# - Välj land (dropdown)
# - Filtrera säsong (Sommar/Vinter)
# - Välj topp N sporter
# - Grafer:
#   1) Medaljer per OS-år (deduplicerat för laghändelser)
#   2) Medaljer per sport (topp N)
#   3) Åldersfördelning bland medaljörer (histogram)
#   4) Medaljtyper (Gold/Silver/Bronze) – staplat
#   5) Medaljeffektivitet: medaljer per 100 deltagare
#   6) Könsfördelning bland medaljörer per år – staplat
#
# Kör så här:
#   pip install dash plotly pandas numpy
#   python dash_os_country_dashboard.py

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output


# --------------------------
# 1) Läs in och förbered data
# --------------------------
DATA_PATH = Path('athlete_events.csv')
if not DATA_PATH.exists():
    raise FileNotFoundError("Hittar inte 'athlete_events.csv' i aktuell mapp. Lägg filen bredvid detta skript.")

# Läs data
raw = pd.read_csv(DATA_PATH)

# Anonymisera namn enligt uppgiften (SHA-256)
raw["Name_hash"] = raw["Name"].astype(str).apply(lambda x: hashlib.sha256(x.encode()).hexdigest())
raw = raw.drop(columns=["Name"])  # ta bort originalnamn

# Grundstädning
raw["Medal"] = raw["Medal"].astype("category")
raw["Season"] = raw["Season"].astype("category")

# Hjälpfunktion: filtrera på land och säsong
SEASON_ORDER = ["Summer", "Winter"]


def filter_country_season(df: pd.DataFrame, country: str, seasons: list[str]) -> pd.DataFrame:
    sub = df[df["Team"] == country].copy()
    if seasons:
        sub = sub[sub["Season"].isin(seasons)]
    return sub


# Räkna medaljer utan att överräkna laghändelser: drop_duplicates på (Year, Season, Team, Event, Medal)
MEDAL_KEYS = ["Year", "Season", "Team", "Event", "Medal"]


def dedup_medals(df: pd.DataFrame) -> pd.DataFrame:
    m = df[df["Medal"].notna()].copy()
    m = m.drop_duplicates(MEDAL_KEYS)
    return m


# Lista länder till dropdown
countries = (
    raw.groupby("Team")["ID"].nunique().sort_values(ascending=False).index.tolist()
)

# Standardland
DEFAULT_COUNTRY = "France" if "France" in countries else countries[0]

# --------------------------
# 2) Bygga Dash-appen
# --------------------------
app = Dash(__name__)
app.title = "OS – Landstatistik"

controls = html.Div(
    [
        html.Div(
            [
                html.Label("Välj land"),
                dcc.Dropdown(
                    id="country-dd",
                    options=[{"label": c, "value": c} for c in countries],
                    value=DEFAULT_COUNTRY,
                    clearable=False,
                ),
            ],
            className="control"
        ),
        html.Div(
            [
                html.Label("Säsong"),
                dcc.Checklist(
                    id="season-cl",
                    options=[{"label": "Sommar", "value": "Summer"}, {"label": "Vinter", "value": "Winter"}],
                    value=["Summer", "Winter"],
                    inline=True,
                ),
            ],
            className="control"
        ),
        html.Div(
            [
                html.Label("Topp N sporter"),
                dcc.Slider(id="topn-slider", min=5, max=20, step=1, value=10,
                           marks={i: str(i) for i in range(5, 21, 5)}),
            ],
            className="control"
        ),
    ],
    style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr", "gap": "16px", "marginBottom": "12px"},
)

app.layout = html.Div(
    [
        html.H2("OS – Landstatistik (Dash)"),
        html.P("Interaktiv dashboard för att utforska ett lands prestationer i OS."),
        controls,
        html.Div(
            [
                dcc.Graph(id="fig-medals-year"),
                dcc.Graph(id="fig-sport-topn"),
                dcc.Graph(id="fig-age-hist"),
                dcc.Graph(id="fig-medal-types"),
                dcc.Graph(id="fig-efficiency"),
                dcc.Graph(id="fig-gender-year"),
            ],
            style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr",
                "gap": "18px",
            },
        ),
        html.Div(
            [
                html.P(
                    "Obs: Medaljräkning dedupliceras för laghändelser (Year, Season, Team, Event, Medal). "
                    "Medaljeffektivitet beräknas som medaljer per 100 unika deltagare per år."
                )
            ],
            style={"marginTop": "8px", "fontSize": "0.9rem", "color": "#444"},
        ),
    ],
    style={"maxWidth": "1200px", "margin": "0 auto", "padding": "16px"},
)

# --------------------------
# 3) Callbacks
# --------------------------

@app.callback(
    Output("fig-medals-year", "figure"),
    Output("fig-sport-topn", "figure"),
    Output("fig-age-hist", "figure"),
    Output("fig-medal-types", "figure"),
    Output("fig-efficiency", "figure"),
    Output("fig-gender-year", "figure"),
    Input("country-dd", "value"),
    Input("season-cl", "value"),
    Input("topn-slider", "value"),
)

def update_figs(country: str, seasons: list[str], topn: int):
    # Filtrera
    sub = filter_country_season(raw, country, seasons)

    # Medaljer de-duplicerat för team events
    medals = dedup_medals(sub)

    # Medaljer per år
    if len(medals):
        medals_per_year = medals.groupby("Year").size().reset_index(name="Medals")
        fig1 = px.line(
            medals_per_year,
            x="Year",
            y="Medals",
            markers=True,
            title=f"Antal medaljer per OS – {country}"
        )
    else:
        fig1 = px.line(title=f"Antal medaljer per OS – {country}")

    # Medaljer per sport – topp N
    sport_counts = medals.groupby("Sport").size().sort_values(ascending=False).head(topn)
    fig2 = px.bar(
        sport_counts[::-1],  # vänd för horisontell stigande
        orientation="h",
        title=f"Topp {topn} sporter – medaljer för {country}",
        labels={"value": "Medaljer", "index": "Sport"}
    )

    # Ålder – histogram (medaljörer)
    age_data = medals.dropna(subset=["Age"]) if len(medals) else medals
    fig3 = px.histogram(
        age_data,
        x="Age",
        nbins=20,
        title=f"Åldersfördelning bland medaljörer – {country}",
    )

    # Medaljtyper – staplat (per år)
    medal_types = medals.groupby(["Year", "Medal"]).size().reset_index(name="Count")
    # Bevara ordning Gold, Silver, Bronze
    if not medal_types.empty:
        medal_types["Medal"] = pd.Categorical(medal_types["Medal"], ["Gold", "Silver", "Bronze"], ordered=True)
        medal_types = medal_types.sort_values(["Year", "Medal"])
    fig4 = px.bar(
        medal_types,
        x="Year",
        y="Count",
        color="Medal",
        title=f"Medaljtyper per OS – {country}",
        barmode="stack",
    )

    # Medaljeffektivitet: medaljer / 100 deltagare
    participants = sub.groupby("Year")["ID"].nunique().rename("Participants")
    medals_year = medals.groupby("Year").size().rename("Medals")
    eff = pd.concat([participants, medals_year], axis=1).fillna(0)
    eff["Medals_per_100"] = np.where(eff["Participants"]>0, eff["Medals"] / eff["Participants"] * 100, 0)
    eff = eff.reset_index()
    fig5 = px.line(
        eff,
        x="Year",
        y="Medals_per_100",
        markers=True,
        title=f"Medaljeffektivitet (medaljer per 100 deltagare) – {country}"
    )

    # Könsfördelning bland medaljörer per år – staplat
    gender_year = medals.groupby(["Year", "Sex"]).size().reset_index(name="Count")
    fig6 = px.bar(
        gender_year,
        x="Year",
        y="Count",
        color="Sex",
        barmode="stack",
        title=f"Könsfördelning bland medaljörer per OS – {country}"
    )

    # Layout-puts
    for f in (fig1, fig2, fig3, fig4, fig5, fig6):
        f.update_layout(margin=dict(l=20, r=20, t=50, b=40))

    return fig1, fig2, fig3, fig4, fig5, fig6


# Entrypoint
if __name__ == "__main__":
    app.run(debug=True)
