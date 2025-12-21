"""Database models using SQLAlchemy"""
from sqlalchemy import Column, String, Text, Float, DateTime, Boolean, JSON, Integer, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from datetime import datetime, timezone
import os
from contextlib import contextmanager


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


class Checkpoint(Base):
    """Checkpoint table for storing workflow state"""
    __tablename__ = "checkpoints"
    
    checkpoint_id = Column(String(255), primary_key=True)
    invoice_id = Column(String(255), nullable=False, index=True)
    workflow_id = Column(String(255), nullable=False, index=True)
    state_blob = Column(JSON, nullable=False)  # Complete workflow state
    paused_reason = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resumed_at = Column(DateTime, nullable=True)
    reviewer_id = Column(String(255), nullable=True)
    decision = Column(String(50), nullable=True)
    status = Column(String(50), default="PENDING", index=True)  # PENDING, RESOLVED, REJECTED


class HumanReviewQueue(Base):
    """Human review queue table"""
    __tablename__ = "human_review_queue"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    checkpoint_id = Column(String(255), unique=True, nullable=False, index=True)
    invoice_id = Column(String(255), nullable=False, index=True)
    vendor_name = Column(String(255))
    amount = Column(Float)
    reason_for_hold = Column(Text)
    review_url = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    reviewed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="PENDING", index=True)  # PENDING, APPROVED, REJECTED


class AuditLog(Base):
    """Audit logs table"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(String(255), nullable=False, index=True)
    invoice_id = Column(String(255), nullable=False, index=True)
    stage = Column(String(100), nullable=False)
    action = Column(String(255))
    details = Column(JSON)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


# Database initialization
def get_db_url():
    """Get database URL from environment or use default"""
    return os.getenv("DATABASE_URL", "sqlite:///./invoice_agent.db")


def init_db():
    """Initialize database and create all tables"""
    engine = create_engine(get_db_url(), echo=False)
    Base.metadata.create_all(engine)
    return engine


@contextmanager
def get_session():
    """Get database session with proper context manager for resource cleanup"""
    engine = create_engine(get_db_url(), echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()
