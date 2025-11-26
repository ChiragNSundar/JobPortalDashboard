# job_portal_dashboard/Monthly_Overview.py

import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc, callback, Input, Output, no_update
import dash_bootstrap_components as dbc
from datetime import datetime


# --- Helper Functions ---
def create_summary_card(title, value, color):
    """Creates a styled summary card."""
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-title"),
            html.H2(f"{value}", className="card-text"),
        ]),
        color=color, inverse=True, className="text-center shadow-sm mb-3"
    )

# --- Page Layout ---
layout = dbc.Container([
    html.H2("Page 7: Monthly Trend by Device", className="text-center my-4", style={'color': '#2c3e50'}),

    # Filters Section
    dbc.Row([
        dbc.Col([html.Label("Select Date Range:", style={'fontWeight': 'bold'}),
                 dcc.DatePickerRange(id='p7-date-range-picker',
                                     display_format='YYYY-MM-DD')],
                width=12, md=6),
        dbc.Col([html.Label("Select Country:", style={'fontWeight': 'bold'}),
                 dcc.Dropdown(id='p7-country-filter', value=[], multi=True,
                              placeholder="Select countries...")],
                width=12, md=6)
    ], className="mb-4"),

    # Summary Cards
    dbc.Row([
        dbc.Col(id='p7-total-applications-card', width=12, md=3),
        dbc.Col(id='p7-mobile-total-card', width=12, md=3),
        dbc.Col(id='p7-desktop-total-card', width=12, md=3),
        dbc.Col(id='p7-mobile-percentage-card', width=12, md=3),
    ], className="mb-4"),

    # Graph
    dbc.Row([dbc.Col(dcc.Graph(id='p7-monthly-device-cv-graph'), width=12)])
])


