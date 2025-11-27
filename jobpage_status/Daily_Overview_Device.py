# job_portal_dashboard/Device_Overview.py

import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc, callback, Input, Output, no_update
import dash_bootstrap_components as dbc
from datetime import datetime

# --- Filter Options ---
DEVICE_TYPE_OPTIONS = [
    {'label': 'All Devices', 'value': 'all_devices'},
    {'label': 'Mobile', 'value': 'mobile'},  # Lowercase to match data
    {'label': 'Desktop', 'value': 'desktop'}  # Lowercase to match data
]


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
    html.H2("Page 6: Daily Application Overview by Device", className="text-center my-4", style={'color': '#2c3e50'}),

    # Filters Section
    dbc.Row([
        # 1. Month Filter (Width changed to 3)
        dbc.Col([html.Label("Select Months:", className="control-label"),
                 dcc.Dropdown(id='p6-month-filter', value=[], multi=True,
                              placeholder="Select months...")],
                width=12, md=3),

        # 2. Country Filter (Width changed to 3)
        dbc.Col([html.Label("Select Country:", className="control-label"),
                 dcc.Dropdown(id='p6-country-filter', value=[], multi=True,
                              placeholder="Select countries...")],
                width=12, md=3),

        # 3. Device Filter (Width changed to 3)
        dbc.Col([html.Label("Filter by Device Type:", className="control-label"),
                 dcc.Dropdown(id='p6-device-filter', options=DEVICE_TYPE_OPTIONS, value='all_devices',
                              clearable=False)],
                width=12, md=3),

        # 4. NEW: Applicant Status Filter (Width 3)
        dbc.Col([html.Label("Filter by Status:", className="control-label"),
                 dcc.Dropdown(id='p6-status-filter',
                              value=[],
                              multi=True,
                              placeholder="Select status...")],
                width=12, md=3),

    ], className="mb-4 glass-container"),

    # Summary Cards
    dbc.Row([
        dbc.Col(id='p6-total-applications-card', width=12, md=3),
        dbc.Col(id='p6-mobile-total-card', width=12, md=3),
        dbc.Col(id='p6-desktop-total-card', width=12, md=3),
        dbc.Col(id='p6-mobile-percentage-card', width=12, md=3),
    ], className="mb-4"),

    # Graph

        html.Div([
        # Optional: Add a Title inside the glass box

        # The Graph
        dcc.Graph(id='p6-daily-device-cv-graph', style={'height': '500px', 'width':'12'})

    ], className="glass-container")

    #dbc.Row([dbc.Col(dcc.Graph(id='p6-daily-device-cv-graph'), width=12)])
])


