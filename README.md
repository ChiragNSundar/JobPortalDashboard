# JobPortalDashboard

#pip install -r requirements.txt


# .env file

# MongoDB Configuration
MONGO_URI=mongodburl
MONGO_DB_NAME=dbname
MONGO_COLLECTION_NAME=collectionname

# Fallback SQL Configuration (Used if Mongo fails)
SQL_HOST=
SQL_USER=
SQL_PASSWORD=
SQL_DATABASE=
SQL_TABLE_NAME=

📊 Job Portal Analytics Dashboard
A comprehensive, interactive data visualization dashboard built with Python Dash and Plotly. This application provides deep insights into job portal traffic, application trends, user device preferences, and geographical distributions, enabling data-driven decision-making.
✨ Features

📈 Advanced Trend Analysis
Daily & Monthly Overviews: Visualize application volume over time with dual-axis graphs showing counts vs. active percentages.
Status Tracking: Monitor the ratio of Active vs. Inactive CVs/Users across all timeframes.
Registration Sources: Analyze which platforms (RegSource) are driving the most traffic.

📱 Device Intelligence
Mobile vs. Desktop Breakdown: Dedicated analytics to compare user behavior across devices.
Device Trends: Track daily and monthly adoption rates of mobile usage.
Percentage Overlays: Line charts overlaying bar graphs to show the exact fluctuation in mobile user percentage over time.

🌍 Geospatial & Demographic Insights
Location Analysis: Detailed bar charts breaking down applications by country and applicant location.
Hierarchical Visualization: A Sunburst Chart (Page 4) that visualizes the relationship between Countries and Application Status (Active/Inactive) in a nested format.
Device by Location: Analyze which countries prefer mobile devices versus desktop computers.

🎛️ Interactive UI & Filtering
Glassmorphism Design: Modern UI with semi-transparent "glass" containers for a sleek look.
Dynamic Filtering: Filter data globally or per page by Date Range, Country, Device Type, Job Title, and Application Status.
Smart Summary Cards: Real-time KPI cards at the top of every page displaying Total Counts, Active/Inactive stats, and Mobile Percentages.

🛠️ Tech Stack
Framework: Dash (Python)
Visualization: Plotly Graph Objects & Plotly Express
UI Components: Dash Bootstrap Components
Data Manipulation: Pandas
State Management: Dash dcc.Store for client-side data handling.

🚀 Installation & Setup
Clone the repository:
code
Bash
git clone https://github.com/yourusername/job-portal-dashboard.git
cd job-portal-dashboard
Install Dependencies:
Ensure you have Python installed, then run:
code
Bash
pip install pandas plotly dash dash-bootstrap-components
Run the Application:
Note: These files are page modules. You likely have a main entry file (e.g., index.py or app.py) that ties them together.
code
Bash
python index.py
Open in Browser:
Go to http://127.0.0.1:8050 to view the dashboard.
📂 Project Structure
code
Text

/job_portal_dashboard
├── Daily_Overview.py           # Page 1: Daily apps & active status
├── Monthly_Trend.py            # Page 2: Monthly trend analysis
├── Location_Analysis.py        # Page 3: Applications by location
├── Pie_Chart.py                # Page 4: Sunburst chart (Country -> Status)
├── Mobile_Desktop.py           # Page 5: Pie chart & device split
├── Daily_Overview_Device.py    # Page 6: Daily trends by device
├── Monthly_Trend_Device.py     # Page 7: Monthly trends by device
├── Device_Location.py          # Page 8: Location analysis split by device
├── Registrysource_bargraph.py  # Page 9: Registration source analysis
└── ... (Main app entry point)


📊 Dashboard Pages Overview
Daily Overview: High-level daily metrics and job title filtering.
Monthly Trend: Long-term trend analysis with date range pickers.
Location Breakdown: Bar charts focusing on geographic distribution.
Country & Status: A Sunburst chart showing the hierarchy of locations and resume status.
Device Breakdown: Pie charts showing the global split between Mobile and Desktop.
Daily Device: Granular daily tracking of device usage.
Monthly Device: Long-term device usage trends.
Location & Device: Cross-referencing location data with device preference (e.g., "Which country uses mobile the most?").
Register Source: Analysis of where users are coming from.


xampp server localhost used for SQL testing,
MongoDB for localhost through compass/atlas and mongosh setup.

hello

Images:
![1_2_3_4_5_6_7_8_merged_page-0001](https://github.com/user-attachments/assets/89fe60fe-f792-45e0-b111-27c5e0b7d3e9)
![1_2_3_4_5_6_7_8_merged_page-0003](https://github.com/user-attachments/assets/438547f6-4ef9-4c5a-9802-5ed61df4c3b2)
![1_2_3_4_5_6_7_8_merged_page-0005](https://github.com/user-attachments/assets/c74a4f19-9a13-4937-aa82-bdf129b4d82d)
![1_2_3_4_5_6_7_8_merged_page-0007](https://github.com/user-attachments/assets/d100bb32-0505-4426-aba3-d80119dc43d6)
![1_2_3_4_5_6_7_8_merged_page-0009](https://github.com/user-attachments/assets/4bf7fa52-dfb9-4c6f-8280-4263ee47079a)
![1_2_3_4_5_6_7_8_merged_page-0011](https://github.com/user-attachments/assets/f8429d39-012f-47d5-98cb-a293580434f8)
![1_2_3_4_5_6_7_8_merged_page-0013](https://github.com/user-attachments/assets/7780bea3-dab6-4703-b41b-8daeaf72e68d)
![1_2_3_4_5_6_7_8_merged_page-0015](https://github.com/user-attachments/assets/d256b275-84b6-41e5-9b5b-8c1ebe656471)







