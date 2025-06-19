import csv
import os
from datetime import datetime
from database import Database, ProcessStatus, ImportanceLevel
import logging

def export_to_csv():
    """
    Export complaints data to a CSV file.
    The file will be saved in an 'exports' folder with timestamp-based naming.
    """
    logger = logging.getLogger(__name__)
    logger.info('Export in progress...')
    
    # Create exports folder if it doesn't exist
    exports_folder = "exports"
    if not os.path.exists(exports_folder):
        os.makedirs(exports_folder)
        logger.info(f"Created exports folder: {exports_folder}")
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = os.path.join(exports_folder, f"complaints_export_{timestamp}.csv")
    
    # Define CSV headers based on our current database schema, with separate columns for root causes and solutions
    headers = [
        'Complaint ID', 'Name', 'Email', 'Contact Number', 'Order ID', 
        'Product Name', 'Purchase Date', 'Complaint Category', 'Description', 
        'Photo Proof Link', 'Importance Level', 'Status', 'Received At', 
        'Root Cause 1', 'Root Cause 2', 'Root Cause 3',
        'Solution 1', 'Solution 2', 'Solution 3',
        'Processed At'
    ]
    
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
                # Parse root causes and solutions into separate columns
                def parse_points(val):
                    if not val:
                        return ["", "", ""]
                    if isinstance(val, list):
                        return val + ["", "", ""][:3-len(val)]
                    # If it's a string, try to split by newlines or numbers
                    import re
                    # Try splitting by numbered points first
                    points = re.findall(r'\d+\.\s*(.*?)(?=\n|$)', val)
                    if len(points) == 3:
                        return points
                    # Otherwise, split by newlines
                    split_points = [p.strip() for p in val.split('\n') if p.strip()]
                    return split_points + ["", "", ""][:3-len(split_points)]
                root_causes = parse_points(complaint.root_cause)
                solutions = parse_points(complaint.suggested_solution)
                writer.writerow([
                    complaint.id,
                    complaint.name or '',
                    complaint.email or '',
                    complaint.contact_number or '',
                    complaint.order_id or '',
                    complaint.product_name or '',
                    complaint.purchase_date or '',
                    complaint.complaint_category or '',
                    complaint.description or '',
                    complaint.photo_proof_link or '',
                    complaint.importance_level.value if complaint.importance_level else '',
                    complaint.processed.value if complaint.processed else '',
                    complaint.received_at.isoformat() if complaint.received_at else '',
                    root_causes[0],
                    root_causes[1],
                    root_causes[2],
                    solutions[0],
                    solutions[1],
                    solutions[2],
                    complaint.processed_at.isoformat() if complaint.processed_at else ''
                ])
        logger.info(f'Export complete. File saved as: {filename}')
        print(f"✅ CSV export saved successfully: {filename}")
        return True
    except Exception as e:
        logger.error(f"Error exporting to CSV: {str(e)}")
        print(f"❌ Error exporting to CSV: {str(e)}")
        return False

def main():
    while True:
        user_input = input("\nWould you like to export the complaints to CSV? (y/n): ").lower()
        
        if user_input in ['y', 'yes']:
            export_to_csv()
            break
        elif user_input in ['n', 'no']:
            break
        else:
            print("\nPlease enter 'y' or 'n'")

if __name__ == "__main__":
    main() 