from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Complaint(Base):
    __tablename__ = 'complaints'

    id = Column(String(20), primary_key=True)
    sender = Column(String(100), nullable=False)
    subject = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    received_at = Column(DateTime, nullable=False)
    processed = Column(Boolean, default=False)
    root_cause = Column(Text)
    suggested_solution = Column(Text)
    processed_at = Column(DateTime)

class Database:
    def __init__(self, db_path='complaints.db'):
        self.engine = create_engine(f'sqlite:///{db_path}')
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
                existing.sender = complaint_data['sender']
                existing.subject = complaint_data['subject']
                existing.body = complaint_data['body']
                existing.received_at = datetime.fromisoformat(complaint_data['received_at'])
                existing.processed = False
                existing.root_cause = None
                existing.suggested_solution = None
                existing.processed_at = None
            else:
                # Create new complaint
                complaint = Complaint(
                    id=complaint_data['id'],
                    sender=complaint_data['sender'],
                    subject=complaint_data['subject'],
                    body=complaint_data['body'],
                    received_at=datetime.fromisoformat(complaint_data['received_at']),
                    processed=False
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
            complaints = session.query(Complaint).filter_by(processed=False).all()
            return complaints
        finally:
            session.close()

    def update_complaint_analysis(self, complaint_id, root_cause, suggested_solution):
        session = self.Session()
        try:
            complaint = session.query(Complaint).filter_by(id=complaint_id).first()
            if complaint:
                complaint.root_cause = root_cause
                complaint.suggested_solution = suggested_solution
                complaint.processed = True
                complaint.processed_at = datetime.utcnow()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Error updating complaint analysis: {e}")
            return False
        finally:
            session.close()

    def get_all_complaints(self):
        session = self.Session()
        try:
            return session.query(Complaint).all()
        finally:
            session.close() 