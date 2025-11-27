# job_portal_dashboard/Monthly_Trend.py

import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc, callback, Input, Output, no_update
import dash_bootstrap_components as dbc


# --- 1. Helper Functions ---

def create_summary_card(title, value, color_class="primary"):
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-title", style={'opacity': '0.9', 'color': 'white'}),
            html.H2(f"{value:,}", className="card-text",style={'fontWeight': 'bold', 'color': 'white'}),
        ]),
        color=color_class, inverse=True, className=f"mb-4 shadow-sm {color_class}"
)

# --- 2. Layout ---
layout = dbc.Container([
    html.H2("Page 2: Monthly Trend Analysis", className="text-center my-4", style={'color': '#2c3e50'}),
    dbc.Row([
        dbc.Col([html.Label("Select Date Range:", className="control-label"),
                 dcc.DatePickerRange(id='p2-date-range-picker', display_format='YYYY-MM-DD')], width=6),
        dbc.Col([html.Label("Select Country:", className="control-label"),
                 dcc.Dropdown(id='p2-country-filter', multi=True)], width=6)
    ], className="mb-4 glass-container"),
    dbc.Row([
        dbc.Col(id='p2-total-applications-card', width=4),
        dbc.Col(id='p2-active-applications-card', width=4),
        dbc.Col(id='p2-inactive-applications-card', width=4),
    ], className="mb-4"),
    dbc.Row([dbc.Col(dcc.Graph(id='p2-monthly-cv-graph'), width=12)])
])


# --- 3. Callback Registration ---
def register_callbacks(app):
    @app.callback(
        [Output('p2-monthly-cv-graph', 'figure'),
         Output('p2-total-applications-card', 'children'),
         Output('p2-active-applications-card', 'children'),
         Output('p2-inactive-applications-card', 'children'),
         Output('p2-date-range-picker', 'min_date_allowed'),
         Output('p2-date-range-picker', 'max_date_allowed'),
         Output('p2-country-filter', 'options')],
        [Input('p2-date-range-picker', 'start_date'),
         Input('p2-date-range-picker', 'end_date'),
         Input('p2-country-filter', 'value'),
         Input('data-source-selector', 'value'),
         Input('global-data-store', 'data')]
    )
    def update_page_2(start_date, end_date, selected_countries,data_source, json_data):

        suffix = "user" if data_source == 'latest_unique' else "cv"

        # 1. Check Data
        if json_data is None:
            return no_update, no_update, no_update, no_update, no_update, no_update, []

        # 2. Load Data
        df = pd.DataFrame(json_data)

        # 3. Calculate Options
        min_date = df['application_date'].min()
        max_date = df['application_date'].max()
        country_options = [{'label': c, 'value': c} for c in sorted(df['applicant_location'].unique())]

        # 4. Handle Defaults
        if not start_date: start_date = min_date
        if not end_date: end_date = max_date

        # 5. Filter
        filtered_df = df.copy()
        filtered_df = filtered_df[
            (filtered_df['application_date'] >= str(start_date)) &
            (filtered_df['application_date'] <= str(end_date))
            ]
        if selected_countries:
            filtered_df = filtered_df[filtered_df['applicant_location'].isin(selected_countries)]

        # 6. Handle Empty
        if filtered_df.empty:
            return go.Figure(), create_summary_card("Total", 0, "primary"), \
                create_summary_card(f"Active ", 0, "success"), \
                create_summary_card("Inactive", 0, "warning"), \
                min_date, max_date, country_options

        def generate_bar_line_graph(df_pivot, x_col, title, x_title):
            fig = go.Figure()

            # 1. Add Bar Traces (Primary Y-Axis)
            fig.add_trace(
                go.Bar(x=df_pivot[x_col], y=df_pivot['Inactive'], name='Inactive', marker_color='#8B4513', opacity=0.9))
            fig.add_trace(
                go.Bar(x=df_pivot[x_col], y=df_pivot['Active'], name='Active', marker_color='#191970', opacity=0.9))

            # 2. Add Scatter Trace (Secondary Y-Axis) - THIS WAS MISSING
            if 'Active_Percent' in df_pivot.columns:
                fig.add_trace(go.Scatter(
                    x=df_pivot[x_col],
                    y=df_pivot['Active_Percent'],
                    name='Active %',
                    mode='lines+markers+text',
                    yaxis='y2',  # Important: Map to secondary axis
                    line=dict(color='#3CB371', width=3),
                    marker=dict(size=8),
                    text=[f"{p:.0f}%" for p in df_pivot['Active_Percent']],
                    textposition="top center",
                    textfont=dict(color='#3CB371')
                ))

            # 3. Update Layout for Dual Axis
            fig.update_layout(
                title=title,
                barmode='group',
                xaxis=dict(title=x_title),
                # Primary Y-Axis (Counts)
                yaxis=dict(
                    title=f'{suffix} Count',
                    title_font=dict(color='#191970'),
                    tickformat='.0f',
                    side='left',
                    showgrid=True,
                    gridcolor='#e0e0e0'
                ),
                # Secondary Y-Axis (Percentage)
                yaxis2=dict(
                    title='Active %',
                    title_font=dict(color='#3CB371'),
                    overlaying='y',
                    side='right',
                    range=[0, 110],  # Slightly >100 to fit labels
                    tickformat='.0f',
                    showgrid=False
                ),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                plot_bgcolor='white', paper_bgcolor='white', margin=dict(t=50, b=50, l=50, r=50)
            )
            return fig


        # 7. Cards Data
        total = len(filtered_df)
        active = len(filtered_df[filtered_df['jobpage_status'] == 'Active'])
        inactive = len(filtered_df[filtered_df['jobpage_status'] == 'Inactive'])

        # 8. Graph Data Preparation
        monthly_counts = filtered_df.groupby(['year_month', 'jobpage_status']).size().reset_index(name='count')
        monthly_pivot = monthly_counts.pivot(index='year_month', columns='jobpage_status', values='count').fillna(0)

        # Ensure columns exist
        if 'Active' not in monthly_pivot: monthly_pivot['Active'] = 0
        if 'Inactive' not in monthly_pivot: monthly_pivot['Inactive'] = 0

        # --- CALCULATE PERCENTAGE HERE ---
        monthly_pivot['Total'] = monthly_pivot['Active'] + monthly_pivot['Inactive']

        # Avoid division by zero
        monthly_pivot['Active_Percent'] = monthly_pivot.apply(
            lambda row: (row['Active'] / row['Total'] * 100) if row['Total'] > 0 else 0, axis=1
        )

        monthly_pivot.reset_index(inplace=True)

        # 9. Generate Graph
        fig = generate_bar_line_graph(monthly_pivot, 'year_month', f'{suffix} Monthly Trend', 'Month')

        return fig, create_summary_card(f"Total {suffix}", total, "primary"), \
            create_summary_card(f"Active {suffix}", active, "success"), \
            create_summary_card(f"Inactive {suffix}", inactive, "warning"), \
            min_date, max_date, country_options