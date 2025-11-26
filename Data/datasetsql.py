# job_portal_dashboard/data_loader.py

import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import pymysql
from sqlalchemy import create_engine
import pymongo
import sys
import os
from dotenv import load_dotenv

# --- 0. Load Environment Variables ---
# This loads the variables from the .env file into the system environment
load_dotenv()

# --- 1. MongoDB Connection Setup ---
# Fetching secrets from environment variables
MONGO_URI = os.getenv('MONGO_URI')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME')
MONGO_COLLECTION_NAME = os.getenv('MONGO_COLLECTION_NAME')


def get_config_from_mongo():
    """
    Connects to MongoDB and retrieves the SQL configuration.
    Returns the dictionary found under 'connection_config'.
    """
    # Check if Mongo credentials exist
    if not MONGO_URI:
        print("❌ Error: MONGO_URI not found in .env file.")
        return None

    try:
        client = pymongo.MongoClient(MONGO_URI)
        db = client[MONGO_DB_NAME]
        collection = db[MONGO_COLLECTION_NAME]

        # Query for the specific document type provided in your JSON
        query = {"type": "db_connection_config"}

        # Fetch the document
        document = collection.find_one(query)

        if document and 'connection_config' in document:
            print("✅ Configuration successfully retrieved from MongoDB.")
            return document['connection_config']
        else:
            print("⚠️ Document not found or missing 'connection_config' key.")
            return None

    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        return None


# --- 2. Define DB_CONFIG using retrieved data ---

# Fetch the data
mongo_config_data = get_config_from_mongo()

if mongo_config_data:
    # If fetch was successful, define DB_CONFIG using the Mongo data
    DB_CONFIG = mongo_config_data
else:
    # Fallback: If Mongo fails, use the local defaults from .env
    print("⚠️ Using local fallback configuration from .env.")

    DB_CONFIG = {
        'host': os.getenv('SQL_HOST'),
        'user': os.getenv('SQL_USER'),
        'password': os.getenv('SQL_PASSWORD'),
        'database': os.getenv('SQL_DATABASE'),
        'table_name': os.getenv('SQL_TABLE_NAME')
    }

    # Check if fallback loaded correctly
    if not DB_CONFIG['host']:
        print("❌ Error: SQL fallback credentials not found in .env file.")

# --- 3. Verify the Configuration ---
# SECURITY NOTE: In production, avoid printing passwords.
# We print the host/db to verify it loaded, but mask the password.
print("\nActive DB_CONFIG:")
print({k: v if k != 'password' else '******' for k, v in DB_CONFIG.items()})


# --- 4. Data Loading Functions ---

def load_data():
    """
    Loads job seeker data from a MySQL database.
    Performs initial data cleaning and feature engineering.
    This is the PRIMARY data source.
    """
    df = pd.DataFrame()

    # Ensure we have a valid config before trying to connect
    if not DB_CONFIG or not DB_CONFIG.get('host'):
        print("❌ Critical Error: No Database Configuration available.")
        return df

    try:
        # Create SQLAlchemy engine for MySQL
        engine_url = (
            f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
            f"@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
        )
        engine = create_engine(engine_url)

        # SQL query to select all necessary columns.
        sql_query = f"SELECT * FROM {DB_CONFIG['table_name']} ORDER BY id DESC LIMIT 20000;"

        # Load data from SQL into a Pandas DataFrame
        df = pd.read_sql(sql_query, engine)
        print(f"Data loaded from MySQL table: {DB_CONFIG['table_name']}.")

    except Exception as e:
        print(f"Error loading data from MySQL: {e}")
        # Return empty DF or handle error as needed
        return pd.DataFrame()

    # --- Data Cleaning and Feature Engineering ---

    # Rename columns based on the CSV structure provided
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
    df['application_date'] = pd.to_datetime(df['application_date'], errors='coerce')

    # Feature Engineering: jobpage_status
    # Logic: Check if status is 'active' (case-insensitive), else 'Inactive'
    df['jobpage_status'] = df['application_status'].apply(
        lambda x: 'Active' if str(x).strip().lower() == 'active' else 'Inactive')

    # Drop rows where date conversion failed
    initial_rows = len(df)
    df.dropna(subset=['application_date'], inplace=True)
    if len(df) < initial_rows:
        print(f"Dropped {initial_rows - len(df)} rows with invalid application dates.")

    # Feature Engineering: Time components
    df['month'] = df['application_date'].dt.month
    df['day_of_month'] = df['application_date'].dt.day
    df['year_month'] = df['application_date'].dt.to_period('M').astype(str)

    # Clean up categorical columns
    if 'dtype' in df.columns:
        df['dtype'] = df['dtype'].fillna('Unknown').astype(str).str.strip()
    if 'regsource' in df.columns:
        df['regsource'] = df['regsource'].fillna('Unknown').astype(str).str.strip()
    if 'application_status' in df.columns:
        df['application_status'] = df['application_status'].astype(str).str.strip()

    print(f"Final DataFrame shape (load_data): {df.shape}")
    return df


def load_unique_most_recent_data(df=None) -> pd.DataFrame:
    """
    Takes the DataFrame from load_data() and deduplicates it using Pandas.
    It keeps only the record with the highest 'id' (most recent) for each 'applicant_id'.

    Args:
        df (pd.DataFrame, optional): The dataframe returned by load_data().
                                     If None, it calls load_data() internally.
    """
    # 1. Get the data (either passed in or loaded fresh)
    if df is None:
        print("No DataFrame provided to load_unique_most_recent_data, calling load_data()...")
        df = load_data()
    else:
        print("Using provided DataFrame for deduplication...")
        # Create a copy to avoid modifying the original dataframe in memory
        df = df.copy()

    if df.empty:
        print("DataFrame is empty. Returning empty DataFrame.")
        return df

    # 2. Verify required columns exist
    if 'applicant_id' not in df.columns:
        print("Error: 'applicant_id' column not found. Ensure load_data() ran correctly.")
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