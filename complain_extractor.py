import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import uuid

# Set up the scope and credentials
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

def get_google_sheets_client():
    """Initialize and return a Google Sheets client"""
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    return gspread.authorize(creds)

def get_complaints_data():
    """Fetch and format complaints data from Google Sheets"""
    client = get_google_sheets_client()
    sheet = client.open("Email Complaint (Responses)").sheet1
    data = sheet.get_all_records()
    
    formatted_complaints = {
        "complaints": []
    }
    
    for record in data:
        # Generate a unique ID for each complaint
        complaint_id = f"COMP-{str(uuid.uuid4())[:8]}"
        
        # Format the complaint data
        complaint = {
            "id": complaint_id,
            "sender": record.get("Email", "unknown@email.com"),  # Adjust field name as needed
            "subject": record.get("Subject", "No Subject"),      # Adjust field name as needed
            "body": record.get("Message", ""),                  # Adjust field name as needed
            "received_at": datetime.now().isoformat()  # You might want to get this from the sheet if available
        }
        formatted_complaints["complaints"].append(complaint)
    
    return formatted_complaints

if __name__ == "__main__":
    # Test the data retrieval
    complaints = get_complaints_data()
    for i, complaint in enumerate(complaints["complaints"], 1):
        print(f"{i}. {complaint}")
