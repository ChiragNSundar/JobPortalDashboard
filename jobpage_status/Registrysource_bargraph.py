# job_portal_dashboard/Register_Source.py

import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc, callback, Input, Output, no_update
import dash_bootstrap_components as dbc
from datetime import datetime


# --- Helper Functions ---
def create_summary_card(title, value, color_class="primary"):
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-title", style={'opacity': '0.9', 'color': 'white'}),
            html.H2(f"{value:,}", className="card-text",style={'fontWeight': 'bold', 'color': 'white'}),
        ]),
        color=color_class, inverse=True, className=f"mb-4 shadow-sm {color_class}"
)

# --- Page Layout ---
layout = dbc.Container([
    html.H2("Count by Registration Source", className="text-center my-4", style={'color': '#2c3e50'}),

    # Filters Section
    dbc.Row([
        dbc.Col([html.Label("Select Date Range:", className="control-label"),
                 dcc.DatePickerRange(
                     id='p9-date-range-filter',
                     display_format='YYYY-MM-DD'
                 )],
                width=12, md=4),
        dbc.Col([html.Label("Select Country:", className="control-label"),
                 dcc.Dropdown(id='p9-country-filter', value=[], multi=True,
                              placeholder="Select countries...")],
                width=12, md=4),
        dbc.Col([html.Label("Select RegSource:", className="control-label"),
                 dcc.Dropdown(id='p9-regsource-filter', value=[], multi=True,
                              placeholder="Select registration sources...")],
                width=12, md=4)
    ], className="mb-4 glass-container"),

    # Summary Cards
    dbc.Row([
        dbc.Col(id='p9-total-applications-card', width=12, md=4),
        dbc.Col(id='p9-active-applications-card', width=12, md=4),
        dbc.Col(id='p9-inactive-applications-card', width=12, md=4),
    ], className="mb-4"),

    # Graph
        html.Div([
        # Optional: Add a Title inside the glass box

        # The Graph
        dcc.Graph(id='p9-cv-graph', style={'height': '500px', 'width':'12'})

    ], className="glass-container")


   # dbc.Row([dbc.Col(dcc.Graph(id='p9-cv-graph'), width=12)])
], fluid=True)


