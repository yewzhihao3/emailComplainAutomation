from database import Database, ProcessStatus, ImportanceLevel
from ai_analyzer import AIAnalyzer
from complain_extractor import get_complaints_data
from export_handler import export_to_csv
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
        """Load complaints from Google Sheets into the database (only new ones)"""
        self.logger.info("Loading complaints from Google Sheets (only new ones)")
        
        # Get complaints from Google Sheets with database instance for sequential ID generation
        complaints_data = get_complaints_data(self.db)
        
        new_complaints_count = 0
        existing_complaints_count = 0
        
        for complaint in complaints_data['complaints']:
            result = self.db.add_complaint(complaint)
            if result == "added":
                new_complaints_count += 1
                self.logger.info(f"Added new complaint {complaint['id']} to database")
            elif result == "skipped":
                existing_complaints_count += 1
                self.logger.info(f"Skipped existing complaint with order_id {complaint.get('order_id')}")
            else:
                self.logger.error(f"Failed to add complaint {complaint['id']}")
        
        self.logger.info(f"Complaint loading completed: {new_complaints_count} new complaints added, {existing_complaints_count} existing complaints skipped")

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

    def clear_database(self):
        """Clear all data from the database"""
        print("\n🗑️ Clearing database to start fresh...")
        if self.db.clear_all_data():
            print("✅ Database cleared successfully")
            return True
        else:
            print("❌ Failed to clear database")
            return False

    def reset_processed_complaints(self):
        """Reset processed complaints to pending status"""
        print("\n🔄 Resetting processed complaints to pending...")
        
        session = self.db.Session()
        try:
            # Reset successful complaints
            successful_count = session.query(self.db.Complaint).filter_by(processed=ProcessStatus.SUCCESSFUL).count()
            session.query(self.db.Complaint).filter_by(processed=ProcessStatus.SUCCESSFUL).update({
                'processed': ProcessStatus.PENDING,
                'processed_at': None,
                'root_cause': None,
                'suggested_solution': None
            })
            
            # Reset failed complaints
            failed_count = session.query(self.db.Complaint).filter_by(processed=ProcessStatus.FAILED).count()
            session.query(self.db.Complaint).filter_by(processed=ProcessStatus.FAILED).update({
                'processed': ProcessStatus.PENDING,
                'processed_at': None,
                'root_cause': None,
                'suggested_solution': None
            })
            
            session.commit()
            
            print(f"✅ Reset {successful_count} successful complaints to pending")
            print(f"✅ Reset {failed_count} failed complaints to pending")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error resetting complaints: {e}")
            return False
        finally:
            session.close()
        
        stats_after = self.db.get_database_stats()
        print(f"Updated database stats: {stats_after}")
        return True

    def show_statistics(self):
        """Show current database statistics"""
        stats = self.db.get_database_stats()
        
        print("\n📊 Current Database Statistics:")
        print("=" * 30)
        print(f"Total complaints: {stats['total']}")
        print(f"Pending: {stats['pending']}")
        print(f"Successfully processed: {stats['successful']}")
        print(f"Failed: {stats['failed']}")
        print(f"Processing success rate: {stats['processed_percentage']}%")

    def show_sample_complaints(self):
        """Show sample complaints from the database"""
        complaints = self.db.get_all_complaints()
        
        if not complaints:
            print("\nℹ️ No complaints found in database.")
            return
        
        print(f"\n📋 Sample Complaints (showing first 5 of {len(complaints)}):")
        print("=" * 50)
        
        for i, complaint in enumerate(complaints[:5]):
            print(f"\nComplaint {i+1}:")
            print(f"  ID: {complaint.id}")
            print(f"  Order ID: {complaint.order_id}")
            print(f"  Name: {complaint.name}")
            print(f"  Category: {complaint.complaint_category}")
            print(f"  Status: {complaint.processed.value}")
            print(f"  Importance: {complaint.importance_level.value if complaint.importance_level else 'Unknown'}")
            if complaint.processed_at:
                print(f"  Processed at: {complaint.processed_at}")
            if complaint.root_cause:
                print(f"  Root Cause: {complaint.root_cause[:100]}...")
            print("-" * 30)

    def export_complaints(self):
        """Export complaints to CSV"""
        print("\n📤 Exporting complaints to CSV...")
        success = export_to_csv()
        if success:
            print("✅ CSV export completed successfully!")
        else:
            print("❌ CSV export failed!")
        return success

    def generate_summary_report(self):
        """Generate a clean summary report of all complaints"""
        stats = self.db.get_database_stats()
        
        summary = {
            'total_complaints': stats['total'],
            'processed_complaints': stats['successful'],
            'failed_complaints': stats['failed'],
            'pending_complaints': stats['pending'],
            'success_rate': f"{stats['processed_percentage']}%"
        }
        
        return summary

    def generate_report(self):
        """Generate a detailed report of all complaints (for export/analysis)"""
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
        
        return report

