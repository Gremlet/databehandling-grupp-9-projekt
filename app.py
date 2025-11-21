from dash import Dash
import pandas as pd
from plots import (
    france_medals,
    france_medals_per_games,
    fencing_medals,
    top_fencing_medals,
    athletics_medals,
    long_distance,
    east_africa_over_time,
    top_xc_skiing,
    medals_over_time_map,
)
from layout import create_layout

app = Dash(__name__)

# generate figures from plots.py
fig_france_medals = france_medals()
fig_france_medals_per_games = france_medals_per_games()
fig_fencing = fencing_medals()
fig_top_fencing = top_fencing_medals()
fig_athletics = athletics_medals()
fig_ld = long_distance()
fig_east_africa = east_africa_over_time()
fig_xc_ski = top_xc_skiing()
fig_world_map = medals_over_time_map()

app.layout = create_layout(
    fig_france_medals,
    fig_france_medals_per_games,
    fig_fencing,
    fig_top_fencing,
    fig_athletics,
    fig_ld,
    fig_east_africa,
    fig_xc_ski,
    fig_world_map,
)

if __name__ == "__main__":
    app.run(debug=True)
