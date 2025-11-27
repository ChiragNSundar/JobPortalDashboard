# job_portal_dashboard/Pie_Chart.py

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import html, dcc, callback, Input, Output, no_update
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta

# Filter options (Static options)
STATUS_OPTIONS = [
    {'label': 'All', 'value': 'All'},
    {'label': 'Active', 'value': 'Active'},
    {'label': 'Inactive', 'value': 'Inactive'}
]


# Helper functions
def create_summary_card(title, value, color_class="primary"):
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-title", style={'opacity': '0.9', 'color': 'white'}),
            html.H2(f"{value:,}", className="card-text",style={'fontWeight': 'bold', 'color': 'white'}),
        ]),
        color=color_class, inverse=True, className=f"mb-4 shadow-sm {color_class}"
)


# --- Modified generate_sunburst_chart function ---
def generate_sunburst_chart(df_sunburst, title):
    # Ensure 'jobpage_status' is treated as a distinct category and handle potential NaNs
    df_sunburst['cv_status_display'] = df_sunburst['jobpage_status'].fillna('Unknown')

    # Define colors for statuses for consistency
    color_map = {
        'Active': 'green',
        'Inactive': 'red',
        'Unknown': 'grey'
    }

    # Create the sunburst chart using Plotly Express
    fig = px.sunburst(df_sunburst,
                      path=['applicant_location', 'cv_status_display'],  # Hierarchical path: Country -> Status
                      values='total_resumes',
                      title=title,
                      color='cv_status_display',  # Color segments by status
                      color_discrete_map=color_map,  # Apply defined colors
                      branchvalues="total"  # Ensure values sum up correctly at each level
                      )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=50, b=50, l=50, r=50),
        height=900,  # Adjust height as needed
    )
    return fig


# Page layout
layout = dbc.Container([
    html.H2("Page 4: Country and Status Breakdown", className="text-center my-4", style={'color': '#2c3e50'}),

    # Filters Section
    dbc.Row([
        dbc.Col([html.Label("Select Date Range:", className="control-label"),
                 dcc.DatePickerRange(id='p4-date-range-picker',
                                     display_format='YYYY-MM-DD')],
                width=12, md=4),
        dbc.Col([html.Label("Select Country:", className="control-label"),
                 dcc.Dropdown(id='p4-country-filter', value=[], multi=True,
                              placeholder="Select countries...")],
                width=12, md=4),
        dbc.Col([html.Label("Select Status:", className="control-label"),
                 dcc.Dropdown(id='p4-status-filter',
                              options=STATUS_OPTIONS,
                              value=['All'],  # Default to 'All' as a list
                              multi=True,  # Enable multi-select
                              placeholder="Select status...")],
                width=12, md=4),
    ], className="mb-4 glass-container"),

    # Summary Cards
    dbc.Row([
        dbc.Col(id='p4-total-applications-card', width=12, md=4),
        dbc.Col(id='p4-active-applications-card', width=12, md=4),
        dbc.Col(id='p4-inactive-applications-card', width=12, md=4),
    ], className="mb-4"),

    # Sunburst Chart Graph
    dbc.Row([
        dbc.Col(
            html.Div(
                dcc.Graph(id='p4-nested-status-sunburst'),
                style={
                    'height': '120vh',
                    'width': '100%',
                    'border': '1px solid #e0e0e0',
                    'borderRadius': '5px',
                    'padding': '10px',
                    'backgroundColor': 'white'
                }
            ),
            width=12, className="glass-container"
        )
    ])
], fluid=True)


