import logging
import backoff
from database import Complaint, ProcessStatus
from ai_analyzer import AIAnalyzer

class ComplaintProcessor:
    def __init__(self, db, analyzer):
        self.db = db
        self.analyzer = analyzer
        self.logger = logging.getLogger(__name__)
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def _analyze_single_complaint(self, complaint_text):
        """Process a single complaint with retry logic"""
        analysis = self.analyzer.analyze_complaint(complaint_text)
        if "API Error" in analysis.get('root_cause', ''):
            raise Exception(f"API Error: {analysis.get('suggested_solution')}")
        return analysis

    def process_complaints(self):
        """Process only unprocessed complaints"""
        self.logger.info("Starting complaint processing cycle (only unprocessed complaints)")
        
        # Show database statistics before processing
        stats_before = self.db.get_database_stats()
        self.logger.info(f"Database stats before processing: {stats_before}")
        
        unprocessed = self.db.get_unprocessed_complaints()
        
        if not unprocessed:
            self.logger.info("No unprocessed complaints found. All complaints have been analyzed.")
            return
        
        self.logger.info(f"Found {len(unprocessed)} unprocessed complaints to analyze")
        
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
        
        # Show database statistics after processing
        stats_after = self.db.get_database_stats()
        self.logger.info(f"Database stats after processing: {stats_after}")
        self.logger.info(f"Processing completed! Processed {stats_after['successful'] - stats_before['successful']} complaints")

    def process_pending_and_failed_complaints(self):
        """Process complaints that are in pending or failed status"""
        self.logger.info("Starting complaint processing for pending and failed complaints")
        
        # Show database statistics before processing
        stats_before = self.db.get_database_stats()
        self.logger.info(f"Database stats before processing: {stats_before}")
        
        # Get both pending and failed complaints
        session = self.db.Session()
        try:
            pending_and_failed = session.query(Complaint).filter(
                Complaint.processed.in_([ProcessStatus.PENDING, ProcessStatus.FAILED])
            ).all()
        finally:
            session.close()
        
        if not pending_and_failed:
            self.logger.info("No pending or failed complaints found. All complaints have been successfully processed.")
            print("ℹ️ No pending or failed complaints found. All complaints have been successfully processed.")
            return
        
        # Count by status
        pending_count = len([c for c in pending_and_failed if c.processed == ProcessStatus.PENDING])
        failed_count = len([c for c in pending_and_failed if c.processed == ProcessStatus.FAILED])
        
        self.logger.info(f"Found {len(pending_and_failed)} complaints to analyze ({pending_count} pending, {failed_count} failed)")
        print(f"🔍 Found {len(pending_and_failed)} complaints to analyze:")
        print(f"   📋 Pending: {pending_count}")
        print(f"   ❌ Failed: {failed_count}")
        
        processed_count = 0
        failed_count = 0
        
        for complaint in pending_and_failed:
            status_text = "pending" if complaint.processed == ProcessStatus.PENDING else "failed"
            self.logger.info(f"Processing {status_text} complaint {complaint.id}")
            print(f"Processing {status_text} complaint {complaint.id}...")
            
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
                    print(f"✅ Successfully processed complaint {complaint.id}")
                    processed_count += 1
                else:
                    self.logger.error(f"Failed to update analysis for complaint {complaint.id}")
                    print(f"❌ Failed to update analysis for complaint {complaint.id}")
                    failed_count += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to process complaint {complaint.id}: {str(e)}")
                print(f"❌ Failed to process complaint {complaint.id}: {str(e)}")
                # Mark complaint as failed with error information
                self.db.mark_complaint_failed(
                    complaint.id,
                    f"Failed to process after {self.max_retries} attempts: {str(e)}"
                )
                failed_count += 1
        
        # Show database statistics after processing
        stats_after = self.db.get_database_stats()
        self.logger.info(f"Database stats after processing: {stats_after}")
        self.logger.info(f"Processing completed! Processed {processed_count} complaints, {failed_count} failed")
        
        print(f"\n📊 Processing Summary:")
        print(f"✅ Successfully processed: {processed_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"📈 Total complaints processed: {processed_count + failed_count}") 