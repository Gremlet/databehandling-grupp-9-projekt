import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px


df = pd.read_csv("data/athlete_events.csv")

# Sortera landlistan
countries = sorted(df["NOC"].dropna().unique())
sports = sorted(df["Sport"].dropna().unique())

app = Dash(__name__)
server = app.server  # För Render deploy

app.layout = html.Div([
    html.H1("Olympiska Spelen Dashboard", className="title"),

    html.Div([
        html.Div([
            html.Label("Välj land:"),
            dcc.Dropdown(
                id="country-dropdown",
                options=[{"label": c, "value": c} for c in countries],
                value="FRA",   # Standard-land
                multi=False
            )
        ], className="filter-box"),

        html.Div([
            html.Label("Välj sport(er):"),
            dcc.Dropdown(
                id="sport-dropdown",
                options=[{"label": s, "value": s} for s in sports],
                value=["Athletics"],   # Standard-sport
                multi=True
            )
        ], className="filter-box"),
    ], className="filter-container"),

    
    html.Div([
        html.Div([
            html.H3("Medaljer per sport"),
            dcc.Graph(id="medals-by-sport")
        ], className="graph-box"),

        html.Div([
            html.H3("Åldersfördelning per sport"),
            dcc.Graph(id="age-dist-by-sport")
        ], className="graph-box"),
    ], className="graph-container"),

], className="main-container")


@app.callback(
    Output("medals-by-sport", "figure"),
    Input("country-dropdown", "value")
)
def update_medals(country):
    dff = df[(df["NOC"] == country) & (df["Medal"].notna())]

    if dff.empty:
        return px.bar(title="Inga medaljer i datasetet för detta land.")

    fig = px.histogram(
        dff,
        x="Sport",
        color="Medal",
        title=f"Medaljer per sport för {country}",
        barmode="group"
    )
    fig.update_layout(xaxis={'categoryorder': 'total descending'})
    return fig


@app.callback(
    Output("age-dist-by-sport", "figure"),
    Input("sport-dropdown", "value")
)
def update_age_distribution(selected_sports):
    dff = df[df["Sport"].isin(selected_sports)]

    if dff.empty:
        return px.box(title="Ingen åldersdata för dessa sporter.")

    fig = px.box(
        dff,
        x="Sport",
        y="Age",
        color="Sport",
        title=f"Åldersfördelning för valda sporter"
    )
    return fig

if __name__ == "__main__":
    app.run(debug=True)
