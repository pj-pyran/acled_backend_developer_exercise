import logging
logger = logging.getLogger(__name__)

'''SQLAlchemy ORM models'''
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Index, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.database import Base


class ConflictData(Base):
    '''Conflict data model for countries and admin1 regions'''
    __tablename__ = 'conflict_data'

    id = Column(Integer, primary_key=True, index=True)
    country = Column(String(100), index=True, nullable=False)
    admin1 = Column(String(100), index=True, nullable=False)
    population = Column(Integer, nullable=True)
    events = Column(Integer, nullable=False)
    risk_score = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    feedback = relationship('UserFeedback', back_populates='conflict_data', cascade='all, delete-orphan')

    # Indexes for efficient queries and enforce uniqueness
    __table_args__ = (
        Index('idx_country_admin1', 'country', 'admin1', unique=True),
    )



class User(Base):
    '''User model for authentication'''
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(500), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    feedback = relationship('UserFeedback', back_populates='user', cascade='all, delete-orphan')


class UserFeedback(Base):
    '''User feedback model for admin1 regions'''
    __tablename__ = 'user_feedback'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    conflict_data_id = Column(Integer, ForeignKey('conflict_data.id', ondelete='CASCADE'), nullable=False, index=True)
    feedback_text = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    user = relationship('User', back_populates='feedback')
    conflict_data = relationship('ConflictData', back_populates='feedback')