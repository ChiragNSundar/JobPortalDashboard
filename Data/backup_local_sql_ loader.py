# job_portal_dashboard/data_loader.py

import pandas as pd
from datetime import datetime
import pymysql
from sqlalchemy import create_engine

# --- Configuration ---
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = ""  # Set your XAMPP root password here if it's not empty
DB_NAME = "jobdatabase"
TABLE_NAME = "jobseeker_data"
CSV_FILE_PATH = '/Users/chiragnsundar/Documents/GitHub/JobPortalDashboard/Data/jobseeker_dashboard_updated2.csv'


# --- Data Loading Functions ---

def load_data():
    """
    Loads job seeker data from the local MySQL database using hardcoded config.
    Performs initial data cleaning and feature engineering.
    """
    df = pd.DataFrame()

    try:
        # Create SQLAlchemy engine for MySQL
        # Format: mysql+pymysql://user:password@host:port/database
        engine_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

        engine = create_engine(engine_url)

        # SQL query to select all necessary columns.
        # Limiting to 20,000 rows for performance; remove LIMIT if you want all data.
        sql_query = f"SELECT * FROM {TABLE_NAME} ORDER BY id DESC LIMIT 20000;"

        # Load data from SQL into a Pandas DataFrame
        df = pd.read_sql(sql_query, engine)
        print(f"✅ Data loaded from MySQL table: {TABLE_NAME}. Rows: {len(df)}")

    except Exception as e:
        print(f"❌ Error loading data from MySQL: {e}")
        return pd.DataFrame()

    # --- Data Cleaning and Feature Engineering ---

    if df.empty:
        print("⚠️ Warning: DataFrame is empty after SQL load.")
        return df

    # Rename columns to match the dashboard's expected format
    # Mapping SQL columns to Dashboard columns
    df.rename(columns={
        'dateUTC': 'application_date',
        'status': 'application_status',
        'countryCode': 'applicant_location',
        'title': 'job_title',
        'userID': 'applicant_id',
        'deviceType': 'dtype',
        'registerSource': 'regsource'
    }, inplace=True)

    # Convert date column, coercing errors to NaT
    if 'application_date' in df.columns:
        df['application_date'] = pd.to_datetime(df['application_date'], errors='coerce')

        # Drop rows where date conversion failed
        initial_rows = len(df)
        df.dropna(subset=['application_date'], inplace=True)
        if len(df) < initial_rows:
            print(f"Dropped {initial_rows - len(df)} rows with invalid application dates.")

        # Feature Engineering: Time components
        df['month'] = df['application_date'].dt.month
        df['day_of_month'] = df['application_date'].dt.day
        df['year_month'] = df['application_date'].dt.to_period('M').astype(str)
    else:
        print("⚠️ Warning: 'application_date' column missing (check 'dateUTC' in SQL).")

    # Feature Engineering: jobpage_status
    if 'application_status' in df.columns:
        df['jobpage_status'] = df['application_status'].apply(
            lambda x: 'Active' if str(x).strip().lower() == 'active' else 'Inactive')
        df['application_status'] = df['application_status'].astype(str).str.strip()

    # Clean up categorical columns
    if 'dtype' in df.columns:
        df['dtype'] = df['dtype'].fillna('Unknown').astype(str).str.strip()
    if 'regsource' in df.columns:
        df['regsource'] = df['regsource'].fillna('Unknown').astype(str).str.strip()

    print(f"Final DataFrame shape (load_data): {df.shape}")
    return df


def load_unique_most_recent_data(df=None) -> pd.DataFrame:
    """
    Takes the DataFrame from load_data() and deduplicates it.
    It keeps only the record with the highest 'id' (most recent) for each 'applicant_id'.
    """
    # 1. Get the data
    if df is None:
        print("No DataFrame provided to load_unique_most_recent_data, calling load_data()...")
        df = load_data()
    else:
        # Create a copy to avoid modifying the original dataframe in memory
        df = df.copy()

    if df.empty:
        return df

    # 2. Verify required columns exist
    if 'applicant_id' not in df.columns:
        print("Error: 'applicant_id' column not found.")
        return df

    if 'id' not in df.columns:
        print("Error: 'id' column not found. Cannot determine most recent record.")
        return df

    # 3. Perform Deduplication
    try:
        # Sort by 'id' in descending order (highest ID = newest)
        df_sorted = df.sort_values(by='id', ascending=False)

        # Drop duplicates based on 'applicant_id', keeping the first one
        df_unique = df_sorted.drop_duplicates(subset=['applicant_id'], keep='first')

        print(f"Deduplication complete. Rows reduced from {len(df)} to {len(df_unique)}.")
        return df_unique

    except Exception as e:
        print(f"Error during deduplication: {e}")
        return df