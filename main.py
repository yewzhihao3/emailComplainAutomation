from database import Database, ProcessStatus, ImportanceLevel, Complaint
from ai_analyzer import AIAnalyzer
from complain_extractor import get_complaints_data
from export_handler import export_to_csv
from visualization_manager import VisualizationManager
from complaint_processor import ComplaintProcessor
from ui_manager import UIManager
from datetime import datetime
import logging
import os
import sys
from dotenv import load_dotenv

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Load environment variables - handle both development and frozen executable
def load_env_file():
    """Load .env file from appropriate location based on environment"""
    # Try multiple possible locations for the .env file
    possible_paths = [
        resource_path('config/.env'),           # Development or bundled
        resource_path('.env'),                  # Root directory fallback
        os.path.join(os.path.dirname(sys.executable), 'config', '.env'),  # Frozen executable
        os.path.join(os.path.dirname(sys.executable), '.env'),            # Frozen executable fallback
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            load_dotenv(path)
            print(f"✅ Loaded .env from: {path}")
            return True
    
    print("❌ No .env file found in any of the expected locations")
    return False

# Load environment variables
load_env_file()

# Configure logging
def setup_logging():
    # Create logs folder if it doesn't exist
    logs_folder = "logs"
    if not os.path.exists(logs_folder):
        os.makedirs(logs_folder)
        print(f"📁 Created logs folder at: {os.path.abspath(logs_folder)}")
    
    # Use a single log file with rotation instead of timestamp-based naming
    log_filename = os.path.join(logs_folder, 'complaint_analysis.log')
    
    # Configure logging with rotation (max 5MB per file, keep 3 backup files)
    from logging.handlers import RotatingFileHandler
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(
                log_filename, 
                maxBytes=5*1024*1024,  # 5MB
                backupCount=3
            ),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Log startup information
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("Application started")
    logger.info(f"Log file: {log_filename}")
    logger.info("=" * 50)

def cleanup_old_logs():
    """Clean up old timestamp-based log files"""
    logs_folder = "logs"
    if not os.path.exists(logs_folder):
        return
    
    import glob
    # Find old timestamp-based log files
    old_logs = glob.glob(os.path.join(logs_folder, "complaint_analysis_*.log"))
    
    if old_logs:
        print(f"\n🗑️ Found {len(old_logs)} old log files. Cleaning up...")
        for log_file in old_logs:
            try:
                os.remove(log_file)
                print(f"   Deleted: {os.path.basename(log_file)}")
            except Exception as e:
                print(f"   Failed to delete {os.path.basename(log_file)}: {e}")
        print("✅ Cleanup completed!")
    else:
        print("\n✅ No old log files found.")

class ComplaintAnalysisSystem:
    def __init__(self, api_key):
        self.db = Database()
        self.analyzer = AIAnalyzer(api_key)
        self.processor = ComplaintProcessor(self.db, self.analyzer)
        self.visualizer = VisualizationManager(self.db)
        self.ui = UIManager()
        self.logger = logging.getLogger(__name__)

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
            successful_count = session.query(Complaint).filter_by(processed=ProcessStatus.SUCCESSFUL).count()
            session.query(Complaint).filter_by(processed=ProcessStatus.SUCCESSFUL).update({
                'processed': ProcessStatus.PENDING,
                'processed_at': None,
                'root_cause': None,
                'suggested_solution': None
            })
            
            # Reset failed complaints
            failed_count = session.query(Complaint).filter_by(processed=ProcessStatus.FAILED).count()
            session.query(Complaint).filter_by(processed=ProcessStatus.FAILED).update({
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

def main():
    """Main application with interactive menu"""
    # Initialize the system with API key from environment variable
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ API key not found in environment variables. Please check your .env file.")
        return
        
    # Setup logging first
    setup_logging()
    
    # Clean up old timestamp-based logs on startup
    cleanup_old_logs()
    
    system = ComplaintAnalysisSystem(api_key)
    
    # Show welcome message
    system.ui.show_welcome_message()
    
    try:
        while True:
            system.ui.show_menu()
            
            try:
                choice = system.ui.get_user_choice(1, 11)
                
                if choice == "exit":
                    break
                elif choice is None:
                    continue
                
                if choice == '1':
                    # Load NEW complaints only
                    print("\n📋 Loading new complaints from Google Sheets...")
                    system.load_complaints_data()
                
                elif choice == '2':
                    # Process UNPROCESSED complaints only
                    print("\n🔍 Processing unprocessed complaints...")
                    system.processor.process_complaints()
                
                elif choice == '3':
                    # Generate visualizations
                    print("\n📈 Generating visualizations...")
                    system.visualizer.generate_complaint_dashboard()
                
                elif choice == '4':
                    # View database summary
                    system.ui.show_statistics(system.db)
                
                elif choice == '5':
                    # View sample complaints
                    system.ui.show_sample_complaints(system.db)
                
                elif choice == '6':
                    # Export complaints to CSV
                    system.export_complaints()
                
                elif choice == '7':
                    # Process PENDING & FAILED complaints
                    print("\n🔄 Processing pending and failed complaints...")
                    system.processor.process_pending_and_failed_complaints()
                
                elif choice == '8':
                    # Reset processed complaints
                    if system.ui.confirm_reset_operation():
                        system.reset_processed_complaints()
                
                elif choice == '9':
                    # Full refresh
                    if system.ui.confirm_full_refresh():
                        system.clear_database()
                        system.load_complaints_data()
                        system.processor.process_complaints()
                
                elif choice == '10':
                    # Manage logs
                    system.ui.manage_logs()
                
                elif choice == '11':
                    # Exit
                    break
                
            except KeyboardInterrupt:
                print("\n\n⚠️  Operation cancelled by user.")
                continue
            except Exception as e:
                print(f"\n❌ An error occurred: {e}")
                system.ui.show_error_message(str(e))
                continue
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    finally:
        system.ui.show_goodbye_message()

if __name__ == "__main__":
    main() 