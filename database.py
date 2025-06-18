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
            self.logger.error(f"Error clearing database: {e}")
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
            self.logger.error(f"Error adding complaint: {e}")
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
        # This function can remain for future use, but auto-close will just mark as SUCCESSFUL
        return False

    def update_complaint_analysis(self, complaint_id, root_cause, suggested_solution, importance_level=None):
        session = self.Session()
        try:
            complaint = session.query(Complaint).filter_by(id=complaint_id).first()
            if complaint:
                complaint.root_cause = root_cause
                complaint.suggested_solution = suggested_solution
                complaint.processed = ProcessStatus.SUCCESSFUL
                complaint.processed_at = datetime.utcnow()
                # ... importance level logic ...
                if importance_level is None:
                    importance_level = self._determine_importance_level(
                        complaint.complaint_category,
                        complaint.description,
                        root_cause,
                        suggested_solution
                    )
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
            self.logger.error(f"Error updating complaint analysis: {e}")
            return False
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
            self.logger.error(f"Error marking complaint as failed: {e}")
            return False
        finally:
            session.close()

    def get_all_complaints(self):
        session = self.Session()
        try:
            return session.query(Complaint).all()
        finally:
            session.close() 