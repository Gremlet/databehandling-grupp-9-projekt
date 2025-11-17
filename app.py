import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html

# Lada data
df = pd.read_csv("data/athlete_events.csv")
noc = pd.read_csv("data/noc_regions.csv")

noc = noc[['NOC', 'region']]

# fr = df.merge(noc, how="left", on="NOC")

# Filtera Frankrike
fr = df[df["Team"] == "France"]

# Mest medaljer per sport
top_sports = (
    fr.dropna(subset=["Medal"])
    .groupby("Sport")["Medal"]
    .count()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

fig_top_sports = px.bar(
    top_sports,
    x="Sport",
    y="Medal",
    title="Top 10 sporter där Frankrike fått flest medaljer",
    labels={"Medal": "Antal medaljer"}
)

# Medaljer per år
medals_year = (
    fr.dropna(subset=["Medal"])
    .groupby("Year")["Medal"]
    .count()
    .reset_index()
)

fig_medals_year = px.line(
    medals_year,
    x="Year",
    y="Medal",
    title="Antal medaljer för Frankrike per år"
)

# Åldersfördelning per sport
fig_age = px.histogram(
    fr.dropna(subset=["Age"]),
    x="Age",
    color="Sport",
    nbins=30,
    title="Åldersfördelning i franska sporter"
)

# Skapa app
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Frankrike - OS Dashboard", style={"textAlign": "center"}),

    html.H2("Topp sporter (mest medaljer)"),
    dcc.Graph(figure=fig_top_sports),

    html.H2("Medaljer per år"),
    dcc.Graph(figure=fig_medals_year),

    html.H2("Ålderfördelning i sporter"),
    dcc.Graph(figure=fig_age),
])

# Starta server
if __name__ == "__main__":
    app.run(debug=True)
