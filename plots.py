import plotly.express as px
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from normalize_noc import normalize_noc
import hashlib

# read files
olympics = pd.read_csv("./data/athlete_events.csv")
noc = pd.read_csv("./data/noc_regions.csv")

# get France data
france_df = olympics.loc[olympics["NOC"] == "FRA"]
france_event_medals = france_df[france_df["Medal"].notna()].drop_duplicates(
    subset=["Games", "Event", "Medal"]
)
france_event_medals["Medal"].groupby(france_event_medals["Sport"]).size()

# anonymise name column
olympics["Name"] = olympics["Name"].apply(
    lambda x: hashlib.sha256(x.encode()).hexdigest()
)

# normalise NOCs so old or defunct IOC codes map to right country
clean = normalize_noc(olympics, noc)

# get all medals with correct NOC
event_medals = clean[clean["Medal"].notna()].drop_duplicates(
    subset=["Games", "Event", "NOC_folded", "Medal"]
)

print(event_medals)


def france_medals():
    # get event medals so individual team medals are not counted as multiple medals
    # team medals only count as 1 medal for the country even if each athlete receives a medal

    france_medals = (
        france_event_medals.groupby("Sport")["Medal"]
        .count()
        .sort_values(ascending=False)
    )

    france_medals = pd.DataFrame(france_medals).head(20)

    fig = px.bar(france_medals, x=france_medals.index, y="Medal")

    fig.update_layout(
        xaxis_tickangle=270,
        yaxis_title="Medal Count",
        margin=dict(l=20, r=20, t=50, b=100),
        title={
            "text": "Sports France has won most medals in",
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
    )
    return fig


def france_medals_per_games():
    france_by_games = (
        france_event_medals.groupby(["Games"])["Medal"]
        .count()
        .reset_index()
        .sort_values(by="Medal", ascending=False)
    )

    france_by_games = france_by_games.sort_index()

    summer = france_by_games.loc[france_by_games["Games"].str.contains("Summer")]
    winter = france_by_games.loc[france_by_games["Games"].str.contains("Winter")]

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            "France's medal count by Summer Games",
            "France's medal count by Winter Games",
        ),
    )

    fig.add_trace(
        go.Bar(x=summer["Games"], y=summer["Medal"], name="Summer"), row=1, col=1
    )

    fig.add_trace(
        go.Bar(x=winter["Games"], y=winter["Medal"], name="Winter"), row=1, col=2
    )

    fig.update_xaxes(tickangle=270)
    fig.update_yaxes(title_text="Medal Count", row=1, col=1)
    fig.update_yaxes(title_text="Medal Count", row=1, col=2)

    fig.update_layout(
        height=600, width=1100, showlegend=False, margin=dict(l=20, r=20, t=80, b=80)
    )

    return fig


