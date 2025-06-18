from database import Database, ProcessStatus, ImportanceLevel
from ai_analyzer import AIAnalyzer
from complain_extractor import get_complaints_data
from export_handler import export_to_csv
import schedule
import time
from datetime import datetime
import logging
import backoff
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('complaint_analysis.log'),
        logging.StreamHandler()
    ]
)

class ComplaintAnalysisSystem:
    def __init__(self, api_key):
        self.db = Database()
        self.analyzer = AIAnalyzer(api_key)
        self.logger = logging.getLogger(__name__)
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    def load_complaints_data(self):
        """Load complaints from Google Sheets into the database"""
        # Clear existing data first
        if self.db.clear_all_data():
            self.logger.info("Cleared existing data from database")
        else:
            self.logger.error("Failed to clear existing data from database")
            return

        # Get complaints from Google Sheets
        complaints_data = get_complaints_data()
        
        for complaint in complaints_data['complaints']:
            success = self.db.add_complaint(complaint)
            if success:
                self.logger.info(f"Added complaint {complaint['id']} to database")
            else:
                self.logger.error(f"Failed to add complaint {complaint['id']}")

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def _analyze_single_complaint(self, complaint_text):
        """Process a single complaint with retry logic"""
        analysis = self.analyzer.analyze_complaint(complaint_text)
        if "API Error" in analysis.get('root_cause', ''):
            raise Exception(f"API Error: {analysis.get('suggested_solution')}")
        return analysis

    def process_complaints(self):
        """Process all unprocessed complaints"""
        self.logger.info("Starting complaint processing cycle")
        unprocessed = self.db.get_unprocessed_complaints()
        
        for complaint in unprocessed:
            self.logger.info(f"Processing complaint {complaint.id}")
            
            try:
                # Create a comprehensive complaint text for analysis
                complaint_text = f"""
                Complaint Category: {complaint.complaint_category}
                Product: {complaint.product_name}
                Order ID: {complaint.order_id}
                Description: {complaint.description}
                """
                
                # Analyze complaint using AI with retry logic
                analysis = self._analyze_single_complaint(complaint_text)
                
                # Convert lists to strings for database storage
                root_cause = analysis.get('root_cause', 'Analysis failed')
                suggested_solution = analysis.get('suggested_solution', 'No solution provided')
                
                # If root_cause is a list, convert it to a string
                if isinstance(root_cause, list):
                    root_cause = '\n'.join(root_cause)
                
                # If suggested_solution is a list, convert it to a string
                if isinstance(suggested_solution, list):
                    suggested_solution = '\n'.join(suggested_solution)
                
                # Update database with analysis results (importance level will be auto-determined)
                success = self.db.update_complaint_analysis(
                    complaint.id,
                    root_cause,
                    suggested_solution
                )
                
                if success:
                    self.logger.info(f"Successfully processed complaint {complaint.id}")
                else:
                    self.logger.error(f"Failed to update analysis for complaint {complaint.id}")
                    
            except Exception as e:
                self.logger.error(f"Failed to process complaint {complaint.id}: {str(e)}")
                # Mark complaint as failed with error information
                self.db.mark_complaint_failed(
                    complaint.id,
                    f"Failed to process after {self.max_retries} attempts: {str(e)}"
                )

    def generate_report(self):
        """Generate a summary report of all complaints"""
        complaints = self.db.get_all_complaints()
        
        report = {
            'total_complaints': len(complaints),
            'processed_complaints': len([c for c in complaints if c.processed == ProcessStatus.SUCCESSFUL]),
            'failed_complaints': len([c for c in complaints if c.processed == ProcessStatus.FAILED]),
            'pending_complaints': len([c for c in complaints if c.processed == ProcessStatus.PENDING]),
            'latest_analyses': []
        }
        
        for complaint in complaints:
            if complaint.processed == ProcessStatus.SUCCESSFUL:
                report['latest_analyses'].append({
                    'id': complaint.id,
                    'category': complaint.complaint_category,
                    'product': complaint.product_name,
                    'root_cause': complaint.root_cause,
                    'solution': complaint.suggested_solution,
                    'importance': complaint.importance_level.value if complaint.importance_level else 'Unknown',
                    'status': complaint.processed.value,
                    'processed_at': complaint.processed_at.isoformat() if complaint.processed_at else None
                })
        
        # self.logger.info(f"Report generated: {report}")
        return report

def main():
    # Initialize the system with API key from environment variable
    api_key = os.getenv('API_KEY')
    if not api_key:
        logging.error("API key not found in environment variables. Please check your .env file.")
        return
        
    system = ComplaintAnalysisSystem(api_key)
    
    try:
        # Load complaints from Google Sheets
        system.load_complaints_data()
        
        # Process all complaints once
        system.process_complaints()
        
        # Generate final report
        report = system.generate_report()
        
        # Log completion
        logging.info("Complaint processing completed successfully!")
        logging.info(f"Final report: {report}")
        
        # Ask user if they want to export CSV
        while True:
            user_input = input("\nWould you like to export the complaints to CSV? (y/n): ").lower()
            
            if user_input in ['y', 'yes']:
                logging.info("Exporting complaints to CSV...")
                success = export_to_csv()
                if success:
                    logging.info("CSV export completed successfully!")
                else:
                    logging.error("CSV export failed!")
                break
            elif user_input in ['n', 'no']:
                logging.info("CSV export skipped.")
                break
            else:
                print("Please enter 'y' or 'n'")
        
        logging.info("System will now exit.")
        
    except KeyboardInterrupt:
        logging.info("System shutdown requested. Stopping gracefully...")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise

if __name__ == "__main__":
    main() 