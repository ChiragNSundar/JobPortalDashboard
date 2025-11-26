# job_portal_dashboard/Mobile_Desktop.py

import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc, callback, Input, Output, no_update
import dash_bootstrap_components as dbc
from datetime import datetime

# Filter options
DEVICE_TYPE_OPTIONS = [
    {'label': 'All', 'value': 'All'},
    {'label': 'Mobile', 'value': 'Mobile'},
    {'label': 'Desktop', 'value': 'Desktop'}
]


# Helper functions
def create_summary_card(title, value, color):
    """Creates a styled summary card."""
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-title"),
            html.H2(f"{value}", className="card-text"),
        ]),
        color=color, inverse=True, className="text-center shadow-sm mb-3"
    )


# Page layout
layout = dbc.Container([
    html.H2("Page 5: Mobile vs Desktop Users Breakdown", className="text-center my-4", style={'color': '#2c3e50'}),

    # Filters Section
    dbc.Row([
        # 1. Date Range (Width changed to 3)
        dbc.Col([html.Label("Select Date Range:", style={'fontWeight': 'bold'}),
                 dcc.DatePickerRange(id='p5-date-range-picker',
                                     display_format='YYYY-MM-DD')],
                width=12, md=3),

        # 2. Country Filter (Width changed to 3)
        dbc.Col([html.Label("Select Country:", style={'fontWeight': 'bold'}),
                 dcc.Dropdown(id='p5-country-filter', value=[], multi=True,
                              placeholder="Select countries...")],
                width=12, md=3),

        # 3. Device Filter (Width changed to 3)
        dbc.Col([html.Label("Filter by Device Type:", style={'fontWeight': 'bold'}),
                 dcc.Dropdown(id='p5-device-filter',
                              options=DEVICE_TYPE_OPTIONS,
                              value=['All'],  # Default to 'All' as a list
                              multi=True,  # Enable multi-select
                              placeholder="Select device type...")],
                width=12, md=3),

        # 4. NEW: Applicant Status Filter (Width 3)
        dbc.Col([html.Label("Filter by Status:", style={'fontWeight': 'bold'}),
                 dcc.Dropdown(id='p5-status-filter',
                              value=[],
                              multi=True,
                              placeholder="Select status...")],
                width=12, md=3),
    ], className="mb-4"),

    # Summary Cards
    dbc.Row([
        dbc.Col(id='p5-total-applications-card', width=12, md=3),
        dbc.Col(id='p5-mobile-total-card', width=12, md=3),
        dbc.Col(id='p5-desktop-total-card', width=12, md=3),
        dbc.Col(id='p5-mobile-percentage-card', width=12, md=3),
    ], className="mb-4"),

    # Pie Chart Graph (Device Type Split)
    dbc.Row([
        dbc.Col(
            html.Div(
                dcc.Graph(id='p5-device-pie-chart'),
                style={
                    'height': '70vh',
                    'width': '100%',
                    'border': '1px solid #e0e0e0',
                    'borderRadius': '5px',
                    'padding': '10px',
                    'backgroundColor': 'white'
                }
            ),
            width=12
        )
    ])
], fluid=True)


