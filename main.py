from database import Database
from ai_analyzer import AIAnalyzer
from mock_data import MOCK_COMPLAINTS
import schedule
import time
from datetime import datetime
import logging
import backoff

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

    def load_mock_data(self):
        """Load mock complaints into the database"""
        # Clear existing data first
        if self.db.clear_all_data():
            self.logger.info("Cleared existing data from database")
        else:
            self.logger.error("Failed to clear existing data from database")
            return

        for complaint in MOCK_COMPLAINTS['complaints']:
            success = self.db.add_complaint(complaint)
            if success:
                self.logger.info(f"Added complaint {complaint['id']} to database")
            else:
                self.logger.error(f"Failed to add complaint {complaint['id']}")

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def _analyze_single_complaint(self, complaint):
        """Process a single complaint with retry logic"""
        analysis = self.analyzer.analyze_complaint(complaint.body)
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
                # Analyze complaint using AI with retry logic
                analysis = self._analyze_single_complaint(complaint)
                
                # Update database with analysis results
                success = self.db.update_complaint_analysis(
                    complaint.id,
                    analysis.get('root_cause', 'Analysis failed'),
                    analysis.get('suggested_solution', 'No solution provided')
                )
                
                if success:
                    self.logger.info(f"Successfully processed complaint {complaint.id}")
                else:
                    self.logger.error(f"Failed to update analysis for complaint {complaint.id}")
                    
            except Exception as e:
                self.logger.error(f"Failed to process complaint {complaint.id}: {str(e)}")
                # Update database with error information
                self.db.update_complaint_analysis(
                    complaint.id,
                    "Processing Error",
                    f"Failed to process after {self.max_retries} attempts: {str(e)}"
                )

    def generate_report(self):
        """Generate a summary report of all complaints"""
        complaints = self.db.get_all_complaints()
        
        report = {
            'total_complaints': len(complaints),
            'processed_complaints': len([c for c in complaints if c.processed]),
            'unprocessed_complaints': len([c for c in complaints if not c.processed]),
            'latest_analyses': []
        }
        
        for complaint in complaints:
            if complaint.processed:
                report['latest_analyses'].append({
                    'id': complaint.id,
                    'subject': complaint.subject,
                    'root_cause': complaint.root_cause,
                    'solution': complaint.suggested_solution,
                    'processed_at': complaint.processed_at.isoformat() if complaint.processed_at else None
                })
        
        self.logger.info(f"Report generated: {report}")
        return report

def main():
    # Initialize the system with your API key
    api_key = "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"
    system = ComplaintAnalysisSystem(api_key)
    
    try:
        # Load mock data
        system.load_mock_data()
        
        # Schedule regular processing
        schedule.every(1).hours.do(system.process_complaints)
        schedule.every(6).hours.do(system.generate_report)
        
        # Initial processing
        system.process_complaints()
        
        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logging.info("System shutdown requested. Stopping gracefully...")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise

if __name__ == "__main__":
    main() 