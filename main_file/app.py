# job_portal_dashboard/app.py

import pandas as pd
import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc

# Import data loading (keep your existing imports)
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
from jobpage_status.Registrysource_bargraph import layout as page9_layout, register_callbacks as register_page9_callbacks

# --- Data Source Selection Options ---
DATA_SOURCE_OPTIONS = [
    {'label': 'Active vs Inactive Based on CV', 'value': 'full'},
    {'label': 'Active vs Inactive Based on Users', 'value': 'latest_unique'}
]

# --- View Mode Options (Global) ---
VIEW_MODE_OPTIONS = [
    {'label': 'Based on CV Count', 'value': 'cv'},
    {'label': 'Based on Unique Users', 'value': 'user'}
]

# Initialize App
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)


# --- LAYOUT ---
def create_navbar():
    return dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Daily Overview", href="/page-1")),
            dbc.NavItem(dbc.NavLink("Monthly Trend", href="/page-2")),
            dbc.NavItem(dbc.NavLink("Location Analysis", href="/page-3")),
            dbc.NavItem(dbc.NavLink("Pie-Chart", href="/page-4")),
            dbc.NavItem(dbc.NavLink("Mobile Desktop", href="/page-5")),
            dbc.NavItem(dbc.NavLink("Daily Device Overview", href="/page-6")),
            dbc.NavItem(dbc.NavLink("Monthly Device Overview", href="/page-7")),
            dbc.NavItem(dbc.NavLink("Device Location Overview", href="/page-8")),
            dbc.NavItem(dbc.NavLink("Registry Source Overview", href="/page-9")),
            # ... other links ...
        ],
        brand="Job Portal Dashboard",
        brand_href="/",
        color="dark",
        dark=True,
        className="mb-4"
    )


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='global-data-store', data=None),  # Holds the JSON data
    dcc.Store(id='trigger-initial-load', data='full'),

    create_navbar(),

    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Label("Select Data Source at Startup:", style={'fontWeight': 'bold'}),
                dcc.RadioItems(
                    id='data-source-selector',
                    options=DATA_SOURCE_OPTIONS,
                    value='full',
                    labelStyle={'display': 'inline-block', 'marginTop': '10px', 'marginRight': '20px'}
                )
            ], width=12)
        ], className="my-3")
    ]),

    html.Div(id='page-content')
])

# --- 1. REGISTER CALLBACKS IMMEDIATELY ---
# We pass 'app' only. The callbacks inside these functions will listen to 'global-data-store'.
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

    # Convert Date objects to strings for JSON serialization
    # (Important: dcc.Store stores JSON, not Pandas objects)
    if 'application_date' in df_result.columns:
        df_result['application_date'] = df_result['application_date'].astype(str)

    return df_result.to_dict('records')


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


if __name__ == '__main__':
    app.run(port=8050, debug=True)