import os
from gspread_dataframe import get_as_dataframe, set_with_dataframe
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import logging
import json
import sys

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def get_complaints_data(db_instance=None):
    """
    Extract complaints data from Google Sheets and return as a list of dictionaries.
    """
    logger = logging.getLogger(__name__)
    
    # Create config folder if it doesn't exist
    config_folder = "config"
    if not os.path.exists(config_folder):
        os.makedirs(config_folder)
        logger.info(f"Created config folder: {config_folder}")
        print(f"📁 Created config folder at: {os.path.abspath(config_folder)}")
    
    # Define the scope and credentials file path
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials_path = resource_path(os.path.join(config_folder, "credentials.json"))
    
    try:
        # Check if credentials file exists
        if not os.path.exists(credentials_path):
            logger.error(f"Credentials file not found at: {credentials_path}")
            logger.info("Please place your Google Sheets API credentials.json file in the config/ folder")
            return None
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
        client = gspread.authorize(creds)

        sheet = client.open("Email Complaint (Responses)").sheet1
        data = sheet.get_all_records()
        
        formatted_complaints = {
            "complaints": []
        }
        
        # Start complaint ID from 1 or get next available ID from database
        if db_instance:
            # Get the starting ID from database for sequential numbering
            starting_id = db_instance.get_next_complaint_id()
            # Extract the starting number
            try:
                starting_number = int(starting_id.split('-')[1])
            except (IndexError, ValueError):
                starting_number = 1
            
            for i, record in enumerate(data):
                complaint_id = f"COMP-{(starting_number + i):06d}"  # Increment sequentially
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
        else:
            # Fallback to simple counter if no database instance provided
            for i, record in enumerate(data):
                complaint_id = f"COMP-{(i + 1):06d}"  # Format as COMP-000001, COMP-000002, etc.
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
    except Exception as e:
        logger.error(f"Error extracting complaints from sheets: {e}")
        return None

if __name__ == "__main__":
    complaints = get_complaints_data()
    if complaints:
        print(json.dumps(complaints, indent=2))