# --- MODIFIED Callback Registration ---
def register_callbacks(app):
    """Registers all callbacks for Page 5 (Device Type Analysis)."""

    # 1. Callback to Initialize Filters (Triggered by Data Load)
    @app.callback(
        [Output('p5-date-range-picker', 'min_date_allowed'),
         Output('p5-date-range-picker', 'max_date_allowed'),
         Output('p5-date-range-picker', 'start_date'),
         Output('p5-date-range-picker', 'end_date'),
         Output('p5-country-filter', 'options'),
         Output('p5-status-filter', 'options')],  # Added Output for Status
        [Input('global-data-store', 'data')]
    )
    def update_page_5_filters(json_data):
        """Populates date pickers, country, and status options based on the DataFrame."""
        if json_data is None:
            return no_update, no_update, no_update, no_update, [], []

        df = pd.DataFrame(json_data)

        # Convert date column
        if 'application_date' in df.columns:
            df['application_date'] = pd.to_datetime(df['application_date'])

        min_date = df['application_date'].min().date()
        max_date = df['application_date'].max().date()

        # Country Options
        country_options = [{'label': country, 'value': country} for country in
                           sorted(df['applicant_location'].unique())]

        # Status Options (NEW)
        status_options = []
        if 'application_status' in df.columns:
            # Drop NaNs, convert to string, sort unique values
            unique_statuses = sorted(df['application_status'].dropna().astype(str).unique())
            status_options = [{'label': s.title(), 'value': s} for s in unique_statuses]

        return min_date, max_date, min_date, max_date, country_options, status_options

    # 2. Callback to Update Content (Triggered by Filters OR Data Load)
    @app.callback(
        [Output('p5-device-pie-chart', 'figure'),
         Output('p5-total-applications-card', 'children'),
         Output('p5-mobile-total-card', 'children'),
         Output('p5-desktop-total-card', 'children'),
         Output('p5-mobile-percentage-card', 'children')],
        [Input('p5-date-range-picker', 'start_date'),
         Input('p5-date-range-picker', 'end_date'),
         Input('p5-country-filter', 'value'),
         Input('p5-device-filter', 'value'),
         Input('p5-status-filter', 'value'),  # Added Input for Status
         Input('data-source-selector', 'value'),
         Input('global-data-store', 'data')]
    )
    def update_page_5_content(start_date, end_date, selected_countries, selected_devices, selected_statuses,
                              data_source, json_data):
        """Updates the pie chart and summary cards based on user filters."""

        if json_data is None:
            return no_update, no_update, no_update, no_update, no_update

        df = pd.DataFrame(json_data)

        # --- Data Cleaning ---
        if 'application_date' in df.columns:
            df['application_date'] = pd.to_datetime(df['application_date'])

        filtered_df = df.copy()

        # Ensure 'dtype' column exists and clean its values
        if 'dtype' in filtered_df.columns:
            filtered_df['dtype'] = filtered_df['dtype'].astype(str).str.strip().str.title()
        else:
            empty_fig = go.Figure().update_layout(title="Data Error: 'dtype' column missing.")
            return empty_fig, \
                create_summary_card("Total Applications", 0, "primary"), \
                create_summary_card("Mobile Users", 0, "warning"), \
                create_summary_card("Desktop Users", 0, "info"), \
                create_summary_card("Mobile %", "N/A", "secondary")

        # --- Date Filtering ---
        if not start_date: start_date = df['application_date'].min().date()
        if not end_date: end_date = df['application_date'].max().date()

        filtered_df = filtered_df[
            (filtered_df['application_date'] >= str(start_date)) &
            (filtered_df['application_date'] <= str(end_date))
            ]

        # --- Country Filtering ---
        if selected_countries:
            filtered_df = filtered_df[filtered_df['applicant_location'].isin(selected_countries)]

        # --- Status Filtering (NEW) ---
        if selected_statuses:
            filtered_df = filtered_df[filtered_df['application_status'].isin(selected_statuses)]

        # --- Device Type Filtering ---
        if not isinstance(selected_devices, list):
            selected_devices = [selected_devices]

        if 'All' not in selected_devices and selected_devices:
            filtered_df = filtered_df[filtered_df['dtype'].isin(selected_devices)]

        # --- Handle Empty Data ---
        if filtered_df.empty:
            empty_fig = go.Figure().update_layout(title="No data available for the selected filters.")
            return empty_fig, \
                create_summary_card("Total Applications", 0, "primary"), \
                create_summary_card("Mobile Users", 0, "warning"), \
                create_summary_card("Desktop Users", 0, "info"), \
                create_summary_card("Mobile %", "0.00%", "secondary")

        # --- Summary Cards Calculations ---
        total_count = filtered_df.shape[0]
        mobile_count = filtered_df[filtered_df['dtype'] == 'Mobile'].shape[0]
        desktop_count = filtered_df[filtered_df['dtype'] == 'Desktop'].shape[0]

        mobile_percentage = (mobile_count / total_count) * 100 if total_count > 0 else 0.0

        suffix = "Users" if data_source == 'latest_unique' else "CVs"

        def generate_device_pie_chart(df_pie, title):
            """Generates a simple Pie Chart showing Mobile vs Desktop split."""
            df_pie['devicetype_display'] = df_pie['dtype'].astype(str).str.title().fillna('Unknown')

            color_map = {
                'Mobile': 'orange',
                'Desktop': 'blue',
                'Unknown': 'grey'
            }

            fig = go.Figure(data=[go.Pie(
                labels=df_pie['devicetype_display'],
                values=df_pie['count'],
                hole=0,
                marker=dict(colors=[color_map.get(label, 'grey') for label in df_pie['devicetype_display']]),
                textinfo='percent+label',
                insidetextorientation='radial'
            )])

            fig.update_layout(
                title=title,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(t=50, b=50, l=50, r=50),
                height=600,
            )
            return fig

        total_card = create_summary_card(f"Total {suffix}", total_count, "primary")
        mobile_card = create_summary_card(f"Mobile {suffix}", mobile_count, "warning")
        desktop_card = create_summary_card(f"Desktop {suffix}", desktop_count, "info")
        mobile_perc_card = create_summary_card("Mobile %", f"{mobile_percentage:.2f}%", "secondary")

        # --- Data Aggregation for Pie Chart ---
        device_counts = filtered_df.groupby('dtype').size().reset_index(name='count')

        # Generate Pie Chart
        fig = generate_device_pie_chart(device_counts, 'Overall Device Type Distribution')

        return fig, total_card, mobile_card, desktop_card, mobile_perc_card