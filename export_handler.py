import csv
from datetime import datetime
from database import Database

def export_to_csv():
    """
    Export complaints data to a CSV file.
    The file will be named 'complaints_export_YYYY-MM-DD_HHMMSS.csv'
    """
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"complaints_export_{timestamp}.csv"
    
    # Define CSV headers
    headers = ['Complaint ID', 'Sender', 'Subject', 'Body', 'Received At', 'Root Cause', 'Suggested Solution', 'Processed At']
    
    try:
        # Initialize database
        db = Database()
        # Get all complaints including their analysis
        complaints = db.get_all_complaints()
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write headers
            writer.writerow(headers)
            
            # Write data
            for complaint in complaints:
                writer.writerow([
                    complaint.id,
                    complaint.sender,
                    complaint.subject,
                    complaint.body,
                    complaint.received_at.isoformat() if complaint.received_at else '',
                    complaint.root_cause if complaint.root_cause else '',
                    complaint.suggested_solution if complaint.suggested_solution else '',
                    complaint.processed_at.isoformat() if complaint.processed_at else ''
                ])
        
        print(f"\nSuccessfully exported complaints to {filename}")
        return True
    except Exception as e:
        print(f"\nError exporting to CSV: {str(e)}")
        return False

def main():
    while True:
        user_input = input("\nWould you like to export the complaints to CSV? (y/n): ").lower()
        
        if user_input in ['y', 'yes']:
            export_to_csv()
            break
        elif user_input in ['n', 'no']:
            print("\nExport cancelled.")
            break
        else:
            print("\nPlease enter 'y' or 'n'")

if __name__ == "__main__":
    main() 