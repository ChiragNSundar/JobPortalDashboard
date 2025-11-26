# job_portal_dashboard/Location_Analysis.py

import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc, callback, Input, Output, no_update
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta


# Helper functions (Unchanged)
def create_summary_card(title, value, color):
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-title"),
            html.H2(f"{value:,}", className="card-text"),
        ]),
        color=color, inverse=True, className="text-center shadow-sm mb-3"
    )

# Page layout
layout = dbc.Container([
    html.H2("Page 3: Location Breakdown", className="text-center my-4", style={'color': '#2c3e50'}),

    # Filters Section
    dbc.Row([
        dbc.Col([html.Label("Select Date Range:", style={'fontWeight': 'bold'}),
                 dcc.DatePickerRange(id='p3-date-range-picker',
                                     # Limits will be set by callback
                                     display_format='YYYY-MM-DD')],
                width=12, md=6),
    ], className="mb-4"),

    # Summary Cards
    dbc.Row([
        dbc.Col(id='p3-total-applications-card', width=12, md=4),
        dbc.Col(id='p3-active-applications-card', width=12, md=4),
        dbc.Col(id='p3-inactive-applications-card', width=12, md=4),
    ], className="mb-4"),

    # Graph with increased height and width
    dbc.Row([
        dbc.Col(
            html.Div(
                dcc.Graph(id='p3-location-cv-graph'),
                style={
                    'height': '80vh',
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
    # 1. Callback to Initialize Date Picker Limits (Triggered by Data Load)
    @app.callback(
        [Output('p3-date-range-picker', 'min_date_allowed'),
         Output('p3-date-range-picker', 'max_date_allowed'),
         Output('p3-date-range-picker', 'start_date'),
         Output('p3-date-range-picker', 'end_date')],
        [Input('global-data-store', 'data')]  # Listen to store, not URL
    )
    def update_page_3_filters(json_data):
        if json_data is None:
            return no_update, no_update, no_update, no_update

        df = pd.DataFrame(json_data)

        # Ensure date column is datetime
        if 'application_date' in df.columns:
            df['application_date'] = pd.to_datetime(df['application_date'])

        min_date = df['application_date'].min().date()
        max_date = df['application_date'].max().date()

        return min_date, max_date, min_date, max_date

    # 2. Callback to Update Content (Triggered by Date Picker OR Data Load)
    @app.callback(
        [Output('p3-location-cv-graph', 'figure'),
         Output('p3-total-applications-card', 'children'),
         Output('p3-active-applications-card', 'children'),
         Output('p3-inactive-applications-card', 'children')],
        [Input('p3-date-range-picker', 'start_date'),
         Input('p3-date-range-picker', 'end_date'),
         Input('data-source-selector', 'value'),
         Input('global-data-store', 'data')]  # Add Store as Input
    )
    def update_page_3_content(start_date, end_date,data_source, json_data):

        # Handle missing data
        if json_data is None:
            return no_update, no_update, no_update, no_update

        df = pd.DataFrame(json_data)

        # Ensure date column is datetime (needed for filtering)
        if 'application_date' in df.columns:
            df['application_date'] = pd.to_datetime(df['application_date'])

        # Handle case where start/end are None (e.g., initial load before first callback fires)
        if not start_date:
            start_date = df['application_date'].min().date()
        if not end_date:
            end_date = df['application_date'].max().date()

        # Filter Data
        filtered_df = df.copy()

        # Convert input strings to datetime for comparison if necessary,
        # but pandas usually handles string vs datetime comparison well.
        filtered_df = filtered_df[
            (filtered_df['application_date'] >= str(start_date)) &
            (filtered_df['application_date'] <= str(end_date))
            ]

        # Handle Empty Filtered Data
        if filtered_df.empty:
            empty_fig = go.Figure().update_layout(title="No data available for the selected filters.")
            return (empty_fig,
                    create_summary_card("Total Applications", 0, "primary"),
                    create_summary_card("Active CVs", 0, "success"),
                    create_summary_card("Inactive CVs", 0, "warning"))

        # Summary Cards
        total_applications = filtered_df.shape[0]
        active_applications = filtered_df[filtered_df['jobpage_status'] == 'Active'].shape[0]
        inactive_applications = filtered_df[filtered_df['jobpage_status'] == 'Inactive'].shape[0]

        suffix = "Users" if data_source == 'latest_unique' else "CVs"

        def generate_bar_line_graph(df_pivot, x_col, title, x_title):
            fig = go.Figure()
            fig.add_trace(
                go.Bar(x=df_pivot[x_col], y=df_pivot['Inactive'], name='Inactive', marker_color='#8B4513', opacity=0.9))
            fig.add_trace(
                go.Bar(x=df_pivot[x_col], y=df_pivot['Active'], name='Active', marker_color='#191970', opacity=0.9))

            if 'Active_Percent' in df_pivot.columns and not df_pivot['Active_Percent'].isnull().all():
                fig.add_trace(go.Scatter(
                    x=df_pivot[x_col], y=df_pivot['Active_Percent'], name='Active%', mode='lines+markers+text',
                    yaxis='y2',
                    line=dict(color='#3CB371', width=3), marker=dict(size=8),
                    text=[f"{p:.0f}%" for p in df_pivot['Active_Percent']], textposition="top center",
                    textfont=dict(color='#3CB371')
                ))

            fig.update_layout(
                title=title,
                barmode='group',
                xaxis=dict(title=x_title),
                yaxis=dict(title=f'{suffix} Count (Active/Inactive)', title_font=dict(color='#191970'), tickformat='.0f',
                           side='left',
                           showgrid=True, gridcolor='#e0e0e0'),
                yaxis2=dict(title='Active %', title_font=dict(color='#3CB371'), overlaying='y', side='right',
                            range=[0, 100],
                            tickformat='.0f', showgrid=False),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(t=50, b=50, l=50, r=50),
                height=700,
                xaxis_tickfont_size=10,
            )

            # For location graph specifically, rotate x-axis labels for better readability
            if x_col == 'applicant_location':
                fig.update_layout(
                    xaxis_tickangle=-45,
                    margin=dict(b=120)
                )

            return fig

        total_card = create_summary_card(f"Total {suffix}", total_applications, "primary")
        active_card = create_summary_card(f"Active {suffix}", active_applications, "success")
        inactive_card = create_summary_card(f"Inactive {suffix}", inactive_applications, "warning")

        # Graph Aggregation
        location_counts = filtered_df.groupby(['applicant_location', 'jobpage_status']).size().reset_index(name='count')
        location_pivot = location_counts.pivot(index='applicant_location', columns='jobpage_status', values='count').fillna(
            0)

        # Ensure columns exist
        if 'Active' not in location_pivot.columns: location_pivot['Active'] = 0
        if 'Inactive' not in location_pivot.columns: location_pivot['Inactive'] = 0

        location_pivot['Total'] = location_pivot['Active'] + location_pivot['Inactive']

        # Safe division
        location_pivot['Active_Percent'] = location_pivot.apply(
            lambda row: (row['Active'] / row['Total'] * 100) if row['Total'] > 0 else 0, axis=1
        )

        location_pivot.reset_index(inplace=True)

        # Graph Generation
        fig = generate_bar_line_graph(location_pivot, 'applicant_location', f'{suffix} by Applicant Location', 'Location')

        return fig, total_card, active_card, inactive_card