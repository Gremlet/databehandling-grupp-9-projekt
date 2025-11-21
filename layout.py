from dash import html, dcc


def create_layout(
    fig_france_medals,
    fig_france_medals_per_games,
    fig_fencing,
    fig_top_fencing,
    fig_athletics,
    fig_ld,
    fig_east_africa,
    fig_xc_ski,
    fig_world_map,
):
    return html.Div(
        style={"padding": "20px"},
        children=[
            html.H1("Olympics Performance Dashboard"),
            html.H2("France Overview"),
            dcc.Graph(figure=fig_france_medals),
            dcc.Graph(figure=fig_france_medals_per_games),
            html.H2("Fencing Analysis"),
            dcc.Graph(figure=fig_fencing),
            dcc.Graph(figure=fig_top_fencing),
            html.H2("Athletics Analysis"),
            dcc.Graph(figure=fig_athletics),
            dcc.Graph(figure=fig_ld),
            dcc.Graph(figure=fig_east_africa),
            html.H2("Winter Sports"),
            dcc.Graph(figure=fig_xc_ski),
            html.H2("Medals Over Time (World Map)"),
            dcc.Graph(figure=fig_world_map),
        ],
    )