# --- MODIFIED Callback Registration ---
def register_callbacks(app):
    # 1. Callback to Initialize Filters (Triggered by Data Load)
    @app.callback(
        [Output('p4-date-range-picker', 'min_date_allowed'),
         Output('p4-date-range-picker', 'max_date_allowed'),
         Output('p4-date-range-picker', 'start_date'),
         Output('p4-date-range-picker', 'end_date'),
         Output('p4-country-filter', 'options')],
        [Input('global-data-store', 'data')]  # Listen to the store
    )
    def update_page_4_filters(json_data):
        if json_data is None:
            return no_update, no_update, no_update, no_update, []

        df = pd.DataFrame(json_data)

        # Convert date column
        if 'application_date' in df.columns:
            df['application_date'] = pd.to_datetime(df['application_date'])

        min_date = df['application_date'].min().date()
        max_date = df['application_date'].max().date()

        country_options = [{'label': country, 'value': country} for country in
                           sorted(df['applicant_location'].unique())]

        return min_date, max_date, min_date, max_date, country_options

    # 2. Callback to Update Content (Triggered by Filters OR Data Load)
    @app.callback(
        [Output('p4-nested-status-sunburst', 'figure'),
         Output('p4-total-applications-card', 'children'),
         Output('p4-active-applications-card', 'children'),
         Output('p4-inactive-applications-card', 'children')],
        [Input('p4-date-range-picker', 'start_date'),
         Input('p4-date-range-picker', 'end_date'),
         Input('p4-country-filter', 'value'),
         Input('p4-status-filter', 'value'),
         Input('data-source-selector', 'value'),
         Input('global-data-store', 'data')]  # Add Store as Input
    )
    def update_page_4_content(start_date, end_date, selected_countries, selected_statuses,data_source, json_data):

        # Handle missing data
        if json_data is None:
            return no_update, no_update, no_update, no_update

        df = pd.DataFrame(json_data)

        # --- Data Cleaning ---
        if 'application_date' in df.columns:
            df['application_date'] = pd.to_datetime(df['application_date'])

        filtered_df = df.copy()

        if 'jobpage_status' in filtered_df.columns:
            filtered_df['jobpage_status'] = filtered_df['jobpage_status'].str.strip().str.capitalize()
        else:
            empty_fig = go.Figure().update_layout(title="Data Error: 'jobpage_status' column missing.")
            return empty_fig, \
                create_summary_card("Total Applications", 0, "primary"), \
                create_summary_card("Active CVs", 0, "success"), \
                create_summary_card("Inactive CVs", 0, "warning")

        # --- Date Filtering ---
        # Handle default dates if inputs are None (e.g. initial load)
        if not start_date:
            start_date = df['application_date'].min().date()
        if not end_date:
            end_date = df['application_date'].max().date()

        # Apply Date Filter
        # Convert string inputs to datetime for comparison
        filtered_df = filtered_df[
            (filtered_df['application_date'] >= str(start_date)) &
            (filtered_df['application_date'] <= str(end_date))
            ]

        # --- Country Filtering ---
        if selected_countries:
            filtered_df = filtered_df[filtered_df['applicant_location'].isin(selected_countries)]

        # --- Status Filtering ---
        if not isinstance(selected_statuses, list):
            selected_statuses = [selected_statuses]

        if 'All' not in selected_statuses and selected_statuses:
            filtered_df = filtered_df[filtered_df['jobpage_status'].isin(selected_statuses)]

        # --- Handle Empty Data ---
        if filtered_df.empty:
            empty_fig = go.Figure().update_layout(title="No data available for the selected filters.")
            return empty_fig, \
                create_summary_card("Total Applications", 0, "primary"), \
                create_summary_card("Active CVs", 0, "success"), \
                create_summary_card("Inactive CVs", 0, "warning")

        # --- Summary Cards ---
        total_applications = filtered_df.shape[0]
        active_applications = filtered_df[filtered_df['jobpage_status'] == 'Active'].shape[0]
        inactive_applications = filtered_df[filtered_df['jobpage_status'] == 'Inactive'].shape[0]

        suffix = "Users" if data_source == 'latest_unique' else "CVs"

        total_card = create_summary_card(f"Total {suffix}", total_applications, "primary")
        active_card = create_summary_card(f"Active {suffix}", active_applications, "success")
        inactive_card = create_summary_card(f"Inactive {suffix}", inactive_applications, "warning")

        # --- Data Aggregation for Sunburst Chart ---
        nested_counts = filtered_df.groupby(['applicant_location', 'jobpage_status']).size().reset_index(
            name='total_resumes')

        # Generate Sunburst Chart
        fig = generate_sunburst_chart(nested_counts, 'Application Status Breakdown by Country')

        return fig, total_card, active_card, inactive_card