import hashlib as hl
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
from Demos.RegCreateKeyTransacted import classname
from dash import Dash, dcc, html, Input, Output, dash

#läser in filen
DATA_PATH = Path('athlete_events.csv')

#"döper" om den
raw = pd.read_csv(DATA_PATH)

#Anonymiserar namnen med: (SHA-256)
raw["Name"] = raw["Name"].apply(lambda x:hl.sha256(str(x).encode("utf-8")).hexdigest())
raw = raw.drop(columns=["Name"]) #tar bort originalnamn

#omvandlar kolumnens datatyp från object (strängar) till kategori
raw["Medal"] = raw["Medal"].astype("category")
raw["Season"] = raw["Season"].astype("category")

#filtrerar säsong
SEASON_ORDER = ["Summer", "Winter"]

#skapar en DataFrame "sub" med rader där landet matchar.
def filter_country_season(df: pd.DataFrame, country: str, seasons: list[str]) -> pd.DataFrame:
    sub = df[df["Team"] == "France"].copy()
    if seasons:
        sub = sub[sub["Season"].isin(seasons)]
    return sub

#definerar en lista med kolumnnamn
MEDAL_KEYS = ["Year", "Season", "Team", "Event", "Medal"]


def dedup_medals(df: pd.DataFrame) -> pd.DataFrame:
    m = df[df["Medal"].notna()].copy() #skapar en kopia av alla rader där "Medal" inte är NaN.
    m = m.drop_duplicates(MEDAL_KEYS) #tar bort rader som är identiska i alla kolumner
    return m

#skapar en lista med länder, sorterade efter antal unika deltagare, från flest till minst
countries = (
    raw.groupby("Team")["ID"].nunique().sort_values(ascending=False).index.tolist()
)

# Landet vi presenterar inom OS: France
DEFAULT_COUNTRY = "France" if "France" in countries else countries[0]

#byggandet av dash-appen, fortsättning följer.....
app = dash.Dash(__name__)


controls = html.Div([
html.Label("Välj land"),
dcc.Dropdown(
    id="country-dropdown",
    options=countries, multi=True,
    value=DEFAULT_COUNTRY,
    clearable=False,
    className = "control"
)])

html.Div(
            [
html.Label("Säsong"),
dcc.Checklist(
    id="season-cl",
    options=[{"label": "Sommar", "value": "Summer"}, {"label": "Vinter", "value": "Winter"}],
    value=["Summer", "Winter"],
    inline=True,
    className="control"
)]),


if __name__ == "__main__":
    app.run(debug=True)
