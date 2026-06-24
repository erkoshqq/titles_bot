import os
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
CREDS_FILE = os.getenv("GOOGLE_CREDS_FILE", "credentials.json")

# Column headers per category
HEADERS = {
    "youtube": ["title", "author", "url"],
    "anime":   ["title"],
    "movies":  ["title"],
    "series":  ["title"],
    "games":   ["title"],
}

_client = None
_spreadsheet = None

def get_sheet(category: str):
    global _client, _spreadsheet
    if _client is None:
        creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        _client = gspread.authorize(creds)
    if _spreadsheet is None:
        _spreadsheet = _client.open_by_key(SHEET_ID)

    # Get or create worksheet for this category
    try:
        ws = _spreadsheet.worksheet(category)
    except gspread.WorksheetNotFound:
        ws = _spreadsheet.add_worksheet(title=category, rows=1000, cols=10)
        headers = HEADERS.get(category, ["title"])
        ws.append_row(headers)
    return ws

def get_items(category: str) -> list[dict]:
    ws = get_sheet(category)
    records = ws.get_all_records()
    return records

def add_item(category: str, data: dict):
    ws = get_sheet(category)
    headers = HEADERS.get(category, ["title"])
    row = [data.get(h, "") for h in headers]
    ws.append_row(row)

def delete_item(category: str, row_index: int):
    ws = get_sheet(category)
    # +2 because: 1-indexed + header row
    ws.delete_rows(row_index + 2)
