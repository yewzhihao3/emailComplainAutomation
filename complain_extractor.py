import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import uuid
import json

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
        complaint_id = f"COMP-{str(uuid.uuid4())[:8]}"
        # Map fields from Google Sheet to database fields
        complaint = {
            "id": complaint_id,
            "name": record.get("Name ", ""),
            "email": record.get("Email", ""),
            "contact_number": record.get("Contact Number", ""),
            "order_id": record.get("Order ID / Reference No.  ", ""),
            "product_name": record.get("Product Name / Batch No.  ", ""),
            "purchase_date": record.get("Date of Purchase / Delivery  ", ""),
            "complaint_category": record.get("Complaint Category  ", ""),
            "description": record.get("Detailed Description  ", ""),
            "photo_proof_link": record.get("Upload photo/video proof (via Google Drive link)  ", ""),
            "importance_level": None,  # To be filled by AI
            "received_at": datetime.now().isoformat()
        }
        formatted_complaints["complaints"].append(complaint)
    
    return formatted_complaints

if __name__ == "__main__":
    complaints = get_complaints_data()
    print(json.dumps(complaints, indent=2))
