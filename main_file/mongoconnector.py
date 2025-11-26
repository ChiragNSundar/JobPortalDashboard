import pymongo
from pymongo import MongoClient, errors
import csv
from datetime import datetime
import sys

# --- Configuration ---
# MongoDB Connection String (Standard local URI)
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "job_database"
COLLECTION_NAME = "job_data"
CSV_FILE_PATH = 'jobseeker_dashboard_updated2.csv'

# --- Type Map Definition ---
TYPE_MAP = {
    'id': int, 'dateUTC': 'date', 'siteInstanceID': int, 'countryCode': str,
    'status': str, 'dataSource': str, 'targetRefID': str, 'title': str,
    'userID': int, 'userEmail': str, 'trafficSource': str, 'registerSource': str,
    'isSearchable': int, 'hasJbeAlert': int, 'isDataFromCV': int, 'deviceType': str,
    'timeCreatedUTC': 'datetime', 'timeUpdatedUTC': 'datetime', 'timeModifiedDB': 'datetime',
    'row_num': int
}


# ---------------------------

def safe_cast(value, target_type, column_name):
    """
    Safely casts a string value to the required Python type.
    Unlike SQL, for MongoDB we want to return actual datetime objects, not strings.
    """
    if not value or value.strip() == "":
        if target_type == int and column_name == 'id':
            raise ValueError(f"ID cannot be empty.")
        return None

    try:
        if target_type == int:
            return int(value)
        elif target_type == 'date':
            # Convert to datetime object, normalize to midnight
            return datetime.strptime(value, '%Y-%m-%d')
        elif target_type == 'datetime':
            # Convert to datetime object
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        return value  # Default to string
    except ValueError:
        raise ValueError(f"Type mismatch: Expected {target_type} for column '{column_name}' but got '{value}'.")
    except Exception as e:
        raise Exception(f"Casting error for '{column_name}': {e}")


def insert_data_from_csv_dynamic():
    client = None
    successful_inserts = 0
    failed_records = []

    try:
        # 1. Connect to MongoDB
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        print("Connection to MongoDB successful.")

        # 2. Read CSV and process data
        with open(CSV_FILE_PATH, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)

            COLUMNS = csv_reader.fieldnames
            if not COLUMNS:
                raise Exception("CSV file is empty or has no header row.")

            # --- Check for missing required columns ---
            MISSING_COLUMNS = [col for col in TYPE_MAP if col not in COLUMNS and col != 'row_num']
            if MISSING_COLUMNS:
                print(f"\nFATAL ERROR: Missing columns in CSV: {MISSING_COLUMNS}")
                return

            # Dynamically determine valid columns
            VALID_COLUMNS = [col for col in COLUMNS if col in TYPE_MAP]

            data_to_insert = []

            for row_index, row_dict in enumerate(csv_reader, 1):
                document = {}
                is_row_valid = True

                for col_name in VALID_COLUMNS:
                    csv_value = row_dict.get(col_name, '')
                    target_type = TYPE_MAP[col_name]

                    try:
                        casted_value = safe_cast(csv_value, target_type, col_name)
                        # Build the dictionary (Document)
                        document[col_name] = casted_value
                    except (ValueError, Exception) as e:
                        print(f"Data Validation Error in Row {row_index} (Column '{col_name}'): {e}")
                        failed_records.append({'row': row_index, 'data': row_dict, 'error': str(e)})
                        is_row_valid = False
                        break

                if is_row_valid:
                    data_to_insert.append(document)

            # 3. Execute batch insert (Chunking)
            # MongoDB can handle large batches, but chunking is still good for memory management.
            CHUNK_SIZE = 500

            if data_to_insert:
                print(f"Found {len(data_to_insert)} records to process.")

                for i in range(0, len(data_to_insert), CHUNK_SIZE):
                    chunk = data_to_insert[i:i + CHUNK_SIZE]
                    try:
                        # insert_many is the MongoDB equivalent of executemany
                        # ordered=False allows the batch to continue even if one doc fails (optional)
                        collection.insert_many(chunk, ordered=True)

                        successful_inserts += len(chunk)
                        print(f"Inserted chunk ending at row index {i + len(chunk)}.")

                    except errors.BulkWriteError as bwe:
                        # Handle partial batch failures
                        print(f"\n--- MONGODB WRITE ERROR in CHUNK starting at {i} ---")
                        print(bwe.details)
                        # Add failed docs to log
                        failed_records.append({'row': 'Chunk Error', 'data': 'See Mongo Logs', 'error': str(bwe)})
                    except Exception as e:
                        print(f"General Error in chunk: {e}")
                        failed_records.append({'row': 'Chunk Error', 'data': 'Unknown', 'error': str(e)})

            else:
                print("No valid records found in CSV to insert.")

    except FileNotFoundError:
        print(f"\nERROR: CSV file not found at path: {CSV_FILE_PATH}")

    except errors.PyMongoError as e:
        print(f"\n--- MONGODB CONNECTION ERROR ---")
        print(f"Error: {e}")

    except Exception as e:
        print(f"\n--- GENERAL ERROR ---")
        print(f"An error occurred: {e}")

    finally:
        # Close connection
        if client:
            client.close()
            print("MongoDB connection closed.")

        if failed_records:
            print(f"\n--- FAILED RECORDS SUMMARY ({len(failed_records)} total) ---")
            try:
                with open('failed_inserts_log.csv', mode='w', newline='', encoding='utf-8') as outfile:
                    # Handle cases where 'data' might be a string (from chunk error) or dict
                    first_data = failed_records[0]['data']
                    fieldnames = first_data.keys() if isinstance(first_data, dict) else ['Error_Details']

                    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for record in failed_records:
                        if isinstance(record['data'], dict):
                            writer.writerow(record['data'])
                        else:
                            outfile.write(f"{record}\n")
                print(f"Details of failed records written to 'failed_inserts_log.csv'")
            except Exception as log_err:
                print(f"Could not write log file: {log_err}")
            print("--------------------------------------------------")


if __name__ == "__main__":
    insert_data_from_csv_dynamic()