def show_menu():
    """Show the main menu"""
    print("\n🚀 Complaint Processing System - Main Menu")
    print("=" * 50)
    print("1. Load and process ALL complaints (⚠️ full refresh)")
    print("2. Load NEW complaints only")
    print("3. Process UNPROCESSED complaints only")
    print("4. Mark ALL as unprocessed (reset status)")
    print("5. View database summary 📊")
    print("6. View sample complaints")
    print("7. Export complaints to CSV")
    print("8. Exit")
    print("-" * 50)

def confirm_full_refresh():
    """Get confirmation for full refresh with strong warning"""
    print("\n⚠️  WARNING: FULL REFRESH OPERATION")
    print("=" * 50)
    print("This operation will:")
    print("• DELETE ALL existing complaint data from the database")
    print("• Load ALL complaints from Google Sheets")
    print("• Process ALL complaints with AI analysis")
    print("• This action cannot be undone!")
    print("=" * 50)
    
    # First confirmation
    confirm = input("\nAre you sure you want to proceed? (y/n): ").lower().strip()
    if confirm not in ['y', 'yes']:
        print("❌ Operation cancelled.")
        return False
    
    # Second confirmation with specific phrase
    print("\n⚠️  FINAL CONFIRMATION REQUIRED")
    print("To proceed, you must type exactly: 'Yes, I understand what am I doing'")
    print("This ensures you understand the consequences of this action.")
    
    phrase = input("\nType the confirmation phrase: ").strip()
    if phrase == "Yes, I understand what am I doing":
        print("✅ Confirmation received. Proceeding with full refresh...")
        return True
    else:
        print("❌ Incorrect phrase. Operation cancelled.")
        return False

def main():
    """Main application with interactive menu"""
    # Initialize the system with API key from environment variable
    api_key = os.getenv('API_KEY')
    if not api_key:
        print("❌ API key not found in environment variables. Please check your .env file.")
        return
        
    system = ComplaintAnalysisSystem(api_key)
    
    print("🚀 Complaint Processing System")
    print("=" * 50)
    print("Welcome to the intelligent complaint analysis system!")
    print("This system will help you process and analyze customer complaints efficiently.")
    
    try:
        while True:
            show_menu()
            
            try:
                choice = input("\nEnter your choice (1-8): ").strip()
                
                if choice == '1':
                    # Load and process ALL complaints (full refresh)
                    if confirm_full_refresh():
                        print("\n🔄 Starting full refresh...")
                        if system.clear_database():
                            system.load_complaints_data()
                            system.process_complaints()
                            stats = system.db.get_database_stats()
                            print(f"\n✅ Full refresh completed!")
                            print(f"📊 Summary: {stats['total']} complaints processed, {stats['successful']} successful, {stats['failed']} failed")
                        else:
                            print("❌ Failed to clear database. Operation cancelled.")
                
                elif choice == '2':
                    # Load NEW complaints only
                    print("\n📋 Loading new complaints from Google Sheets...")
                    system.load_complaints_data()
                
                elif choice == '3':
                    # Process UNPROCESSED complaints only
                    print("\n🔍 Processing unprocessed complaints...")
                    system.process_complaints()
                
                elif choice == '4':
                    # Mark ALL as unprocessed (reset status)
                    system.reset_processed_complaints()
                
                elif choice == '5':
                    # View database summary
                    system.show_statistics()
                
                elif choice == '6':
                    # View sample complaints
                    system.show_sample_complaints()
                
                elif choice == '7':
                    # Export complaints to CSV
                    system.export_complaints()
                
                elif choice == '8':
                    print("\n👋 Thank you for using the Complaint Processing System!")
                    break
                
                else:
                    print("❌ Invalid choice. Please enter a number between 1-8.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                logging.error(f"Error in main menu: {e}")
        
    except KeyboardInterrupt:
        print("\n\n👋 System shutdown requested. Stopping gracefully...")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        logging.error(f"Unexpected error: {str(e)}")
        raise

if __name__ == "__main__":
    main() 