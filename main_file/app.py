# job_portal_dashboard/app.py

import pandas as pd
import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc

# Import data loading
from Data.datasetsql import load_data, load_unique_most_recent_data

# Import pages
from jobpage_status.Daily_Overview import layout as page1_layout, register_callbacks as register_page1_callbacks
from jobpage_status.Monthly_Trend import layout as page2_layout, register_callbacks as register_page2_callbacks
from jobpage_status.Location_Analysis import layout as page3_layout, register_callbacks as register_page3_callbacks
from jobpage_status.Pie_chart import layout as page4_layout, register_callbacks as register_page4_callbacks
from jobpage_status.Mobile_Desktop import layout as page5_layout, register_callbacks as register_page5_callbacks
from jobpage_status.Daily_Overview_Device import layout as page6_layout, register_callbacks as register_page6_callbacks
from jobpage_status.Monthly_Trend_Device import layout as page7_layout, register_callbacks as register_page7_callbacks
from jobpage_status.Device_Location import layout as page8_layout, register_callbacks as register_page8_callbacks
from jobpage_status.Registrysource_bargraph import layout as page9_layout, \
    register_callbacks as register_page9_callbacks

# --- Data Source Selection Options ---
DATA_SOURCE_OPTIONS = [
    {'label': 'Active vs Inactive Based on CV', 'value': 'full'},
    {'label': 'Active vs Inactive Based on Users', 'value': 'latest_unique'}
]

# Initialize App with Bootstrap and FontAwesome (for the icon)
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    title="Job Portal Dashboard"
)


# --- NAVBAR COMPONENT (Reorganized to match PDF) ---
def create_navbar():
    return dbc.Navbar(
        dbc.Container([
            # Brand / Logo (Icon + Text)
            html.A(
                dbc.Row([
                    dbc.Col(html.I(className="fas fa-chart-line fa-lg me-2", style={"color": "#00d2ff"})),
                    dbc.Col(dbc.NavbarBrand("Job Portal Dashboard", className="ms-2")),
                ], align="center", className="g-0"),
                href="/",
                style={"textDecoration": "none"},
            ),

            # Toggler for mobile
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),

            # Links
            dbc.Collapse(
                dbc.Nav([
                    dbc.NavItem(dbc.NavLink("Daily", href="/page-1")),
                    dbc.NavItem(dbc.NavLink("Monthly", href="/page-2")),
                    dbc.NavItem(dbc.NavLink("Location", href="/page-3")),
                    dbc.NavItem(dbc.NavLink("Pie Chart", href="/page-4")),  # Pie Chart

                    # Dropdown for Device Analytics (Matches PDF Arrow)
                    dbc.DropdownMenu(
                        children=[
                            dbc.DropdownMenuItem("Mobile vs Desktop", href="/page-5"),
                            dbc.DropdownMenuItem("Daily Device Trend", href="/page-6"),
                            dbc.DropdownMenuItem("Monthly Device Trend", href="/page-7"),
                            dbc.DropdownMenuItem("Device Location", href="/page-8"),
                        ],
                        nav=True,
                        in_navbar=True,
                        label="Device Analytics",
                    ),

                    dbc.NavItem(dbc.NavLink("Registry Source", href="/page-9")),

                ], className="ms-auto", navbar=True),
                id="navbar-collapse",
                navbar=True,
            ),
        ]),
        color="dark",
        dark=True,
        className="custom-navbar mb-4 sticky-top",  # Uses CSS class
        expand="lg"
    )


# --- APP LAYOUT ---
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='global-data-store', data=None),
    dcc.Store(id='trigger-initial-load', data='full'),

    # Navbar
    create_navbar(),

    dbc.Container([
        # Data Source Selector (Wrapped in Glass Container for visibility)
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Label("Select Data Source:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                    dcc.RadioItems(
                        id='data-source-selector',
                        options=DATA_SOURCE_OPTIONS,
                        value='full',
                        labelStyle={'display': 'inline-block', 'marginRight': '20px'},
                        inputStyle={"marginRight": "5px"}
                    )
                ], className="glass-container")  # Applies glass effect
            ], width=12)
        ], className="mb-3"),

        # Page Content
        html.Div(id='page-content')
    ], fluid=True)
])

# --- 1. REGISTER CALLBACKS ---
register_page1_callbacks(app)
register_page2_callbacks(app)
register_page3_callbacks(app)
register_page4_callbacks(app)
register_page5_callbacks(app)
register_page6_callbacks(app)
register_page7_callbacks(app)
register_page8_callbacks(app)
register_page9_callbacks(app)


# --- 2. DATA LOADING CALLBACKS ---
@callback(
    Output('trigger-initial-load', 'data'),
    Input('data-source-selector', 'value')
)
def set_load_trigger(selected_source):
    return selected_source


@callback(
    Output('global-data-store', 'data'),
    Input('trigger-initial-load', 'data')
)
def load_global_data(data_source_type):
    print(f"Initial Data Load Triggered. Source: {data_source_type}")
    if data_source_type == 'latest_unique':
        try:
            df_result = load_unique_most_recent_data()
        except Exception:
            return pd.DataFrame().to_dict('records')
    else:
        df_result = load_data()

    if df_result is not None and 'application_date' in df_result.columns:
        df_result['application_date'] = df_result['application_date'].astype(str)

    return df_result.to_dict('records') if df_result is not None else []


# --- 3. ROUTING CALLBACK ---
@callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/page-1':
        return page1_layout
    elif pathname == '/page-2':
        return page2_layout
    elif pathname == '/page-3':
        return page3_layout
    elif pathname == '/page-4':
        return page4_layout
    elif pathname == '/page-5':
        return page5_layout
    elif pathname == '/page-6':
        return page6_layout
    elif pathname == '/page-7':
        return page7_layout
    elif pathname == '/page-8':
        return page8_layout
    elif pathname == '/page-9':
        return page9_layout
    else:
        return page1_layout


# --- NAVBAR TOGGLER CALLBACK ---
@callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [dash.State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


if __name__ == '__main__':
    app.run(port=8050, debug=True)