# --- MODIFIED Callback Registration ---
def register_callbacks(app):
    """Registers all callbacks for Page 6 (Daily Device Overview)."""

    # 1. Callback to Initialize Filters (Triggered by Data Load)
    @app.callback(
        [Output('p6-month-filter', 'options'),
         Output('p6-country-filter', 'options'),
         Output('p6-status-filter', 'options')],  # Added Output for Status
        [Input('global-data-store', 'data')]
    )
    def populate_initial_filters(json_data):
        """Populates initial filter options based on the DataFrame."""
        if json_data is None:
            return [], [], []

        df = pd.DataFrame(json_data)

        # Ensure 'month' column exists
        if 'month' not in df.columns and 'application_date' in df.columns:
            df['application_date'] = pd.to_datetime(df['application_date'])
            df['month'] = df['application_date'].dt.month

        month_map = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
                     7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}

        month_opts = [{'label': month_map.get(m, f"Month {m}"), 'value': m} for m in sorted(df['month'].unique())]
        country_opts = [{'label': country, 'value': country} for country in sorted(df['applicant_location'].unique())]

        # Status Options (NEW)
        status_opts = []
        if 'application_status' in df.columns:
            unique_statuses = sorted(df['application_status'].dropna().astype(str).unique())
            status_opts = [{'label': s.title(), 'value': s} for s in unique_statuses]

        return month_opts, country_opts, status_opts

    # 2. Callback to Update Content (Triggered by Filters OR Data Load)
    @app.callback(
        [Output('p6-daily-device-cv-graph', 'figure'),
         Output('p6-total-applications-card', 'children'),
         Output('p6-mobile-total-card', 'children'),
         Output('p6-desktop-total-card', 'children'),
         Output('p6-mobile-percentage-card', 'children')],
        [Input('p6-month-filter', 'value'),
         Input('p6-country-filter', 'value'),
         Input('p6-device-filter', 'value'),
         Input('p6-status-filter', 'value'),  # Added Input for Status
         Input('data-source-selector', 'value'),
         Input('global-data-store', 'data')]
    )
    def update_page_6_content(selected_months, selected_countries, selected_device, selected_statuses, data_source,
                              json_data):

        if json_data is None:
            return no_update, no_update, no_update, no_update, no_update

        df = pd.DataFrame(json_data)
        filtered_df = df.copy()

        # Ensure 'dtype' is lowercase for consistent filtering
        if 'dtype' in filtered_df.columns:
            filtered_df['dtype'] = filtered_df['dtype'].astype(str).str.lower().str.strip()
        else:
            # Handle missing column
            empty_fig = go.Figure().update_layout(title="Data Error: 'dtype' column missing.")
            return empty_fig, \
                create_summary_card("Total", 0, "primary"), \
                create_summary_card("Mobile", 0, "warning"), \
                create_summary_card("Desktop", 0, "info"), \
                create_summary_card("Mobile %", "N/A", "secondary")

        # --- Apply Filters ---
        if selected_months:
            filtered_df = filtered_df[filtered_df['month'].isin(selected_months)]

        if selected_countries:
            filtered_df = filtered_df[filtered_df['applicant_location'].isin(selected_countries)]

        # Status Filtering (NEW)
        if selected_statuses:
            filtered_df = filtered_df[filtered_df['application_status'].isin(selected_statuses)]

        if selected_device != 'all_devices':
            filtered_df = filtered_df[filtered_df['dtype'] == selected_device]

        # --- Handle Empty Data ---
        if filtered_df.empty:
            empty_fig = go.Figure().update_layout(title="No data available for the selected filters.")
            return empty_fig, \
                create_summary_card("Total Applications", 0, "primary"), \
                create_summary_card("Mobile CVs", 0, "warning"), \
                create_summary_card("Desktop CVs", 0, "info"), \
                create_summary_card("Mobile %", "0.00%", "secondary")

        # --- Summary Cards Calculations ---
        total_applications = filtered_df.shape[0]
        mobile_count = filtered_df[filtered_df['dtype'] == 'mobile'].shape[0]
        desktop_count = filtered_df[filtered_df['dtype'] == 'desktop'].shape[0]

        suffix = "Users" if data_source == 'latest_unique' else "CVs"

        total_card = create_summary_card(f"Total {suffix}", total_applications, "primary")
        mobile_card = create_summary_card(f"Mobile {suffix}", mobile_count, "warning")
        desktop_card = create_summary_card(f"Desktop {suffix}", desktop_count, "info")

        mobile_percentage = (mobile_count / total_applications) * 100 if total_applications > 0 else 0.0
        mobile_perc_card = create_summary_card("Mobile %", f"{mobile_percentage:.2f}%", "secondary")

        # --- Graph Aggregation ---
        def generate_device_bar_line_graph(df_pivot, x_col, title, x_title):
            """Generates a combined Bar and Line graph for daily Mobile vs Desktop counts."""
            fig = go.Figure()

            # Bar Traces for Mobile vs Desktop counts
            if 'desktop' in df_pivot.columns:
                fig.add_trace(
                    go.Bar(x=df_pivot[x_col], y=df_pivot['desktop'], name='Desktop', marker_color='#191970',
                           opacity=0.9))
            if 'mobile' in df_pivot.columns:
                fig.add_trace(
                    go.Bar(x=df_pivot[x_col], y=df_pivot['mobile'], name='Mobile', marker_color='#FF8C00', opacity=0.9))

            # Line Trace for Mobile Percentage (if available)
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
                           showgrid=True, gridcolor='#e0e0e0', rangemode='tozero'),
                yaxis2=dict(title='Mobile %', title_font=dict(color='#3CB371'), overlaying='y', side='right',
                            range=[0, 100],
                            tickformat='.0f', showgrid=False),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                plot_bgcolor='white', paper_bgcolor='white', margin=dict(t=50, b=50, l=50, r=50)
            )

            # Set linear ticks for Day of Month
            if x_col == 'day_of_month':
                fig.update_layout(xaxis=dict(tickmode='linear', dtick=1, tick0=1, range=[0.5, 31.5]))

            return fig

        # 1. Group by Day and Device Type
        daily_summary = filtered_df.groupby(['day_of_month', 'dtype']).size().reset_index(name='Total_Count')

        # 2. Pivot to get Mobile/Desktop counts per day
        daily_pivot_device = daily_summary.pivot_table(
            index='day_of_month',
            columns='dtype',
            values='Total_Count',
            fill_value=0
        ).reset_index()

        # Ensure 'mobile' and 'desktop' columns exist
        if 'mobile' not in daily_pivot_device.columns: daily_pivot_device['mobile'] = 0
        if 'desktop' not in daily_pivot_device.columns: daily_pivot_device['desktop'] = 0

        # 3. Calculate Totals and Mobile Percentage
        daily_pivot_device['Total'] = daily_pivot_device['mobile'] + daily_pivot_device['desktop']

        daily_pivot_device['Mobile_Percent'] = daily_pivot_device.apply(
            lambda row: (row['mobile'] / row['Total'] * 100) if row['Total'] > 0 else 0, axis=1
        )

        # --- Final Pivot for Graph ---
        if selected_device == 'all_devices':
            final_daily_pivot = daily_pivot_device
        else:
            device_name = selected_device

            final_daily_pivot = pd.DataFrame({
                'day_of_month': daily_pivot_device['day_of_month'],
                'mobile': daily_pivot_device[device_name] if device_name == 'mobile' else 0,
                'desktop': daily_pivot_device[device_name] if device_name == 'desktop' else 0,
                'Mobile_Percent': 0  # No line for single selection
            })

        # --- Graph Generation ---
        fig = generate_device_bar_line_graph(final_daily_pivot, 'day_of_month',
                                             f'Daily {suffix} Count by Device ({selected_device})',
                                             'Day of Month')

        return fig, total_card, mobile_card, desktop_card, mobile_perc_card