# --- MODIFIED Callback Registration ---
def register_callbacks(app):
    """Registers all callbacks for Page 8 (Monthly Device Trend)."""

    # 1. Callback to Initialize Filters (Triggered by Data Load)
    @app.callback(
        [Output('p7-date-range-picker', 'min_date_allowed'),
         Output('p7-date-range-picker', 'max_date_allowed'),
         Output('p7-date-range-picker', 'start_date'),
         Output('p7-date-range-picker', 'end_date'),
         Output('p7-country-filter', 'options')],
        [Input('global-data-store', 'data')]  # Listen to Store
    )
    def populate_initial_filters(json_data):
        """Populates date pickers and country filter options based on the DataFrame."""
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
        [Output('p7-monthly-device-cv-graph', 'figure'),
         Output('p7-total-applications-card', 'children'),
         Output('p7-mobile-total-card', 'children'),
         Output('p7-desktop-total-card', 'children'),
         Output('p7-mobile-percentage-card', 'children')],
        [Input('p7-date-range-picker', 'start_date'),
         Input('p7-date-range-picker', 'end_date'),
         Input('p7-country-filter', 'value'),
         Input('data-source-selector', 'value'),
         Input('global-data-store', 'data')]  # Add Store as Input
    )
    def update_page_7(start_date, end_date, selected_countries,data_source, json_data):

        if json_data is None:
            return no_update, no_update, no_update, no_update, no_update

        df = pd.DataFrame(json_data)

        # --- Data Cleaning ---
        if 'application_date' in df.columns:
            df['application_date'] = pd.to_datetime(df['application_date'])

        # Ensure 'dtype' is lowercase for consistent filtering/aggregation
        if 'dtype' in df.columns:
            df['dtype'] = df['dtype'].astype(str).str.lower().str.strip()

        filtered_df = df.copy()

        # Handle default dates if inputs are None
        if not start_date: start_date = df['application_date'].min().date()
        if not end_date: end_date = df['application_date'].max().date()

        # Apply Filters
        filtered_df = filtered_df[
            (filtered_df['application_date'] >= str(start_date)) &
            (filtered_df['application_date'] <= str(end_date))
            ]

        if selected_countries:
            filtered_df = filtered_df[filtered_df['applicant_location'].isin(selected_countries)]

        # Handle Empty Data
        if filtered_df.empty:
            empty_fig = go.Figure().update_layout(title="No data available for the selected filters.")
            return empty_fig, \
                create_summary_card("Total Applications", 0, "primary"), \
                create_summary_card("Mobile CVs", 0, "warning"), \
                create_summary_card("Desktop CVs", 0, "info"), \
                create_summary_card("Mobile %", "0.00%", "secondary")

        # Summary Cards
        total_applications = filtered_df.shape[0]
        mobile_count = filtered_df[filtered_df['dtype'] == 'mobile'].shape[0]
        desktop_count = filtered_df[filtered_df['dtype'] == 'desktop'].shape[0]

        suffix = "Users" if data_source == 'latest_unique' else "CVs"

        def generate_device_monthly_graph(df_pivot, x_col, title, x_title):
            """Generates a combined Bar and Line graph for monthly Mobile vs Desktop counts."""
            fig = go.Figure()

            # Bar Traces: Mobile and Desktop counts (using lowercase names from aggregation)
            if 'desktop' in df_pivot.columns:
                fig.add_trace(
                    go.Bar(x=df_pivot[x_col], y=df_pivot['desktop'], name='Desktop', marker_color='#191970',
                           opacity=0.9))
            if 'mobile' in df_pivot.columns:
                fig.add_trace(
                    go.Bar(x=df_pivot[x_col], y=df_pivot['mobile'], name='Mobile', marker_color='#FF8C00', opacity=0.9))

            # Line Trace: Mobile Percentage of Total
            if 'Mobile_Percent' in df_pivot.columns and not df_pivot['Mobile_Percent'].isnull().all():
                fig.add_trace(go.Scatter(
                    x=df_pivot[x_col], y=df_pivot['Mobile_Percent'], name='Mobile %', mode='lines+markers+text',
                    yaxis='y2',
                    line=dict(color='#3CB371', width=3), marker=dict(size=8),
                    text=[f"{p:.0f}%" for p in df_pivot['Mobile_Percent']], textposition="top center",
                    textfont=dict(color='#3CB371')
                ))

            fig.update_layout(
                title=title,
                barmode='group',
                xaxis=dict(title=x_title),
                yaxis=dict(title=f'{suffix} Count (Mobile/Desktop)', title_font=dict(color='#191970'), tickformat='.0f',
                           side='left',
                           showgrid=True, gridcolor='#e0e0e0', rangemode='tozero'),  # Ensure Y-axis starts at 0
                yaxis2=dict(title='Mobile %', title_font=dict(color='#3CB371'), overlaying='y', side='right',
                            range=[0, 100],
                            tickformat='.0f', showgrid=False),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                plot_bgcolor='white', paper_bgcolor='white', margin=dict(t=50, b=50, l=50, r=50)
            )
            return fig

        total_card = create_summary_card(f"Total {suffix}", total_applications, "primary")
        mobile_card = create_summary_card(f"Mobile {suffix}", mobile_count, "warning")
        desktop_card = create_summary_card(f"Desktop {suffix}", desktop_count, "info")

        mobile_percentage = (mobile_count / total_applications) * 100 if total_applications > 0 else 0.0
        mobile_perc_card = create_summary_card("Mobile %", f"{mobile_percentage:.2f}%", "secondary")

        # Graph Aggregation (Group by Year-Month and Device Type)
        monthly_device_counts = filtered_df.groupby(['year_month', 'dtype']).size().reset_index(name='count')

        # Pivot to get Mobile/Desktop counts per month
        monthly_pivot = monthly_device_counts.pivot_table(
            index='year_month',
            columns='dtype',
            values='count',
            fill_value=0
        ).reset_index()

        # Ensure 'mobile' and 'desktop' columns exist (lowercase)
        if 'mobile' not in monthly_pivot.columns: monthly_pivot['mobile'] = 0
        if 'desktop' not in monthly_pivot.columns: monthly_pivot['desktop'] = 0

        # Calculate Total and Mobile Percentage
        monthly_pivot['Total'] = monthly_pivot['mobile'] + monthly_pivot['desktop']

        monthly_pivot['Mobile_Percent'] = monthly_pivot.apply(
            lambda row: (row['mobile'] / row['Total'] * 100) if row['Total'] > 0 else 0, axis=1
        )

        monthly_pivot.sort_values('year_month', inplace=True)

        # Graph Generation
        fig = generate_device_monthly_graph(monthly_pivot, 'year_month', f'Monthly {suffix}: Mobile vs. Desktop {suffix}',
                                            'Month')

        return fig, total_card, mobile_card, desktop_card, mobile_perc_card