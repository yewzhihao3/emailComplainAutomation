from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum
import logging
import sqlite3
import os
from typing import List, Optional

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
    def __init__(self, db_path='data/complaints.db'):
        # Create data folder if it doesn't exist
        data_folder = os.path.dirname(db_path)
        if data_folder and not os.path.exists(data_folder):
            os.makedirs(data_folder)
        
        self.db_path = db_path
        self.init_database()
        self.logger = logging.getLogger(__name__)

    def init_database(self):
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

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

    def get_next_complaint_id(self):
        """Get the next available complaint ID for sequential numbering"""
        session = self.Session()
        try:
            # Get the highest complaint ID number
            highest_id = session.query(Complaint.id).order_by(Complaint.id.desc()).first()
            
            if highest_id:
                # Extract the number from the highest ID (e.g., "COMP-000123" -> 123)
                try:
                    current_number = int(highest_id[0].split('-')[1])
                    next_number = current_number + 1
                except (IndexError, ValueError):
                    # If parsing fails, start from 1
                    next_number = 1
            else:
                # No complaints in database, start from 1
                next_number = 1
            
            return f"COMP-{next_number:06d}"
        finally:
            session.close()

    def add_complaint(self, complaint_data):
        session = self.Session()
        try:
            # Check if complaint already exists by order_id (more reliable than id)
            existing = None
            if complaint_data.get('order_id'):
                existing = session.query(Complaint).filter_by(order_id=complaint_data['order_id']).first()
            
            # If not found by order_id, check by id as fallback
            if not existing:
                existing = session.query(Complaint).filter_by(id=complaint_data['id']).first()
            
            if existing:
                # Update existing complaint with new data but preserve processing status
                self.logger.info(f"Complaint with order_id {complaint_data.get('order_id')} already exists, skipping")
                return "skipped"  # Return "skipped" to indicate existing complaint
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
                self.logger.info(f"Added new complaint {complaint_data['id']} to database")
                return "added"  # Return "added" to indicate new complaint
        except Exception as e:
            session.rollback()
            self.logger.error(f"Error adding complaint: {e}")
            return False  # Return False to indicate error
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

    def get_database_stats(self):
        """Get statistics about the complaints database"""
        session = self.Session()
        try:
            total_complaints = session.query(Complaint).count()
            pending_complaints = session.query(Complaint).filter_by(processed=ProcessStatus.PENDING).count()
            successful_complaints = session.query(Complaint).filter_by(processed=ProcessStatus.SUCCESSFUL).count()
            failed_complaints = session.query(Complaint).filter_by(processed=ProcessStatus.FAILED).count()
            
            return {
                'total': total_complaints,
                'pending': pending_complaints,
                'successful': successful_complaints,
                'failed': failed_complaints,
                'processed_percentage': round((successful_complaints + failed_complaints) / total_complaints * 100, 2) if total_complaints > 0 else 0
            }
        finally:
            session.close()

    def get_complaint_by_order_id(self, order_id):
        """Get a complaint by order_id"""
        if not order_id:
            return None
        session = self.Session()
        try:
            return session.query(Complaint).filter_by(order_id=order_id).first()
        finally:
            session.close() 