def fencing_medals():

    # France has won its most medals in fencing
    # Fencing performance over time

    all_fencing_medals = (
        event_medals[event_medals["Sport"] == "Fencing"]
        .groupby("Games")["Medal"]
        .size()
        .rename("Total_fencing")
    )

    fra_fencing_medals = (
        france_event_medals[france_event_medals["Sport"] == "Fencing"]
        .groupby("Games")["Medal"]
        .size()
        .rename("France_fencing")
    )

    fencing_compare = (
        pd.concat([fra_fencing_medals, all_fencing_medals], axis=1)
        .fillna(0)
        .sort_index()
    )

    fencing_compare["Percent"] = (
        fencing_compare["France_fencing"] / fencing_compare["Total_fencing"] * 100
    )

    fig = make_subplots(specs=[[{"secondary_y": True}]])  # dual-axis magic

    fig.add_trace(
        go.Bar(
            x=fencing_compare.index,
            y=fencing_compare["Total_fencing"],
            name="Total Fencing Medals",
            marker_color="steelblue",
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=fencing_compare.index,
            y=fencing_compare["Percent"],
            name="France % of all Fencing Medals",
            mode="lines+markers",
            line=dict(color="firebrick", width=3),
            opacity=0.6,
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title="France's Fencing Performance Over Time",
        xaxis_title="Games",
        yaxis_title="Total Fencing Medals",
        legend=dict(x=0.9, y=1.2),
        height=600,
        margin=dict(l=20, r=20, t=80, b=80),
    )

    fig.update_yaxes(
        title_text="Percentage of All Fencing Medals (%)", secondary_y=True
    )

    return fig


def top_fencing_medals():
    fencing_medals = (
        event_medals[event_medals["Sport"] == "Fencing"]
        .groupby("NOC_folded")["Medal"]
        .count()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    fig = px.bar(
        fencing_medals,
        x="NOC_folded",
        y="Medal",
        title="Top Countries in Fencing (Event-Level Medals)",
    )

    fig.update_layout(xaxis_title="Country", yaxis_title="Medal count")

    return fig


def athletics_medals():
    athletics_medals = (
        event_medals[event_medals["Sport"] == "Athletics"]
        .groupby("NOC_folded")["Medal"]
        .count()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    fig = px.bar(
        athletics_medals,
        x="NOC_folded",
        y="Medal",
        title="Top Countries in Athletics (Event-Level Medals)",
    )

    fig.update_layout(xaxis_title="Country", yaxis_title="Medal count")

    return fig


def long_distance():
    # Long distance events

    long_distance_events = [
        "Athletics Women's Marathon",
        "Athletics Men's Marathon",
        "Athletics Men's 3,000 metres Steeplechase",
        "Athletics Women's 3,000 metres Steeplechase",
        "Athletics Women's 5,000 metres",
        "Athletics Men's 5,000 metres",
        "Athletics Men's 10,000 metres",
        "Athletics Women's 10,000 metres",
        "Athletics Women's Marathon",
        "Athletics Men's Marathon",
    ]

    ld_medals = event_medals[
        (event_medals["Sport"] == "Athletics")
        & (event_medals["Event"].isin(long_distance_events))
    ]

    ld_medal_counts = (
        ld_medals.groupby("NOC_folded")["Medal"]
        .count()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    fig = px.bar(
        ld_medal_counts,
        x="NOC_folded",
        y="Medal",
        title="Top Countries in Long-Distance Athletics",
    )

    fig.update_layout(xaxis_title="Country", yaxis_title="Medal count")

    return fig


def east_africa_over_time():
    # Timeline of East African dominance

    long_distance_events = [
        "Athletics Women's Marathon",
        "Athletics Men's Marathon",
        "Athletics Men's 3,000 metres Steeplechase",
        "Athletics Women's 3,000 metres Steeplechase",
        "Athletics Women's 5,000 metres",
        "Athletics Men's 5,000 metres",
        "Athletics Men's 10,000 metres",
        "Athletics Women's 10,000 metres",
        "Athletics Women's Marathon",
        "Athletics Men's Marathon",
    ]
    ld_medals = event_medals[
        (event_medals["Sport"] == "Athletics")
        & (event_medals["Event"].isin(long_distance_events))
    ]

    east_africa = (
        ld_medals[ld_medals["NOC"].isin(["KEN", "ETH"])]
        .groupby(["Year", "NOC", "Games"])["Medal"]
        .count()
        .reset_index()
    )

    east_africa

    fig = px.line(
        east_africa,
        x="Year",
        y="Medal",
        color="NOC",
        title="Rise of Kenya and Ethiopia in Long-Distance Running",
    )
    return fig


def top_xc_skiing():
    xc_ski_medals = (
        event_medals[event_medals["Sport"] == "Cross Country Skiing"]
        .groupby("NOC_folded")["Medal"]
        .count()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    fig = px.bar(
        xc_ski_medals,
        x="NOC_folded",
        y="Medal",
        title="Top Countries in Cross Country Skiing (Event-Level Medals)",
    )
    fig.update_layout(xaxis_title="Country", yaxis_title="Medal count")
    return fig


def medals_over_time_map():
    yearly_medals = (
        event_medals.groupby(["Year", "NOC"]).size().reset_index(name="Count")
    )

    yearly_medals = yearly_medals.merge(noc[["NOC", "region"]], on="NOC", how="left")

    yearly_medals = yearly_medals.dropna(subset=["region"])

    fig = px.choropleth(
        yearly_medals,
        locations="region",
        locationmode="country names",
        color="Count",
        hover_name="region",
        animation_frame="Year",
        color_continuous_scale="Plasma",
        title="Olympic medals over time",
    )
    return fig
