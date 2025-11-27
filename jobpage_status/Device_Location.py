# job_portal_dashboard/Location_Device.py

import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc, callback, Input, Output, no_update
import dash_bootstrap_components as dbc
from datetime import datetime

# --- Filter Options ---
# Initialized as None/Empty, populated by callback
COUNTRY_OPTIONS = []
MIN_DATE = None
MAX_DATE = None


# --- Helper Functions ---
def create_summary_card(title, value, color_class="primary"):
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-title", style={'opacity': '0.9', 'color': 'white'}),
            html.H2(f"{value:}", className="card-text",style={'fontWeight': 'bold', 'color': 'white'}),
        ]),
        color=color_class, inverse=True, className=f"mb-4 shadow-sm {color_class}"
)


# --- Page Layout ---
layout = dbc.Container([
    html.H2("Page 8: Total CV Count by Location", className="text-center my-4", style={'color': '#2c3e50'}),

    # Filters Section
    dbc.Row([
        # 1. Date Range (Width changed to 4)
        dbc.Col([html.Label("Select Date Range:", style={'fontWeight': 'bold'}),
                 dcc.DatePickerRange(id='p8-date-range-picker',
                                     display_format='YYYY-MM-DD')],
                width=12, md=4),

        # 2. Country Filter (Width changed to 4)
        dbc.Col([html.Label("Select Applicant Location:", style={'fontWeight': 'bold'}),
                 dcc.Dropdown(id='p8-country-filter',
                              multi=True,
                              placeholder="Select one or more locations...")
                 ],
                width=12, md=4),

        # 3. NEW: Applicant Status Filter (Width 4)
        dbc.Col([html.Label("Filter by Status:", style={'fontWeight': 'bold'}),
                 dcc.Dropdown(id='p8-status-filter',
                              value=[],
                              multi=True,
                              placeholder="Select status...")],
                width=12, md=4),
    ], className="mb-4"),

    # Summary Cards
    dbc.Row([
        dbc.Col(id='p8-total-applications-card', width=12, md=3),
        dbc.Col(id='p8-mobile-total-card', width=12, md=3),
        dbc.Col(id='p8-desktop-total-card', width=12, md=3),
        dbc.Col(id='p8-mobile-percentage-card', width=12, md=3),
    ], className="mb-4"),

    # Graph
    dbc.Row([
        dbc.Col(
            html.Div(
                dcc.Graph(id='p8-location-cv-graph'),
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
    """Registers all callbacks for Page 8 (Location Count Bar Chart)."""

    # 1. Callback to Initialize Filters (Triggered by Data Load)
    @app.callback(
        [Output('p8-date-range-picker', 'min_date_allowed'),
         Output('p8-date-range-picker', 'max_date_allowed'),
         Output('p8-date-range-picker', 'start_date'),
         Output('p8-date-range-picker', 'end_date'),
         Output('p8-country-filter', 'options'),
         Output('p8-status-filter', 'options')],  # Added Output for Status
        [Input('global-data-store', 'data')]
    )
    def populate_initial_filters(json_data):
        """Populates date pickers, country, and status filter options."""
        if json_data is None:
            return no_update, no_update, no_update, no_update, [], []

        df = pd.DataFrame(json_data)

        # Convert date column
        if 'application_date' in df.columns:
            df['application_date'] = pd.to_datetime(df['application_date'])

        min_date = df['application_date'].min().date()
        max_date = df['application_date'].max().date()

        country_options = [{'label': country, 'value': country} for country in
                           sorted(df['applicant_location'].unique())]

        # Status Options (NEW)
        status_options = []
        if 'application_status' in df.columns:
            unique_statuses = sorted(df['application_status'].dropna().astype(str).unique())
            status_options = [{'label': s.title(), 'value': s} for s in unique_statuses]

        return min_date, max_date, min_date, max_date, country_options, status_options

    # 2. Callback to Update Content (Triggered by Filters OR Data Load)
    @app.callback(
        [Output('p8-location-cv-graph', 'figure'),
         Output('p8-total-applications-card', 'children'),
         Output('p8-mobile-total-card', 'children'),
         Output('p8-desktop-total-card', 'children'),
         Output('p8-mobile-percentage-card', 'children')],
        [Input('p8-date-range-picker', 'start_date'),
         Input('p8-date-range-picker', 'end_date'),
         Input('p8-country-filter', 'value'),
         Input('p8-status-filter', 'value'),  # Added Input for Status
         Input('data-source-selector', 'value'),
         Input('global-data-store', 'data')]
    )
    def update_page_8_content(start_date, end_date, selected_countries, selected_statuses, data_source, json_data):

        if json_data is None:
            return no_update, no_update, no_update, no_update, no_update

        df = pd.DataFrame(json_data)

        # --- Data Cleaning ---
        if 'application_date' in df.columns:
            df['application_date'] = pd.to_datetime(df['application_date'])

        # Normalize dtype
        if 'dtype' in df.columns:
            df['dtype'] = df['dtype'].astype(str).str.lower().str.strip()

        filtered_df = df.copy()

        # Handle default dates
        if not start_date: start_date = df['application_date'].min().date()
        if not end_date: end_date = df['application_date'].max().date()

        # --- Date Filtering ---
        filtered_df = filtered_df[
            (filtered_df['application_date'] >= str(start_date)) &
            (filtered_df['application_date'] <= str(end_date))
            ]

        # --- Country Filtering ---
        if selected_countries:
            if not isinstance(selected_countries, list):
                selected_countries = [selected_countries]
            filtered_df = filtered_df[filtered_df['applicant_location'].isin(selected_countries)]

        # --- Status Filtering (NEW) ---
        if selected_statuses:
            filtered_df = filtered_df[filtered_df['application_status'].isin(selected_statuses)]

        # --- Handle Empty Data ---
        if filtered_df.empty:
            empty_fig = go.Figure().update_layout(title="No data available for the selected filters.")
            zero_card = create_summary_card("Mobile %", "0.00%", "secondary")
            return empty_fig, \
                create_summary_card("Total Applications", 0, "primary"), \
                create_summary_card("Mobile CVs", 0, "warning"), \
                create_summary_card("Desktop CVs", 0, "info"), \
                zero_card

        # --- Summary Cards ---
        total_applications = filtered_df.shape[0]
        mobile_count = filtered_df[filtered_df['dtype'] == 'mobile'].shape[0]
        desktop_count = filtered_df[filtered_df['dtype'] == 'desktop'].shape[0]

        mobile_percentage = (mobile_count / total_applications) * 100 if total_applications > 0 else 0.0

        suffix = "Users" if data_source == 'latest_unique' else "CVs"

        def generate_location_bar_chart(df_pivot, x_col, title, x_title):
            """Generates a Bar Chart showing Total CV Count per Location (Mobile vs Desktop split)
               AND adds a Scatter trace for Mobile Users with visible text labels."""
            fig = go.Figure()

            # Bar Trace 1: Mobile Count (Yellow/Orange)
            if 'mobile' in df_pivot.columns:
                fig.add_trace(
                    go.Bar(x=df_pivot[x_col], y=df_pivot['mobile'], name='Mobile CVs (Bar)', marker_color='#FFC300',
                           opacity=0.9))

            # Bar Trace 2: Desktop Count (Dark Blue)
            if 'desktop' in df_pivot.columns:
                fig.add_trace(
                    go.Bar(x=df_pivot[x_col], y=df_pivot['desktop'], name='Desktop CVs (Bar)', marker_color='#191970',
                           opacity=0.9))

            # --- NEW TRACE: Scatter for Mobile Percentage on Secondary Y-Axis with Labels ---
            if 'mobile_percentage' in df_pivot.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df_pivot[x_col],
                        y=df_pivot['mobile_percentage'],
                        name='Mobile % (Trend)',
                        mode='lines+markers+text',  # Added +text
                        marker=dict(color='#FF5733', size=8),
                        line=dict(color='#FF5733', width=2),
                        opacity=0.7,
                        yaxis='y2',
                        text=[f"{p:.0f}%" for p in df_pivot['mobile_percentage']],
                        textposition="top center"
                    )
                )

            fig.update_layout(
                title=title,
                barmode='group',
                xaxis=dict(title=x_title),
                # Primary Y-axis (Counts)
                yaxis=dict(title=f'Total {suffix} Count', title_font=dict(color='#191970'), tickformat='.0f',
                           side='left',
                           showgrid=True, gridcolor='#e0e0e0', rangemode='tozero'),
                # Secondary Y-axis (Percentage)
                yaxis2=dict(
                    title=f'Mobile {suffix} Percentage (%)',
                    title_font=dict(color='#FF5733'),
                    overlaying='y',
                    side='right',
                    showgrid=False,
                    tickformat=".0f",
                    range=[0, 110]  # Slightly higher range for text labels
                ),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                plot_bgcolor='white', paper_bgcolor='white',
                margin=dict(t=50, b=120, l=50, r=50),
                xaxis_tickangle=-45,
            )
            return fig

        total_card = create_summary_card(f"Total {suffix}", total_applications, "primary")
        mobile_card = create_summary_card(f"Mobile {suffix}", mobile_count, "warning")
        desktop_card = create_summary_card(f"Desktop {suffix}", desktop_count, "info")
        mobile_percent_card = create_summary_card("Mobile %", f"{mobile_percentage:.2f}%", "secondary")

        # --- Graph Aggregation ---
        location_device_counts = filtered_df.groupby(['applicant_location', 'dtype']).size().reset_index(
            name='Total_Count')

        location_pivot = location_device_counts.pivot_table(
            index='applicant_location',
            columns='dtype',
            values='Total_Count',
            fill_value=0
        ).reset_index()

        # Ensure columns exist
        if 'mobile' not in location_pivot.columns: location_pivot['mobile'] = 0
        if 'desktop' not in location_pivot.columns: location_pivot['desktop'] = 0

        # Calculate percentage for the new trace
        location_pivot['Total_Count'] = location_pivot['mobile'] + location_pivot['desktop']

        location_pivot['mobile_percentage'] = location_pivot.apply(
            lambda row: (row['mobile'] / row['Total_Count'] * 100) if row['Total_Count'] > 0 else 0, axis=1
        )

        location_pivot.sort_values('Total_Count', ascending=False, inplace=True)

        # Graph Generation
        fig = generate_location_bar_chart(location_pivot, 'applicant_location',
                                          f'{suffix} Count by Location (Mobile vs Desktop) with Mobile % Trend',
                                          'Country/Location')

        return fig, total_card, mobile_card, desktop_card, mobile_percent_card