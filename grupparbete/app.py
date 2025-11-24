# Dash-app: OS-landstatistik (Frankrike)
# ------------------------------------------------
# Funktioner:
# - Välj land (dropdown)
# - Filtrera säsong (Sommar/Vinter)
# - Välj topp N sporter
# - Grafer

# 1) Medaljer per OS-år (deduplicerat för laghändelser)
# 2) Medaljer per sport (topp N)
# 3) Åldersfördelning bland medaljörer (histogram)
# 4) Medaljtyper (Gold/Silver/Bronze) – staplat
# 5) Medaljeffektivitet: medaljer per 100 deltagare
# 6) Könsfördelning bland medaljörer per år – staplat


import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

# 1) Läs in och förbered data

# Skapa ett Path-objekt som pekar på CSV-filen med OS-datan
DATA_PATH = Path("athlete_events.csv")

# Kolla om filen finns – annars ge ett tydligt felmeddelande
if not DATA_PATH.exists():
    raise FileNotFoundError("Hittar inte 'athlete_events.csv' i aktuell mapp. Lägg filen bredvid detta skript.")

# Läs in datan i en pandas-DataFrame
raw = pd.read_csv(DATA_PATH)

# Anonymisera namn enligt uppgiften (SHA-256)
# Vi skapar en ny kolumn 'Name_hash' där vi ersätter namnet med en hash-sträng
raw["Name_hash"] = raw["Name"].astype(str).apply(lambda x: hashlib.sha256(x.encode()).hexdigest())

# Ta bort originalkolumnen med riktiga namn för att anonymisera datan
raw = raw.drop(columns=["Name"])

# Grundstädning: gör om 'Medal' och 'Season' till kategoriska variabler
# Det är effektivare och trevligare när vi grupperar och plottar
raw["Medal"] = raw["Medal"].astype("category")
raw["Season"] = raw["Season"].astype("category")

# Hjälplist för säsong – kan användas om man vill ha en viss ordning
SEASON_ORDER = ["Summer", "Winter"]

# Hjälpfunktion: filtrera på land och säsong
def filter_country_season(df: pd.DataFrame, country: str, seasons: list[str]) -> pd.DataFrame:
    """
    Filtrerar datan till ett visst land och valda säsonger (Sommar/Vinter).
    """
    # Välj bara rader där Team = valt land
    sub = df[df["Team"] == country].copy()

    # Om användaren har valt en eller flera säsonger, filtrera på dem
    if seasons:
        sub = sub[sub["Season"].isin(seasons)]

    return sub

# Nyckelkolumner som definierar en unik medaljhändelse
# används för att inte överräkna lagmedaljer
MEDAL_KEYS = ["Year", "Season", "Team", "Event", "Medal"]