# --- MODIFIED Callback Registration ---
def register_callbacks(app):
    # 1. Callback to Initialize Filters (Triggered by Data Load)
    @app.callback(
        [Output('p9-date-range-filter', 'min_date_allowed'),
         Output('p9-date-range-filter', 'max_date_allowed'),
         Output('p9-date-range-filter', 'start_date'),
         Output('p9-date-range-filter', 'end_date'),
         Output('p9-country-filter', 'options'),
         Output('p9-regsource-filter', 'options')],
        [Input('global-data-store', 'data')]  # Listen to Store
    )
    def populate_initial_filters(json_data):
        if json_data is None:
            return no_update, no_update, no_update, no_update, [], []

        df = pd.DataFrame(json_data)

        # Convert date column
        if 'application_date' in df.columns:
            df['application_date'] = pd.to_datetime(df['application_date'])

        min_date = df['application_date'].min().date()
        max_date = df['application_date'].max().date()

        country_options = [{'label': c, 'value': c} for c in sorted(df['applicant_location'].unique())]

        # Handle potential missing 'regsource' column or NaNs
        if 'regsource' in df.columns:
            reg_sources = [rs for rs in df['regsource'].unique() if pd.notna(rs)]
            regsource_options = [{'label': str(rs), 'value': rs} for rs in sorted(reg_sources)]
        else:
            regsource_options = []

        return min_date, max_date, min_date, max_date, country_options, regsource_options

    # 2. Callback to Update Content (Triggered by Filters OR Data Load)
    @app.callback(
        [Output('p9-cv-graph', 'figure'),
         Output('p9-total-applications-card', 'children'),
         Output('p9-active-applications-card', 'children'),
         Output('p9-inactive-applications-card', 'children')],
        [Input('p9-date-range-filter', 'start_date'),
         Input('p9-date-range-filter', 'end_date'),
         Input('p9-country-filter', 'value'),
         Input('p9-regsource-filter', 'value'),
         Input('data-source-selector', 'value'),
         Input('global-data-store', 'data')]  # Add Store as Input
    )
    def update_page(start_date, end_date, selected_countries, selected_regsources,data_source, json_data):

        if json_data is None:
            return no_update, no_update, no_update, no_update

        df = pd.DataFrame(json_data)

        # --- Data Cleaning ---
        if 'application_date' in df.columns:
            df['application_date'] = pd.to_datetime(df['application_date'])

        filtered_df = df.copy()

        # Handle default dates
        if not start_date: start_date = df['application_date'].min().date()
        if not end_date: end_date = df['application_date'].max().date()

        # Apply Date Filter
        filtered_df = filtered_df[
            (filtered_df['application_date'] >= str(start_date)) &
            (filtered_df['application_date'] <= str(end_date))
            ]

        # Apply Country Filter
        if selected_countries:
            filtered_df = filtered_df[filtered_df['applicant_location'].isin(selected_countries)]

        # Apply RegSource Filter
        if selected_regsources and 'regsource' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['regsource'].isin(selected_regsources)]

        # Handle Empty Data
        if filtered_df.empty:
            empty_fig = go.Figure().update_layout(title="No data available for the selected filters.")
            return empty_fig, \
                create_summary_card("Total Applications", 0, "primary"), \
                create_summary_card("Active CVs", 0, "success"), \
                create_summary_card("Inactive CVs", 0, "warning")

        # Summary Cards
        total_applications = filtered_df.shape[0]
        active_applications = filtered_df[filtered_df['jobpage_status'] == 'Active'].shape[0]
        inactive_applications = filtered_df[filtered_df['jobpage_status'] == 'Inactive'].shape[0]

        suffix = "Users" if data_source == 'latest_unique' else "CVs"

        def generate_bar_line_graph(df_pivot, x_col, title, x_title):
            fig = go.Figure()
            # Plot only the 'Total' column as requested
            fig.add_trace(
                go.Bar(x=df_pivot[x_col], y=df_pivot['Total'], name='Total CVs', marker_color='#191970', opacity=0.9)
            )

            fig.update_layout(
                title=title,
                xaxis=dict(title=x_title),
                yaxis=dict(title=f'Total {suffix} Count', title_font=dict(color='#191970'), tickformat='.0f',
                           side='left',
                           showgrid=True, gridcolor='#e0e0e0'),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                plot_bgcolor='white', paper_bgcolor='white', margin=dict(t=50, b=50, l=50, r=50)
            )
            return fig


        total_card = create_summary_card(f"Total {suffix}", total_applications, "primary")
        active_card = create_summary_card(f"Active {suffix}", active_applications, "success")
        inactive_card = create_summary_card(f"Inactive {suffix}", inactive_applications, "warning")

        # Graph Aggregation
        if 'regsource' in filtered_df.columns:
            regsource_counts = filtered_df.groupby(['regsource', 'jobpage_status']).size().reset_index(name='count')
            regsource_pivot = regsource_counts.pivot(index='regsource', columns='jobpage_status', values='count').fillna(0)
        else:
            # Fallback if column missing
            regsource_pivot = pd.DataFrame(columns=['Active', 'Inactive'])

        # Ensure 'Active' and 'Inactive' columns exist
        if 'Active' not in regsource_pivot.columns: regsource_pivot['Active'] = 0
        if 'Inactive' not in regsource_pivot.columns: regsource_pivot['Inactive'] = 0

        # Calculate Total
        regsource_pivot['Total'] = regsource_pivot['Active'] + regsource_pivot['Inactive']
        regsource_pivot.reset_index(inplace=True)

        # Graph Generation
        fig = generate_bar_line_graph(regsource_pivot, 'regsource',
                                      f'Total {suffix} Count by Registration Source',
                                      'Registration Source')

        return fig, total_card, active_card, inactive_card