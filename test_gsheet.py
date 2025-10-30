import gspread
from google.oauth2.service_account import Credentials

try:
    creds = Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_url(
        "https://docs.google.com/spreadsheets/d/17inpznMMjoVS3CT8P3la_AD40i1txifSZWiPFDenLY0/edit?usp=sharing"
    ).worksheet("Sheet1")
    emails = sheet.col_values(1)
    print("✅ Connected successfully!")
    print("Premium users list:", emails)
except Exception as e:
    print("❌ Error:", e)