def dedup_medals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Plockar ut medaljrader och tar bort dubbletter baserat på MEDAL_KEYS.
    Detta gör att ett lag inte räknas flera gånger för samma medalj.
    """
    # Välj bara rader där Medal inte är NaN (dvs riktiga medaljer)
    m = df[df["Medal"].notna()].copy()

    # Ta bort dubbletter, t.ex. flera lagmedlemmar i samma event
    m = m.drop_duplicates(MEDAL_KEYS)
    return m

# Lista länder till dropdown:
# Gruppar på 'Team', räknar unika ID (idrottare), sorterar, och tar ut index som lista
countries = (
    raw.groupby("Team")["ID"].nunique()
    .sort_values(ascending=False)
    .index
    .tolist()
)

# Standardland i dropdown: Frankrike om det finns, annars första landet i listan
DEFAULT_COUNTRY = "France" if "France" in countries else countries[0]

# 2) Bygg Dash-app

# Skapa själva Dash-appen
app = Dash(__name__)
app.title = "OS – Landstatistik"  # Sidtitel i webbläsaren

# Kontrollpanel med dropdown, checkboxes och slider
controls = html.Div(
    [
        # Välj land
        html.Div(
            [
                html.Label("Välj land"),
                dcc.Dropdown(
                    id="country-dd",  # id används i callback
                    options=[{"label": c, "value": c} for c in countries],  # alla länder
                    value=DEFAULT_COUNTRY,  # förvalt land
                    clearable=False,  # kan inte rensa bort valet helt
                ),
            ],
            className="control"
        ),
        # Välj säsong (Sommar/Vinter)
        html.Div(
            [
                html.Label("Säsong"),
                dcc.Checklist(
                    id="season-cl",  # id för säsongsfiltret
                    options=[
                        {"label": "Sommar", "value": "Summer"},
                        {"label": "Vinter", "value": "Winter"},
                    ],
                    value=["Summer", "Winter"],  # båda valda som standard
                    inline=True,  # visa valen på samma rad
                ),
            ],
            className="control"
        ),
        # Välj topp N sporter
        html.Div(
            [
                html.Label("Topp N sporter"),
                dcc.Slider(
                    id="topn-slider",
                    min=5,
                    max=20,
                    step=1,
                    value=10,  # standard = topp 10
                    marks={i: str(i) for i in range(5, 21, 5)},  # markeringar vid 5,10,15,20
                ),
            ],
            className="control"
        ),
    ],
    # Gör kontrollpanelen till en grid med tre kolumner (land, säsong, topp N)
    style={
        "display": "grid",
        "gridTemplateColumns": "1fr 1fr 1fr",
        "gap": "16px",
        "marginBottom": "12px",
    },
)

# Hela appens layout (hur sidan ser ut)
app.layout = html.Div(
    [
        html.H2("OS – Landstatistik (Dash)"),
        html.P("Interaktiv dashboard för att utforska ett lands prestationer i OS."),
        controls,  # vår kontrollpanel
        html.Div(
            [
                # Plats för 6 stycken grafer (de fylls av callbacken längre ner)
                dcc.Graph(id="fig-medals-year"),
                dcc.Graph(id="fig-sport-topn"),
                dcc.Graph(id="fig-age-hist"),
                dcc.Graph(id="fig-medal-types"),
                dcc.Graph(id="fig-efficiency"),
                dcc.Graph(id="fig-gender-year"),
            ],
            # Layout: 2 kolumner med grafer
            style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr",
                "gap": "18px",
            },
        ),
        # Liten informationsruta längst ner
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
    # Ser till att sidan inte ska vara för bred och ligg mer centrerad
    style={"maxWidth": "1200px", "margin": "0 auto", "padding": "16px"},
)

# 3) Callbacks

# Kopplar ihop inputs (dropdown, checklist, slider) med outputs (6 grafer)
@app.callback(
    Output("fig-medals-year", "figure"),
    Output("fig-sport-topn", "figure"),
    Output("fig-age-hist", "figure"),
    Output("fig-medal-types", "figure"),
    Output("fig-efficiency", "figure"),
    Output("fig-gender-year", "figure"),
    Input("country-dd", "value"),   # valt land
    Input("season-cl", "value"),    # valda säsonger
    Input("topn-slider", "value"),  # topp N sporter
)
def update_figs(country: str, seasons: list[str], topn: int):
    """
    Den här funktionen körs varje gång användaren ändrar land, säsong eller topp N.
    Den filtrerar datan och bygger sex Plotly-figurer som returneras till graferna.
    """

    # Filtrera på land och säsong
    sub = filter_country_season(raw, country, seasons)

    # Plocka ut medaljer (deduplicerat så att lag inte räknas flera gånger)
    medals = dedup_medals(sub)

    # 1) Medaljer per år
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
        # Om inga medaljer hittas – tom figur
        fig1 = px.line(title=f"Antal medaljer per OS – {country}")

    # 2) Medaljer per sport – topp N
    sport_counts = (
        medals.groupby("Sport").size()
        .sort_values(ascending=False)
        .head(topn)
    )
    fig2 = px.bar(
        sport_counts[::-1],  # vänd så att den populäraste sportens stapel hamnar längst upp
        orientation="h",
        title=f"Topp {topn} sporter – medaljer för {country}",
        labels={"value": "Medaljer", "index": "Sport"},
    )

    # 3) Ålder – histogram (medaljörer)
    age_data = medals.dropna(subset=["Age"]) if len(medals) else medals
    fig3 = px.histogram(
        age_data,
        x="Age",
        nbins=20,
        title=f"Åldersfördelning bland medaljörer – {country}",
    )

    # 4) Medaljtyper – staplat (per år)
    medal_types = medals.groupby(["Year", "Medal"]).size().reset_index(name="Count")

    # Se till att ordningen blir Gold, Silver, Bronze (inte alfabetisk)
    if not medal_types.empty:
        medal_types["Medal"] = pd.Categorical(
            medal_types["Medal"],
            ["Gold", "Silver", "Bronze"],
            ordered=True,
        )
        medal_types = medal_types.sort_values(["Year", "Medal"])

    fig4 = px.bar(
        medal_types,
        x="Year",
        y="Count",
        color="Medal",
        title=f"Medaljtyper per OS – {country}",
        barmode="stack",  # stackade staplar = totalen + fördelning
    )

    # 5) Medaljeffektivitet: medaljer / 100 deltagare
    # Antal deltagare per år (unika ID)
    participants = sub.groupby("Year")["ID"].nunique().rename("Participants")
    # Antal medaljer per år
    medals_year = medals.groupby("Year").size().rename("Medals")

    # Lägg ihop till en DataFrame
    eff = pd.concat([participants, medals_year], axis=1).fillna(0)

    # Beräkna medaljer per 100 deltagare, undvik division med 0
    eff["Medals_per_100"] = np.where(
        eff["Participants"] > 0,
        eff["Medals"] / eff["Participants"] * 100,
        0,
    )

    eff = eff.reset_index()

    fig5 = px.line(
        eff,
        x="Year",
        y="Medals_per_100",
        markers=True,
        title=f"Medaljeffektivitet (medaljer per 100 deltagare) – {country}",
    )

    # 6) Könsfördelning bland medaljörer per år – staplat
    gender_year = medals.groupby(["Year", "Sex"]).size().reset_index(name="Count")
    fig6 = px.bar(
        gender_year,
        x="Year",
        y="Count",
        color="Sex",
        barmode="stack",
        title=f"Könsfördelning bland medaljörer per OS – {country}",
    )

    # layout-fix: marginaler runt graferna
    for f in (fig1, fig2, fig3, fig4, fig5, fig6):
        f.update_layout(margin=dict(l=20, r=20, t=50, b=40))

    # Returnera alla sex figurer till respektive dcc.Graph
    return fig1, fig2, fig3, fig4, fig5, fig6


# Entrypoint – kör bara appen om filen körs direkt (inte om den importeras)
if __name__ == "__main__":
    app.run(debug=True)