# job_portal_dashboard/Daily_Overview.py

import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc, callback, Input, Output, no_update
import dash_bootstrap_components as dbc


# Helper functions (Unchanged)
def create_summary_card(title, value, color):
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-title"),
            html.H2(f"{value:,}", className="card-text"),
        ]),
        color=color, inverse=True, className="text-center shadow-sm mb-3"
)

# Page layout: Options are empty placeholders, filled by callback
layout = dbc.Container([
    html.H2("Page 1: Daily Application Overview", className="text-center my-4", style={'color': '#2c3e50'}),

    # Filters Section
    dbc.Row([
        dbc.Col([html.Label("Select Months:", style={'fontWeight': 'bold'}),
                 dcc.Dropdown(id='p1-month-filter', value=[], multi=True, placeholder="Select months...")],
                width=12, md=4),
        dbc.Col([html.Label("Select Country:", style={'fontWeight': 'bold'}),
                 dcc.Dropdown(id='p1-country-filter', value=[], multi=True, placeholder="Select countries...")],
                width=12, md=4),
        dbc.Col([html.Label("Select Job Title:", style={'fontWeight': 'bold'}),
                 dcc.Dropdown(id='p1-job-title-filter', value='all', clearable=False)],
                width=12, md=4)
    ], className="mb-4"),

    # Summary Cards
    dbc.Row([
        dbc.Col(id='p1-total-applications-card', width=12, md=4),
        dbc.Col(id='p1-active-applications-card', width=12, md=4),
        dbc.Col(id='p1-inactive-applications-card', width=12, md=4),
    ], className="mb-4"),

    # Graph
    dbc.Row([dbc.Col(dcc.Graph(id='p1-daily-cv-graph'), width=12)])
])


# --- MODIFIED Callback Registration ---
# REMOVED 'df_passed' argument. It now only takes 'app'.
def register_callbacks(app):
    @app.callback(
        [Output('p1-daily-cv-graph', 'figure'),
         Output('p1-total-applications-card', 'children'),
         Output('p1-active-applications-card', 'children'),
         Output('p1-inactive-applications-card', 'children'),
         Output('p1-month-filter', 'options'),
         Output('p1-country-filter', 'options'),
         Output('p1-job-title-filter', 'options')],
        [Input('p1-month-filter', 'value'),
         Input('p1-country-filter', 'value'),
         Input('p1-job-title-filter', 'value'),
         Input('data-source-selector', 'value'),
         Input('global-data-store', 'data')]  # <--- NEW INPUT: The Data Store
    )

    def update_page_1(selected_months, selected_countries, selected_job_title,data_source, json_data):

        # 1. Handle Initial Load (Data might be None)
        if json_data is None:
            # Return no updates or empty placeholders
            return no_update, no_update, no_update, no_update, [], [], []

        # 2. Deserialize Data
        df = pd.DataFrame(json_data)

        # 3. Calculate Options (Dynamically based on loaded data)
        month_map = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
                     7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}

        # Ensure 'month' column exists (if it was lost in serialization, recreate it from date)
        if 'month' not in df.columns and 'application_date' in df.columns:
            df['application_date'] = pd.to_datetime(df['application_date'])
            df['month'] = df['application_date'].dt.month

        initial_months = sorted(df['month'].unique())
        initial_countries = sorted(df['applicant_location'].unique())
        job_titles_clean = [title for title in df['job_title'].unique() if pd.notna(title)]

        month_options = [{'label': month_map.get(m, str(m)), 'value': m} for m in initial_months]
        country_options = [{'label': country, 'value': country} for country in initial_countries]
        job_title_options = [{'label': 'All Jobs', 'value': 'all'}] + \
                            [{'label': str(t), 'value': t} for t in sorted(job_titles_clean)]

        # 4. Apply Filters
        filtered_df = df.copy()

        if selected_months:
            filtered_df = filtered_df[filtered_df['month'].isin(selected_months)]
        if selected_countries:
            filtered_df = filtered_df[filtered_df['applicant_location'].isin(selected_countries)]
        if selected_job_title and selected_job_title != 'all':
            filtered_df = filtered_df[filtered_df['job_title'] == selected_job_title]

        # 5. Handle Empty Filtered Data
        if filtered_df.empty:
            empty_fig = go.Figure().update_layout(title="No data available for the selected filters.")
            return (empty_fig,
                    create_summary_card("Total Applications", 0, "primary"),
                    create_summary_card("Active CVs", 0, "success"),
                    create_summary_card("Inactive CVs", 0, "warning"),
                    month_options, country_options, job_title_options)

        suffix = "user" if data_source == 'latest_unique' else "cv"

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
                title=title, barmode='group', xaxis=dict(title=x_title),
                yaxis=dict(title=f'{suffix} Count (Active/Inactive)', title_font=dict(color='#191970'),
                           tickformat='.0f', side='left',
                           showgrid=True, gridcolor='#e0e0e0'),
                yaxis2=dict(title='Active %', title_font=dict(color='#3CB371'), overlaying='y', side='right',
                            range=[0, 100],
                            tickformat='.0f', showgrid=False),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                plot_bgcolor='white', paper_bgcolor='white', margin=dict(t=50, b=50, l=50, r=50)
            )
            if x_col == 'day_of_month':
                fig.update_layout(xaxis=dict(tickmode='linear', dtick=1, tick0=1, range=[0.5, 31.5]))
            return fig

        # 6. Summary Cards Logic
        total_applications = filtered_df.shape[0]
        active_applications = filtered_df[filtered_df['jobpage_status'] == 'Active'].shape[0]
        inactive_applications = filtered_df[filtered_df['jobpage_status'] == 'Inactive'].shape[0]

        total_card = create_summary_card(f"Total {suffix}", total_applications, "primary")
        active_card = create_summary_card(f"Active {suffix}", active_applications, "success")
        inactive_card = create_summary_card(f"Inactive {suffix}", inactive_applications, "warning")

        # 7. Graph Logic
        daily_counts = filtered_df.groupby(['day_of_month', 'jobpage_status']).size().reset_index(name='count')
        daily_pivot = daily_counts.pivot(index='day_of_month', columns='jobpage_status', values='count').fillna(0)

        if 'Active' in daily_pivot.columns and 'Inactive' in daily_pivot.columns:
            daily_pivot['Total'] = daily_pivot['Active'] + daily_pivot['Inactive']
            daily_pivot['Active_Percent'] = (daily_pivot['Active'] / daily_pivot['Total']) * 100
        else:
            daily_pivot['Total'] = daily_pivot.get('Active', 0) + daily_pivot.get('Inactive', 0)
            daily_pivot['Active_Percent'] = 0.0

        daily_pivot.reset_index(inplace=True)

        fig = generate_bar_line_graph(daily_pivot, 'day_of_month', f'Daily {suffix}: Active vs. Inactive Users',
                                      'Day of Month')

        # 8. Return everything
        return fig, total_card, active_card, inactive_card, month_options, country_options, job_title_options