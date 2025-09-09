"""
SQLAlchemy models for OLIS Legislature Tracker
Corresponds to the PostgreSQL schema in postgres_schema.sql
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Date, Time, Text, 
    DECIMAL, ForeignKey, ARRAY, JSON, Index, UUID, func, text
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import expression
from datetime import datetime, date, time
from typing import Optional, List
import uuid

Base = declarative_base()

class SchemaVersion(Base):
    __tablename__ = 'schema_versions'
    
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    checksum: Mapped[Optional[str]] = mapped_column(Text)

class Company(Base):
    __tablename__ = 'companies'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    website: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    address_line1: Mapped[Optional[str]] = mapped_column(String(255))
    address_line2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(50))
    zip: Mapped[Optional[str]] = mapped_column(String(20))
    country: Mapped[str] = mapped_column(String(50), server_default='US')
    
    # Subscription & Access
    subscription_tier: Mapped[str] = mapped_column(String(50), server_default='basic')
    max_users: Mapped[int] = mapped_column(Integer, server_default='10')
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=expression.true())
    
    # Billing
    billing_contact_name: Mapped[Optional[str]] = mapped_column(String(255))
    billing_contact_email: Mapped[Optional[str]] = mapped_column(String(255))
    billing_contact_phone: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    users = relationship("User", back_populates="company")
    bill_priorities = relationship("CompanyBillPriority", back_populates="company")

class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    company_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    
    # Authentication
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    
    # Profile
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Access & Permissions
    role: Mapped[str] = mapped_column(String(50), server_default='user')
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=expression.true())
    is_company_admin: Mapped[bool] = mapped_column(Boolean, server_default=expression.false())
    
    # Authentication metadata
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    password_reset_token: Mapped[Optional[str]] = mapped_column(String(255))
    password_reset_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    login_count: Mapped[int] = mapped_column(Integer, server_default='0')
    
    # Preferences
    timezone: Mapped[str] = mapped_column(String(50), server_default='America/Los_Angeles')
    notification_preferences: Mapped[dict] = mapped_column(JSONB, server_default='{}')
    ui_preferences: Mapped[dict] = mapped_column(JSONB, server_default='{}')
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True))
    
    # Relationships
    company = relationship("Company", back_populates="users")
    tracked_measures = relationship("UserTrackedMeasure", back_populates="user")
    alerts = relationship("UserMeasureAlert", back_populates="user")
    saved_searches = relationship("SavedSearch", back_populates="user")
    activity_logs = relationship("UserActivityLog", back_populates="user")
    search_preferences = relationship("UserSearchPreference", back_populates="user", uselist=False)

class LegislativeSession(Base):
    __tablename__ = 'legislative_sessions'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    
    # OLIS Fields
    session_key: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    session_name: Mapped[str] = mapped_column(String(100), nullable=False)
    session_type: Mapped[Optional[str]] = mapped_column(String(50))
    session_year: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Dates
    begin_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    
    # Status
    is_current: Mapped[bool] = mapped_column(Boolean, server_default=expression.false())
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=expression.true())
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sync_status: Mapped[str] = mapped_column(String(50), server_default='pending')
    
    # Relationships
    committees = relationship("Committee", back_populates="session")
    measures = relationship("Measure", back_populates="session")

class Committee(Base):
    __tablename__ = 'committees'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    session_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('legislative_sessions.id'), nullable=False)
    
    # Committee identification
    committee_code: Mapped[str] = mapped_column(String(20), nullable=False)
    committee_name: Mapped[str] = mapped_column(String(255), nullable=False)
    chamber: Mapped[Optional[str]] = mapped_column(String(20))
    committee_type: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Details
    description: Mapped[Optional[str]] = mapped_column(Text)
    chair_name: Mapped[Optional[str]] = mapped_column(String(255))
    vice_chair_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=expression.true())
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    session = relationship("LegislativeSession", back_populates="committees")
    measures = relationship("Measure", back_populates="current_committee")
    meetings = relationship("CommitteeMeeting", back_populates="committee")

class Measure(Base):
    __tablename__ = 'measures'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    session_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('legislative_sessions.id'), nullable=False)
    
    # OLIS Identification Fields
    session_key: Mapped[str] = mapped_column(String(10), nullable=False)
    measure_prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    measure_number: Mapped[int] = mapped_column(Integer, nullable=False)
    prefix_meaning: Mapped[Optional[str]] = mapped_column(String(255))
    lc_number: Mapped[Optional[int]] = mapped_column(Integer)
    chapter_number: Mapped[Optional[int]] = mapped_column(Integer)
    
    # OLIS Content Fields
    measure_summary: Mapped[Optional[str]] = mapped_column(Text)
    catch_line: Mapped[Optional[str]] = mapped_column(Text)
    minority_catch_line: Mapped[Optional[str]] = mapped_column(Text)
    relating_to: Mapped[Optional[str]] = mapped_column(Text)
    relating_to_full: Mapped[Optional[str]] = mapped_column(Text)
    at_the_request_of: Mapped[Optional[str]] = mapped_column(Text)
    
    # OLIS Status & Location Fields
    current_location: Mapped[Optional[str]] = mapped_column(String(500))
    current_version: Mapped[Optional[str]] = mapped_column(String(50))
    
    # OLIS Committee Fields
    current_committee_code: Mapped[Optional[str]] = mapped_column(String(20))
    current_subcommittee: Mapped[Optional[str]] = mapped_column(String(255))
    
    # OLIS Date/Time Fields
    created_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    modified_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    effective_date: Mapped[Optional[date]] = mapped_column(Date)
    
    # OLIS Other Fields
    fiscal_impact: Mapped[Optional[str]] = mapped_column(Text)
    revenue_impact: Mapped[Optional[str]] = mapped_column(Text)
    fiscal_analyst: Mapped[Optional[str]] = mapped_column(String(255))
    revenue_economist: Mapped[Optional[str]] = mapped_column(String(255))
    emergency_clause: Mapped[bool] = mapped_column(Boolean, server_default=expression.false())
    vetoed: Mapped[bool] = mapped_column(Boolean, server_default=expression.false())
    
    # Additional computed/derived fields
    bill_number: Mapped[Optional[str]] = mapped_column(String(20))  # Generated column in SQL
    chamber: Mapped[Optional[str]] = mapped_column(String(20))
    bill_type: Mapped[Optional[str]] = mapped_column(String(50))
    status_category: Mapped[Optional[str]] = mapped_column(String(50))
    priority_score: Mapped[int] = mapped_column(Integer, server_default='0')
    
    # Foreign key references
    current_committee_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('committees.id'))
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sync_status: Mapped[str] = mapped_column(String(50), server_default='pending')
    
    # Relationships
    session = relationship("LegislativeSession", back_populates="measures")
    current_committee = relationship("Committee", back_populates="measures")
    sponsors = relationship("MeasureSponsor", back_populates="measure")
    testimonies = relationship("Testimony", back_populates="measure")
    user_tracked = relationship("UserTrackedMeasure", back_populates="measure")
    alerts = relationship("UserMeasureAlert", back_populates="measure")
    company_priorities = relationship("CompanyBillPriority", back_populates="measure")
    
    # Indexes
    __table_args__ = (
        Index('idx_measures_unique', 'session_key', 'measure_prefix', 'measure_number', unique=True),
    )

class MeasureSponsor(Base):
    __tablename__ = 'measure_sponsors'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    measure_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id', ondelete='CASCADE'), nullable=False)
    
    # Sponsor details
    sponsor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sponsor_type: Mapped[Optional[str]] = mapped_column(String(50))
    chamber: Mapped[Optional[str]] = mapped_column(String(20))
    district: Mapped[Optional[str]] = mapped_column(String(10))
    party: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Order/priority
    sponsor_order: Mapped[int] = mapped_column(Integer, server_default='0')
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    measure = relationship("Measure", back_populates="sponsors")

class CommitteeMeeting(Base):
    __tablename__ = 'committee_meetings'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    committee_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('committees.id'), nullable=False)
    
    # Meeting details
    meeting_date: Mapped[date] = mapped_column(Date, nullable=False)
    meeting_time: Mapped[Optional[time]] = mapped_column(Time)
    location: Mapped[Optional[str]] = mapped_column(String(255))
    meeting_type: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Status
    is_cancelled: Mapped[bool] = mapped_column(Boolean, server_default=expression.false())
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    committee = relationship("Committee", back_populates="meetings")
    testimonies = relationship("Testimony", back_populates="meeting")

class Testimony(Base):
    __tablename__ = 'testimonies'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    measure_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id', ondelete='CASCADE'), nullable=False)
    meeting_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('committee_meetings.id'))
    
    # Testimony details
    testifier_name: Mapped[Optional[str]] = mapped_column(String(255))
    testifier_organization: Mapped[Optional[str]] = mapped_column(String(255))
    testifier_title: Mapped[Optional[str]] = mapped_column(String(255))
    testifier_city: Mapped[Optional[str]] = mapped_column(String(100))
    testifier_state: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Position
    position_code: Mapped[Optional[int]] = mapped_column(Integer)  # 3981=neutral, 3982=favor, 3983=against
    position_text: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Testimony content
    testimony_text: Mapped[Optional[str]] = mapped_column(Text)
    testimony_summary: Mapped[Optional[str]] = mapped_column(Text)
    
    # Meeting context
    meeting_date: Mapped[Optional[date]] = mapped_column(Date)
    committee_code: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Analysis
    sentiment_score: Mapped[Optional[float]] = mapped_column(DECIMAL(3,2))
    key_points: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    measure = relationship("Measure", back_populates="testimonies")
    meeting = relationship("CommitteeMeeting", back_populates="testimonies")

# User-specific tables
class UserTrackedMeasure(Base):
    __tablename__ = 'user_tracked_measures'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    measure_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id', ondelete='CASCADE'), nullable=False)
    
    # Tracking preferences
    tracking_reason: Mapped[Optional[str]] = mapped_column(String(255))
    priority_level: Mapped[str] = mapped_column(String(20), server_default='medium')
    
    # Notification preferences
    notify_on_status_change: Mapped[bool] = mapped_column(Boolean, server_default=expression.true())
    notify_on_committee_action: Mapped[bool] = mapped_column(Boolean, server_default=expression.true())
    notify_on_new_testimony: Mapped[bool] = mapped_column(Boolean, server_default=expression.false())
    notify_on_amendments: Mapped[bool] = mapped_column(Boolean, server_default=expression.false())
    
    # User notes
    private_notes: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[List[str]] = mapped_column(JSONB, server_default='[]')
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_viewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="tracked_measures")
    measure = relationship("Measure", back_populates="user_tracked")
    
    __table_args__ = (
        Index('idx_user_tracked_unique', 'user_id', 'measure_id', unique=True),
    )

class UserMeasureAlert(Base):
    __tablename__ = 'user_measure_alerts'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    measure_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id', ondelete='CASCADE'), nullable=False)
    
    # Alert criteria
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    alert_title: Mapped[str] = mapped_column(String(255), nullable=False)
    alert_message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Alert metadata
    is_read: Mapped[bool] = mapped_column(Boolean, server_default=expression.false())
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sent_email: Mapped[bool] = mapped_column(Boolean, server_default=expression.false())
    sent_email_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Reference data
    old_value: Mapped[Optional[str]] = mapped_column(Text)
    new_value: Mapped[Optional[str]] = mapped_column(Text)
    change_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    measure = relationship("Measure", back_populates="alerts")

class UserSearchPreference(Base):
    __tablename__ = 'user_search_preferences'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Default search filters
    default_session_keys: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    default_chambers: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    default_bill_types: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    default_committees: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    
    # Hot bills criteria
    hot_bills_min_testimonies: Mapped[int] = mapped_column(Integer, server_default='5')
    hot_bills_weight_recent: Mapped[float] = mapped_column(DECIMAL(3,2), server_default='1.0')
    hot_bills_weight_testimony: Mapped[float] = mapped_column(DECIMAL(3,2), server_default='0.8')
    hot_bills_weight_amendments: Mapped[float] = mapped_column(DECIMAL(3,2), server_default='0.6')
    
    # Display preferences
    results_per_page: Mapped[int] = mapped_column(Integer, server_default='25')
    default_sort_order: Mapped[str] = mapped_column(String(50), server_default='relevance')
    show_bill_summaries: Mapped[bool] = mapped_column(Boolean, server_default=expression.true())
    show_fiscal_impact: Mapped[bool] = mapped_column(Boolean, server_default=expression.true())
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="search_preferences")

class SavedSearch(Base):
    __tablename__ = 'saved_searches'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Search details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    search_criteria: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Notifications
    notify_on_new_results: Mapped[bool] = mapped_column(Boolean, server_default=expression.false())
    last_notification_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Usage
    use_count: Mapped[int] = mapped_column(Integer, server_default='0')
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Sharing
    is_shared: Mapped[bool] = mapped_column(Boolean, server_default=expression.false())
    shared_with_company: Mapped[bool] = mapped_column(Boolean, server_default=expression.false())
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="saved_searches")

class CompanyBillPriority(Base):
    __tablename__ = 'company_bill_priorities'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    company_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    measure_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id', ondelete='CASCADE'), nullable=False)
    
    # Priority details
    priority_level: Mapped[str] = mapped_column(String(20), nullable=False)
    priority_reason: Mapped[Optional[str]] = mapped_column(Text)
    assigned_to_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id'))
    
    # Client/project association
    client_name: Mapped[Optional[str]] = mapped_column(String(255))
    project_name: Mapped[Optional[str]] = mapped_column(String(255))
    billing_code: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Status tracking
    status: Mapped[str] = mapped_column(String(50), server_default='active')
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id'))
    
    # Relationships
    company = relationship("Company", back_populates="bill_priorities")
    measure = relationship("Measure", back_populates="company_priorities")
    assigned_to_user = relationship("User", foreign_keys=[assigned_to_user_id])
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    
    __table_args__ = (
        Index('idx_company_priorities_unique', 'company_id', 'measure_id', unique=True),
    )

class UserActivityLog(Base):
    __tablename__ = 'user_activity_log'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Activity details
    activity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    activity_description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Context
    measure_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id'))
    search_query: Mapped[Optional[str]] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    
    # Metadata
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="activity_logs")

class SyncJob(Base):
    __tablename__ = 'sync_jobs'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    
    # Job details
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), server_default='pending')
    
    # Parameters
    session_keys: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    sync_measures: Mapped[bool] = mapped_column(Boolean, server_default=expression.true())
    sync_testimony: Mapped[bool] = mapped_column(Boolean, server_default=expression.true())
    sync_committees: Mapped[bool] = mapped_column(Boolean, server_default=expression.true())
    
    # Progress tracking
    total_items: Mapped[Optional[int]] = mapped_column(Integer)
    processed_items: Mapped[int] = mapped_column(Integer, server_default='0')
    failed_items: Mapped[int] = mapped_column(Integer, server_default='0')
    
    # Results
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    sync_summary: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id'))