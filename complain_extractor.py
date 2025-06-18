import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Set up the scope and credentials
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Open the spreadsheet (use the exact name or URL)
sheet = client.open("Email Complaint (Responses)").sheet1

# Read all form responses
data = sheet.get_all_records()

# Example: print them
for i, record in enumerate(data, 1):
    print(f"{i}. {record}")
