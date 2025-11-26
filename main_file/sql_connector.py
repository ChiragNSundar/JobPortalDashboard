import pymysql
from pymysql import Error
import csv
from datetime import datetime

# --- Configuration ---
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = ""  # Set your XAMPP root password here if it's not empty
DB_NAME = "jobdatabase"
TABLE_NAME = "jobseeker_data"
CSV_FILE_PATH = 'jobseeker_dashboard_updated2.csv'

# --- Type Map Definition ---
# THIS IS CRITICAL: Define the expected Python type for each column header
# that exists in your database schema.
TYPE_MAP = {
    'id': int, 'dateUTC': 'date', 'siteInstanceID': int, 'countryCode': str,
    'status': str, 'dataSource': str, 'targetRefID': str, 'title': str,
    'userID': int, 'userEmail': str, 'trafficSource': str, 'registerSource': str,
    'isSearchable': int, 'hasJbeAlert': int, 'isDataFromCV': int, 'deviceType': str,
    'timeCreatedUTC': 'datetime', 'timeUpdatedUTC': 'datetime', 'timeModifiedDB': 'datetime',
    'row_num': int
}


# ---------------------------

def safe_cast(value, target_type, column_name, row_num):
    """Safely casts a string value to the required type (int, date, datetime)."""
    # Treat empty strings as NULL, unless it's the ID column
    if not value:
        if target_type == int and column_name == 'id':
            raise ValueError(f"ID cannot be empty.")
        return None

    try:
        if target_type == int:
            return int(value)
        elif target_type == 'date':
            # MySQL DATE format: YYYY-MM-DD
            datetime.strptime(value, '%Y-%m-%d')
            return value
        elif target_type == 'datetime':
            # MySQL DATETIME format: YYYY-MM-DD HH:MM:SS
            datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return value
        return value  # Default to string
    except ValueError:
        raise ValueError(f"Type mismatch: Expected {target_type} for column '{column_name}' but got '{value}'.")
    except Exception as e:
        raise Exception(f"Casting error for '{column_name}': {e}")


def insert_data_from_csv_dynamic():
    cnx = None
    successful_inserts = 0
    failed_records = []

    try:
        # 1. Connect to the database
        cnx = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cur = cnx.cursor()
        print("Connection to MySQL successful.")

        # 2. Read CSV and process data
        with open(CSV_FILE_PATH, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)

            COLUMNS = csv_reader.fieldnames
            if not COLUMNS:
                raise Exception("CSV file is empty or has no header row.")

            # --- Check for missing required columns ---
            MISSING_COLUMNS = [col for col in TYPE_MAP if col not in COLUMNS and col != 'row_num']
            if MISSING_COLUMNS:
                print(
                    f"\nFATAL ERROR: The following columns required by the script/DB schema are MISSING from the CSV header: {MISSING_COLUMNS}")
                return  # Stop execution immediately

            # Dynamically determine the final list of columns to use (only those present in CSV AND TYPE_MAP)
            VALID_COLUMNS = [col for col in COLUMNS if col in TYPE_MAP]

            # Construct SQL statement dynamically
            sql = f"INSERT INTO {TABLE_NAME} ({', '.join(VALID_COLUMNS)}) VALUES ({', '.join(['%s'] * len(VALID_COLUMNS))})"

            data_to_insert = []

            for row_index, row_dict in enumerate(csv_reader, 1):
                record_values = []
                is_row_valid = True

                for col_name in VALID_COLUMNS:
                    csv_value = row_dict.get(col_name, '')
                    target_type = TYPE_MAP[col_name]

                    try:
                        casted_value = safe_cast(csv_value, target_type, col_name, row_index)
                        record_values.append(casted_value)
                    except (ValueError, Exception) as e:
                        print(f"Data Validation Error in Row {row_index} (Column '{col_name}'): {e}")
                        failed_records.append({'row': row_index, 'data': row_dict, 'error': str(e)})
                        is_row_valid = False
                        break

                if is_row_valid:
                    data_to_insert.append(tuple(record_values))

            # 3. Execute batch insert (with chunking for better resilience)
            CHUNK_SIZE = 500  # Commit every 500 rows

            if data_to_insert:
                print(f"Found {len(data_to_insert)} records to process.")

                for i in range(0, len(data_to_insert), CHUNK_SIZE):
                    chunk = data_to_insert[i:i + CHUNK_SIZE]
                    try:
                        cur.executemany(sql, chunk)
                        cnx.commit()  # Commit after each chunk
                        successful_inserts += len(chunk)
                        print(f"Committed chunk ending at row index {i + len(chunk)}.")
                    except Error as err:
                        # If a chunk fails, log it and roll back that chunk's transaction
                        print(f"\n--- DATABASE ERROR in CHUNK starting at row index {i} ---")
                        print(f"Error Code: {err.args[0]}")
                        print(f"Error Message: {err.args[1]}")
                        cnx.rollback()
                        print("Chunk rolled back. Continuing to next chunk.")
                        # Move failed records to the failed list (simplified for this example)
                        failed_records.extend([{'row': 'Chunk Error', 'data': chunk, 'error': err.args[1]}])

            else:
                print("No valid records found in CSV to insert.")

    except FileNotFoundError:
        print(f"\nERROR: CSV file not found at path: {CSV_FILE_PATH}")

    except Error as err:
        # Handle MySQL errors that occur before or outside the chunk loop
        print(f"\n--- DATABASE CONNECTION/INITIAL ERROR ---")
        print(f"Error Code: {err.args[0]}")
        print(f"Error Message: {err.args[1]}")
        if cnx:
            cnx.rollback()
        print("-----------------------------------------")

    except Exception as e:
        # Handle general errors (like connection failure before cursor is made)
        print(f"\n--- GENERAL ERROR ---")
        print(f"An error occurred: {e}")
        print("---------------------")

    finally:
        # Close connection safely using PyMySQL's .open attribute
        if cnx and cnx.open:
            cur.close()
            cnx.close()
            print("MySQL connection closed.")

        if failed_records:
            print(f"\n--- FAILED RECORDS SUMMARY ({len(failed_records)} total) ---")
            # Log failed records to a file for review
            with open('failed_inserts_log.csv', mode='w', newline='', encoding='utf-8') as outfile:
                # Try to get fieldnames from the first failed record's data dictionary
                fieldnames = failed_records[0]['data'].keys() if failed_records[0]['data'] else ['Data']
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                for record in failed_records:
                    writer.writerow(record['data'])
            print(f"Details of failed records written to 'failed_inserts_log.csv'")
            print("--------------------------------------------------")


if __name__ == "__main__":
    insert_data_from_csv_dynamic()