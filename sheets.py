
from pathlib import Path
import time
import gspread
from google.oauth2.service_account import Credentials


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

CREDENTIALS_FILE = (
    BASE_DIR
    / "credentials"
    / "google-service-account.json"
)

SPREADSHEET_ID = "1t_dik82cVKEVs3Mx9cgmW5Env8wMk_PkwLtkwVnvuzw"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ---------------------------------------------------------
# Google Sheets connection
# ---------------------------------------------------------

def get_client():
    """
    Create and return an authenticated gspread client.
    """

    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"Google credentials not found: {CREDENTIALS_FILE}"
        )

    credentials = Credentials.from_service_account_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
    )

    return gspread.authorize(credentials)


def get_spreadsheet():
    """
    Connect to Google Sheets with a few retries.

    Temporary Google/network connection failures
    should not immediately crash the application.
    """

    credentials = Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
    )

    last_error = None

    for attempt in range(3):

        try:

            client = gspread.authorize(
                credentials
            )

            spreadsheet = client.open_by_key(
                SPREADSHEET_ID
            )

            return spreadsheet

        except Exception as error:

            last_error = error

            print(
                f"Google Sheets connection attempt "
                f"{attempt + 1}/3 failed."
            )

            if attempt < 2:
                time.sleep(3)

    raise last_error



# ---------------------------------------------------------
# Worksheet access
# ---------------------------------------------------------

def get_sheet(sheet_name):
    """
    Return a worksheet by name.

    Example:
        get_sheet("Notification")
    """

    spreadsheet = get_spreadsheet()

    try:
        return spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        raise ValueError(
            f"Worksheet '{sheet_name}' was not found."
        )


# ---------------------------------------------------------
# Read data
# ---------------------------------------------------------


def get_all_records(sheet_name):
    """
    Return all records from a Google Sheet.

    Each record includes the actual Google Sheets
    row number so other modules can update that row.
    """

    worksheet = get_sheet(sheet_name)

    records = worksheet.get_all_records()

    # Google Sheets row 1 contains the headers.
    # Therefore the first data record is row 2.
    for index, record in enumerate(records, start=2):
        record["Row number"] = index

    return records




def get_headers(sheet_name):
    """
    Return the first row of a worksheet.
    """

    worksheet = get_sheet(sheet_name)

    return worksheet.row_values(1)


# ---------------------------------------------------------
# Append data
# ---------------------------------------------------------

def append_record(sheet_name, record):
    """
    Append one dictionary as a new row.

    The dictionary keys must match the worksheet headers.
    """

    worksheet = get_sheet(sheet_name)

    headers = worksheet.row_values(1)

    if not headers:
        raise ValueError(
            f"Worksheet '{sheet_name}' has no headers."
        )

    row = [
        record.get(header, "")
        for header in headers
    ]

    worksheet.append_row(
        row,
        value_input_option="USER_ENTERED",
    )


def update_record(sheet_name, row_number, updates):
    """
    Update specific columns in an existing Google Sheets row.

    Example:
        update_record(
            "Events",
            3,
            {
                "notification_status": "Processed",
            }
        )
    """

    worksheet = get_sheet(sheet_name)

    headers = worksheet.row_values(1)

    for field, value in updates.items():

        if field not in headers:
            raise ValueError(
                f"Column '{field}' does not exist "
                f"in sheet '{sheet_name}'."
            )

        column_number = headers.index(field) + 1

        worksheet.update_cell(
            row_number,
            column_number,
            value,
        )

    return True



# ---------------------------------------------------------
# Search records
# ---------------------------------------------------------

def find_records(sheet_name, column_name, value):
    """
    Find all records where a specific column equals value.

    Example:

        find_records(
            "Notification",
            "Notification Key",
            "katli|2026-08-22|00:09|mlotiio|0794345654|WhatsApp"
        )
    """

    records = get_all_records(sheet_name)

    matches = []

    for record in records:
        record_value = str(
            record.get(column_name, "")
        ).strip()

        if record_value == str(value).strip():
            matches.append(record)

    return matches


def record_exists(sheet_name, column_name, value):
    """
    Return True if at least one matching record exists.
    """

    matches = find_records(
        sheet_name,
        column_name,
        value,
    )

    return len(matches) > 0

def get_worksheet(sheet_name):
     """ Return a Google Sheets worksheet by name. """
     spreadsheet = get_spreadsheet() 
     return spreadsheet.worksheet(sheet_name)

# ---------------------------------------------------------
# Simple update helper
# ---------------------------------------------------------

def update_cell(sheet_name, row_number, column_number, value):
    """
    Update one cell.

    row_number and column_number are 1-based.
    """

    worksheet = get_sheet(sheet_name)

    worksheet.update_cell(
        row_number,
        column_number,
        value,
    )


# ---------------------------------------------------------
# Connection test
# ---------------------------------------------------------

if __name__ == "__main__":
    spreadsheet = get_spreadsheet()

    print("Connected successfully!")
    print(f"Spreadsheet: {spreadsheet.title}")

    print("\nSheets:")

    for worksheet in spreadsheet.worksheets():
        print(f"- {worksheet.title}")


def update_record(sheet_name, row_number, updates):
    """
    Update specific columns in a Google Sheets row.

    Example:

        update_record(
            "Notification",
            87,
            {
                "Status": "Sent",
                "Sent At": "2026-08-11T10:00:00+00:00"
            }
        )
    """

    worksheet = get_worksheet(sheet_name)

    headers = worksheet.row_values(1)

    for column_name, value in updates.items():

        if column_name not in headers:
            raise ValueError(
                f"Column '{column_name}' "
                f"does not exist in '{sheet_name}'"
            )

        column_number = (
            headers.index(column_name) + 1
        )

        worksheet.update_cell(
            row_number,
            column_number,
            value,
        )
