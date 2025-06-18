from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum
import logging

Base = declarative_base()

class ProcessStatus(enum.Enum):
    PENDING = "Pending"
    SUCCESSFUL = "Successful"
    FAILED = "Failed"
    CLOSED = "Closed"

class ImportanceLevel(enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class Complaint(Base):
    __tablename__ = 'complaints'

    id = Column(String(40), primary_key=True)
    name = Column(String(100))
    email = Column(String(100), nullable=False)
    contact_number = Column(String(50))
    order_id = Column(String(100))
    product_name = Column(String(200))
    purchase_date = Column(String(50))
    complaint_category = Column(String(100))
    description = Column(Text)
    photo_proof_link = Column(Text)
    importance_level = Column(Enum(ImportanceLevel), default=ImportanceLevel.MEDIUM)
    received_at = Column(DateTime, nullable=False)
    processed = Column(Enum(ProcessStatus), default=ProcessStatus.PENDING)
    root_cause = Column(Text)
    suggested_solution = Column(Text)
    processed_at = Column(DateTime)

class Database:
    def __init__(self, db_path='complaints.db'):
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.logger = logging.getLogger(__name__)

    def clear_all_data(self):
        """Clear all data from the complaints table"""
        session = self.Session()
        try:
            session.query(Complaint).delete()
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error clearing database: {e}")
            return False
        finally:
            session.close()

    def add_complaint(self, complaint_data):
        session = self.Session()
        try:
            # Check if complaint already exists
            existing = session.query(Complaint).filter_by(id=complaint_data['id']).first()
            if existing:
                # Update existing complaint
                for key, value in complaint_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.processed = ProcessStatus.PENDING
                existing.root_cause = None
                existing.suggested_solution = None
                existing.processed_at = None
            else:
                # Create new complaint
                complaint = Complaint(
                    id=complaint_data['id'],
                    name=complaint_data.get('name'),
                    email=complaint_data.get('email'),
                    contact_number=complaint_data.get('contact_number'),
                    order_id=complaint_data.get('order_id'),
                    product_name=complaint_data.get('product_name'),
                    purchase_date=complaint_data.get('purchase_date'),
                    complaint_category=complaint_data.get('complaint_category'),
                    description=complaint_data.get('description'),
                    photo_proof_link=complaint_data.get('photo_proof_link'),
                    importance_level=ImportanceLevel.MEDIUM,  # Default to medium
                    received_at=datetime.fromisoformat(complaint_data['received_at']),
                    processed=ProcessStatus.PENDING
                )
                session.add(complaint)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error adding complaint: {e}")
            return False
        finally:
            session.close()

    def get_unprocessed_complaints(self):
        session = self.Session()
        try:
            complaints = session.query(Complaint).filter_by(processed=ProcessStatus.PENDING).all()
            return complaints
        finally:
            session.close()

    def _determine_importance_level(self, complaint_category, description, root_cause, suggested_solution):
        """Determine importance level based on complaint analysis"""
        # Keywords that indicate high importance
        high_importance_keywords = [
            'safety', 'health', 'medical', 'surgical', 'critical', 'urgent', 
            'emergency', 'dangerous', 'harmful', 'injury', 'infection', 'contamination',
            'defective', 'broken', 'damaged', 'faulty', 'unsafe'
        ]
        
        # Keywords that indicate critical importance
        critical_keywords = [
            'life-threatening', 'death', 'fatal', 'severe injury', 'major safety',
            'recall', 'contamination', 'toxic', 'poisonous', 'explosive'
        ]
        
        # Check description and root cause for keywords
        text_to_check = f"{description} {root_cause} {suggested_solution}".lower()
        
        # Check for critical keywords first
        for keyword in critical_keywords:
            if keyword in text_to_check:
                return ImportanceLevel.CRITICAL
        
        # Check for high importance keywords
        high_count = sum(1 for keyword in high_importance_keywords if keyword in text_to_check)
        if high_count >= 2:
            return ImportanceLevel.HIGH
        
        # Category-based importance
        if complaint_category.lower() in ['safety issue', 'medical device', 'pharmaceutical']:
            return ImportanceLevel.HIGH
        
        # Default to medium for most cases
        return ImportanceLevel.MEDIUM

    def _should_auto_close(self, complaint_category, description, root_cause, suggested_solution):
        """Determine if a complaint should be automatically closed based on solution completeness"""
        # Keywords that indicate the issue has been resolved or solution is complete
        resolution_keywords = [
            'replaced', 'refunded', 'exchanged', 'fixed', 'resolved', 'completed',
            'delivered', 'shipped', 'corrected', 'addressed', 'handled', 'processed',
            'compensated', 'reimbursed', 'apologized', 'acknowledged', 'investigated'
        ]
        
        # Keywords that indicate immediate action was taken
        immediate_action_keywords = [
            'immediately', 'urgently', 'right away', 'asap', 'promptly',
            'dispatched', 'sent', 'issued', 'provided', 'offered'
        ]
        
        # Check if solution contains resolution keywords
        solution_text = f"{suggested_solution}".lower()
        
        # Count resolution keywords in the solution
        resolution_count = sum(1 for keyword in resolution_keywords if keyword in solution_text)
        immediate_count = sum(1 for keyword in immediate_action_keywords if keyword in solution_text)
        
        # Auto-close if there are multiple resolution keywords or immediate action keywords
        if resolution_count >= 2 or immediate_count >= 1:
            return True
        
        # Auto-close for certain categories that typically get quick resolution
        quick_resolution_categories = [
            'delivery issue', 'billing issue', 'order issue', 'product issue'
        ]
        
        if complaint_category.lower() in quick_resolution_categories and resolution_count >= 1:
            return True
        
        return False

    def update_complaint_analysis(self, complaint_id, root_cause, suggested_solution, importance_level=None):
        session = self.Session()
        try:
            complaint = session.query(Complaint).filter_by(id=complaint_id).first()
            if complaint:
                complaint.root_cause = root_cause
                complaint.suggested_solution = suggested_solution
                
                # Determine if complaint should be auto-closed
                should_close = self._should_auto_close(
                    complaint.complaint_category,
                    complaint.description,
                    root_cause,
                    suggested_solution
                )
                
                if should_close:
                    complaint.processed = ProcessStatus.CLOSED
                    self.logger.info(f"Auto-closing complaint {complaint_id} - solution provided")
                else:
                    complaint.processed = ProcessStatus.SUCCESSFUL
                
                complaint.processed_at = datetime.utcnow()
                
                # Determine importance level if not provided
                if importance_level is None:
                    importance_level = self._determine_importance_level(
                        complaint.complaint_category,
                        complaint.description,
                        root_cause,
                        suggested_solution
                    )
                
                # Convert string to enum if needed
                if isinstance(importance_level, str):
                    try:
                        importance_level = ImportanceLevel(importance_level)
                    except ValueError:
                        importance_level = ImportanceLevel.MEDIUM
                
                complaint.importance_level = importance_level
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Error updating complaint analysis: {e}")
            return False
        finally:
            session.close()

    def manually_close_complaint(self, complaint_id, closure_reason="Manually closed"):
        """Manually close a complaint"""
        session = self.Session()
        try:
            complaint = session.query(Complaint).filter_by(id=complaint_id).first()
            if complaint:
                complaint.processed = ProcessStatus.CLOSED
                complaint.processed_at = datetime.utcnow()
                # Add closure reason to suggested solution if not already present
                if not complaint.suggested_solution or "closed" not in complaint.suggested_solution.lower():
                    current_solution = complaint.suggested_solution or ""
                    complaint.suggested_solution = f"{current_solution}\n\n{closure_reason}"
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Error manually closing complaint: {e}")
            return False
        finally:
            session.close()

    def get_closed_complaints(self):
        """Get all closed complaints"""
        session = self.Session()
        try:
            complaints = session.query(Complaint).filter_by(processed=ProcessStatus.CLOSED).all()
            return complaints
        finally:
            session.close()

    def mark_complaint_failed(self, complaint_id, error_message):
        """Mark a complaint as failed processing"""
        session = self.Session()
        try:
            complaint = session.query(Complaint).filter_by(id=complaint_id).first()
            if complaint:
                complaint.processed = ProcessStatus.FAILED
                complaint.root_cause = "Processing Error"
                complaint.suggested_solution = error_message
                complaint.processed_at = datetime.utcnow()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Error marking complaint as failed: {e}")
            return False
        finally:
            session.close()

    def get_all_complaints(self):
        session = self.Session()
        try:
            return session.query(Complaint).all()
        finally:
            session.close() 