# job_portal_dashboard/data_loader.py
"""
import pandas as pd
from datetime import datetime, timedelta
import numpy as np # Ensure numpy is imported if you use mock data

#data loading
def load_data():

    #Loads job seeker data from a CSV file or creates mock data if the file is not found.
    #Performs initial data cleaning and feature engineering.

    try:
        df = pd.read_csv("jobseeker_dashboard_updated2.csv")
        print("Data loaded from CSV.")
    except FileNotFoundError:
        print("CSV not found. Creating mock data...")
        # Mock data generation
        num_rows = 5000
        start_date = datetime(2024, 1, 1)
        dates = [start_date + timedelta(days=np.random.randint(0, 365), hours=np.random.randint(0, 24)) for _ in
                 range(num_rows)]
        data = {
            'dateUTC': dates,
            'status': np.random.choice(['Applied', 'Interview', 'Rejected'], num_rows),
            'countryCode': np.random.choice(['US', 'CA', 'MX', 'UK', 'DE'], num_rows),
            'title': np.random.choice(
                ['Software Engineer', 'Data Analyst', 'Product Manager', 'UX Designer', 'Marketing Specialist'],
                num_rows),
            'userID': [f'user_{i}' for i in range(num_rows)],
            'isDataFromCV': np.random.choice([1, 0], num_rows, p=[0.6, 0.4])
        }
        df = pd.DataFrame(data)
        print("Mock data created.")

    # Rename columns
    df.rename(columns={
        'dateUTC': 'application_date',
        'status': 'application_status',
        'countryCode': 'applicant_location',
        'title': 'job_title',
        'userID': 'applicant_id',
        'deviceType': 'dtype',
        'registerSource':'regsource'
       }, inplace=True)

    # Data type conversions and feature engineering
    df['application_date'] = pd.to_datetime(df['application_date'])
    df['jobpage_status'] = df['isDataFromCV'].apply(
        lambda x: 'Active' if (x == 1 or (isinstance(x, str) and x.lower() == 'active')) else 'Inactive')
    df['month'] = df['application_date'].dt.month
    df['day_of_month'] = df['application_date'].dt.day
    df['year_month'] = df['application_date'].dt.to_period('M').astype(str)
    # df['device_type']=df['device_type'].astype(str)

    return df

df = pd.read_csv("jobseeker_dashboard_updated2.csv")
print(df['deviceType'].head())
print(df['registerSource'].unique())
    
"""