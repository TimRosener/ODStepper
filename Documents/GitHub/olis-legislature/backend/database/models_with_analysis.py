"""
SQLAlchemy ORM Models for OLIS Legislature Tracker with Analysis Framework
Enhanced version with extensible analysis capabilities
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, List, Any
import uuid
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, Date, DateTime, 
    ForeignKey, UniqueConstraint, Index, DECIMAL, Numeric,
    text, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, INET
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

Base = declarative_base()

# ============================================================================
# COMPANY & USER MANAGEMENT
# ============================================================================

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
    max_users: Mapped[int] = mapped_column(Integer, server_default=text('10'))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text('TRUE'))
    
    # Billing
    billing_contact_name: Mapped[Optional[str]] = mapped_column(String(255))
    billing_contact_email: Mapped[Optional[str]] = mapped_column(String(255))
    billing_contact_phone: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="company", cascade="all, delete-orphan")
    bill_priorities: Mapped[List["CompanyBillPriority"]] = relationship("CompanyBillPriority", back_populates="company")


class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    company_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('companies.id'), nullable=False)
    
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
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text('TRUE'))
    is_company_admin: Mapped[bool] = mapped_column(Boolean, server_default=text('FALSE'))
    
    # Authentication metadata
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    password_reset_token: Mapped[Optional[str]] = mapped_column(String(255))
    password_reset_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    login_count: Mapped[int] = mapped_column(Integer, server_default=text('0'))
    
    # Preferences
    timezone: Mapped[str] = mapped_column(String(50), server_default='America/Los_Angeles')
    notification_preferences: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    ui_preferences: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True))
    
    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="users")
    tracked_measures: Mapped[List["UserTrackedMeasure"]] = relationship("UserTrackedMeasure", back_populates="user")
    alerts: Mapped[List["UserMeasureAlert"]] = relationship("UserMeasureAlert", back_populates="user")
    activity_logs: Mapped[List["UserActivityLog"]] = relationship("UserActivityLog", back_populates="user")


# ============================================================================
# OLIS DATA MIRRORING
# ============================================================================

class LegislativeSession(Base):
    __tablename__ = 'legislative_sessions'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    
    # OLIS Fields
    session_key: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    session_name: Mapped[str] = mapped_column(String(100), nullable=False)
    session_type: Mapped[Optional[str]] = mapped_column(String(50))
    session_year: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Dates
    begin_date: Mapped[Optional[datetime]] = mapped_column(Date)
    end_date: Mapped[Optional[datetime]] = mapped_column(Date)
    
    # Status
    is_current: Mapped[bool] = mapped_column(Boolean, server_default=text('FALSE'))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text('TRUE'))
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sync_status: Mapped[str] = mapped_column(String(50), server_default='pending')
    
    # Relationships
    measures: Mapped[List["Measure"]] = relationship("Measure", back_populates="session")
    committees: Mapped[List["Committee"]] = relationship("Committee", back_populates="session")


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
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text('TRUE'))
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    session: Mapped["LegislativeSession"] = relationship("LegislativeSession", back_populates="committees")
    measures: Mapped[List["Measure"]] = relationship("Measure", back_populates="current_committee")


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
    current_committee_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('committees.id'))
    
    # OLIS Date/Time Fields
    created_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    modified_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    effective_date: Mapped[Optional[datetime]] = mapped_column(Date)
    
    # OLIS Other Fields
    fiscal_impact: Mapped[Optional[str]] = mapped_column(Text)
    revenue_impact: Mapped[Optional[str]] = mapped_column(Text)
    fiscal_analyst: Mapped[Optional[str]] = mapped_column(String(255))
    revenue_economist: Mapped[Optional[str]] = mapped_column(String(255))
    emergency_clause: Mapped[bool] = mapped_column(Boolean, server_default=text('FALSE'))
    vetoed: Mapped[bool] = mapped_column(Boolean, server_default=text('FALSE'))
    
    # Additional fields
    chamber: Mapped[Optional[str]] = mapped_column(String(20))
    bill_type: Mapped[Optional[str]] = mapped_column(String(50))
    status_category: Mapped[Optional[str]] = mapped_column(String(50))
    priority_score: Mapped[int] = mapped_column(Integer, server_default=text('0'))
    
    # NEW: Analysis metadata fields
    analysis_metadata: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    last_comprehensive_analysis: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    analysis_flags: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    ai_insights: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sync_status: Mapped[str] = mapped_column(String(50), server_default='pending')
    
    # Relationships
    session: Mapped["LegislativeSession"] = relationship("LegislativeSession", back_populates="measures")
    current_committee: Mapped[Optional["Committee"]] = relationship("Committee", back_populates="measures")
    testimonies: Mapped[List["Testimony"]] = relationship("Testimony", back_populates="measure")
    sponsors: Mapped[List["MeasureSponsor"]] = relationship("MeasureSponsor", back_populates="measure")
    tracked_by_users: Mapped[List["UserTrackedMeasure"]] = relationship("UserTrackedMeasure", back_populates="measure")
    analyses: Mapped[List["MeasureAnalysis"]] = relationship("MeasureAnalysis", back_populates="measure")
    amendments: Mapped[List["Amendment"]] = relationship("Amendment", back_populates="measure")


class Testimony(Base):
    __tablename__ = 'testimonies'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    measure_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id'), nullable=False)
    meeting_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True))
    
    # Testimony details
    testifier_name: Mapped[Optional[str]] = mapped_column(String(255))
    testifier_organization: Mapped[Optional[str]] = mapped_column(String(255))
    testifier_title: Mapped[Optional[str]] = mapped_column(String(255))
    testifier_city: Mapped[Optional[str]] = mapped_column(String(100))
    testifier_state: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Position
    position_code: Mapped[Optional[int]] = mapped_column(Integer)  # 3981=neutral, 3982=in_favor, 3983=against
    position_text: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Testimony content
    testimony_text: Mapped[Optional[str]] = mapped_column(Text)
    testimony_summary: Mapped[Optional[str]] = mapped_column(Text)
    
    # Meeting context
    meeting_date: Mapped[Optional[datetime]] = mapped_column(Date)
    committee_code: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Analysis fields
    sentiment_score: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(3,2))
    emotion_scores: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    key_points: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    
    # NEW: Advanced analysis fields
    analysis_version: Mapped[Optional[int]] = mapped_column(Integer)
    analysis_metadata: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    extracted_entities: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    policy_recommendations: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    stakeholder_classification: Mapped[Optional[str]] = mapped_column(String(100))
    credibility_indicators: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    measure: Mapped["Measure"] = relationship("Measure", back_populates="testimonies")


# ============================================================================
# NEW: EXTENSIBLE ANALYSIS FRAMEWORK
# ============================================================================

class AnalysisType(Base):
    __tablename__ = 'analysis_types'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    
    # Type definition
    type_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    type_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Configuration
    default_parameters: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    required_fields: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    output_schema: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # AI/ML Configuration
    default_model: Mapped[Optional[str]] = mapped_column(String(100))
    default_prompt_template: Mapped[Optional[str]] = mapped_column(Text)
    confidence_threshold: Mapped[Decimal] = mapped_column(DECIMAL(3,2), server_default=text('0.7'))
    
    # Scheduling
    auto_analyze: Mapped[bool] = mapped_column(Boolean, server_default=text('FALSE'))
    analysis_frequency: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text('TRUE'))
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id'))
    
    # Relationships
    analyses: Mapped[List["MeasureAnalysis"]] = relationship("MeasureAnalysis", back_populates="analysis_type")
    configurations: Mapped[List["AnalysisConfiguration"]] = relationship("AnalysisConfiguration", back_populates="analysis_type")


class MeasureAnalysis(Base):
    __tablename__ = 'measure_analyses'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    measure_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id'), nullable=False)
    analysis_type_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('analysis_types.id'), nullable=False)
    
    # Analysis versioning
    analysis_version: Mapped[int] = mapped_column(Integer, server_default=text('1'))
    is_current_version: Mapped[bool] = mapped_column(Boolean, server_default=text('TRUE'))
    
    # Analysis content
    raw_analysis: Mapped[Optional[dict]] = mapped_column(JSONB)
    structured_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    key_findings: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    
    # Confidence and quality
    confidence_scores: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    overall_confidence: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(3,2))
    quality_score: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(3,2))
    
    # Analysis metadata
    ai_model_used: Mapped[Optional[str]] = mapped_column(String(100))
    prompt_version: Mapped[Optional[str]] = mapped_column(String(50))
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    token_count: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Who/what performed it
    performed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id'))
    performed_by_system: Mapped[bool] = mapped_column(Boolean, server_default=text('FALSE'))
    
    # Status
    status: Mapped[str] = mapped_column(String(50), server_default='completed')
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    measure: Mapped["Measure"] = relationship("Measure", back_populates="analyses")
    analysis_type: Mapped["AnalysisType"] = relationship("AnalysisType", back_populates="analyses")
    performed_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[performed_by_user_id])


class Amendment(Base):
    __tablename__ = 'amendments'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    measure_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id'), nullable=False)
    
    # Amendment identification
    amendment_number: Mapped[Optional[str]] = mapped_column(String(50))
    amendment_type: Mapped[Optional[str]] = mapped_column(String(50))
    sponsor_name: Mapped[Optional[str]] = mapped_column(String(255))
    sponsor_type: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Content
    original_text: Mapped[Optional[str]] = mapped_column(Text)
    amended_text: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Status
    status: Mapped[Optional[str]] = mapped_column(String(50))
    action_date: Mapped[Optional[datetime]] = mapped_column(Date)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    measure: Mapped["Measure"] = relationship("Measure", back_populates="amendments")
    analyses: Mapped[List["AmendmentAnalysis"]] = relationship("AmendmentAnalysis", back_populates="amendment")


class AmendmentAnalysis(Base):
    __tablename__ = 'amendment_analyses'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    amendment_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('amendments.id'), nullable=False)
    measure_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id'), nullable=False)
    
    # Analysis content
    change_summary: Mapped[Optional[str]] = mapped_column(Text)
    change_impact_analysis: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    stakeholder_impact: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    fiscal_impact_delta: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2))
    legal_implications: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    
    # Comparison metrics
    text_similarity_score: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(3,2))
    substantive_change_score: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(3,2))
    
    # AI Analysis
    ai_interpretation: Mapped[Optional[str]] = mapped_column(Text)
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(3,2))
    analysis_metadata: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    
    # Metadata
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    analyzed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id'))
    analysis_version: Mapped[int] = mapped_column(Integer, server_default=text('1'))
    
    # Relationships
    amendment: Mapped["Amendment"] = relationship("Amendment", back_populates="analyses")
    analyzed_by: Mapped[Optional["User"]] = relationship("User")


class AnalysisConfiguration(Base):
    __tablename__ = 'analysis_configurations'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    analysis_type_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('analysis_types.id'), nullable=False)
    
    # Configuration details
    config_name: Mapped[str] = mapped_column(String(255), nullable=False)
    config_version: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text('TRUE'))
    
    # Prompts and parameters
    prompt_template: Mapped[Optional[str]] = mapped_column(Text)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text)
    parameters: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    preprocessing_steps: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    postprocessing_steps: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    
    # Thresholds and rules
    confidence_threshold: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(3,2))
    quality_threshold: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(3,2))
    validation_rules: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    
    # A/B Testing
    is_experiment: Mapped[bool] = mapped_column(Boolean, server_default=text('FALSE'))
    experiment_group: Mapped[Optional[str]] = mapped_column(String(50))
    experiment_metrics: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id'))
    
    # Relationships
    analysis_type: Mapped["AnalysisType"] = relationship("AnalysisType", back_populates="configurations")
    created_by: Mapped[Optional["User"]] = relationship("User")


class AnalysisHistory(Base):
    __tablename__ = 'analysis_history'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    
    # What was analyzed
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    analysis_type_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('analysis_types.id'))
    
    # Analysis details
    analysis_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True))
    config_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('analysis_configurations.id'))
    
    # Performance metrics
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    token_count: Mapped[Optional[int]] = mapped_column(Integer)
    cost_estimate: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10,4))
    
    # Results summary
    success: Mapped[Optional[bool]] = mapped_column(Boolean)
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(3,2))
    key_metrics: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    error_details: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Who/what triggered it
    triggered_by: Mapped[Optional[str]] = mapped_column(String(50))
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id'))
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    analysis_type: Mapped[Optional["AnalysisType"]] = relationship("AnalysisType")
    config: Mapped[Optional["AnalysisConfiguration"]] = relationship("AnalysisConfiguration")
    user: Mapped[Optional["User"]] = relationship("User")


# ============================================================================
# USER PREFERENCES & TRACKING
# ============================================================================

class UserTrackedMeasure(Base):
    __tablename__ = 'user_tracked_measures'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    measure_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id'), nullable=False)
    
    # Tracking preferences
    tracking_reason: Mapped[Optional[str]] = mapped_column(String(255))
    priority_level: Mapped[str] = mapped_column(String(20), server_default='medium')
    
    # Notification preferences
    notify_on_status_change: Mapped[bool] = mapped_column(Boolean, server_default=text('TRUE'))
    notify_on_committee_action: Mapped[bool] = mapped_column(Boolean, server_default=text('TRUE'))
    notify_on_new_testimony: Mapped[bool] = mapped_column(Boolean, server_default=text('FALSE'))
    notify_on_amendments: Mapped[bool] = mapped_column(Boolean, server_default=text('FALSE'))
    notify_on_new_analysis: Mapped[bool] = mapped_column(Boolean, server_default=text('TRUE'))
    
    # User notes
    private_notes: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    
    # NEW: Analysis preferences
    preferred_analysis_types: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    analysis_frequency: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_viewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tracked_measures")
    measure: Mapped["Measure"] = relationship("Measure", back_populates="tracked_by_users")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'measure_id', name='idx_user_tracked_unique'),
    )


class UserMeasureAlert(Base):
    __tablename__ = 'user_measure_alerts'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    measure_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id'), nullable=False)
    
    # Alert criteria
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    alert_title: Mapped[str] = mapped_column(String(255), nullable=False)
    alert_message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Alert metadata
    is_read: Mapped[bool] = mapped_column(Boolean, server_default=text('FALSE'))
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sent_email: Mapped[bool] = mapped_column(Boolean, server_default=text('FALSE'))
    sent_email_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Reference data
    old_value: Mapped[Optional[str]] = mapped_column(Text)
    new_value: Mapped[Optional[str]] = mapped_column(Text)
    change_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="alerts")
    measure: Mapped["Measure"] = relationship("Measure")


# ============================================================================
# SUPPORTING TABLES
# ============================================================================

class MeasureSponsor(Base):
    __tablename__ = 'measure_sponsors'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    session_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('legislative_sessions.id'), nullable=False)
    measure_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id'), nullable=False)
    legislator_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('legislators.id'))
    
    # OLIS identifiers
    measure_sponsor_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    session_key: Mapped[str] = mapped_column(String(20), nullable=False)
    measure_prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    measure_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Sponsor details
    sponsor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sponsor_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "Primary", "Co-Sponsor"
    chamber: Mapped[Optional[str]] = mapped_column(String(20))
    district: Mapped[Optional[str]] = mapped_column(String(10))
    party: Mapped[Optional[str]] = mapped_column(String(50))
    legislator_code: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Order/priority
    sponsor_order: Mapped[int] = mapped_column(Integer, server_default=text('0'))
    
    # OLIS metadata
    olis_created_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    olis_modified_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Sync metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Constraints
    __table_args__ = (
        Index('idx_sponsor_session', 'session_key'),
        Index('idx_sponsor_measure', 'measure_prefix', 'measure_number'),
        Index('idx_sponsor_legislator', 'legislator_code'),
        Index('idx_sponsor_type', 'sponsor_type'),
    )
    
    # Relationships
    session: Mapped["LegislativeSession"] = relationship("LegislativeSession")
    measure: Mapped["Measure"] = relationship("Measure", back_populates="sponsors")
    legislator: Mapped[Optional["Legislator"]] = relationship("Legislator")


class CompanyBillPriority(Base):
    __tablename__ = 'company_bill_priorities'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    company_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('companies.id'), nullable=False)
    measure_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id'), nullable=False)
    
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
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id'))
    
    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="bill_priorities")
    measure: Mapped["Measure"] = relationship("Measure")
    assigned_to: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to_user_id])
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_user_id])
    
    __table_args__ = (
        UniqueConstraint('company_id', 'measure_id', name='idx_company_priorities_unique'),
    )


class UserActivityLog(Base):
    __tablename__ = 'user_activity_log'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Activity details
    activity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    activity_description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Context
    measure_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id'))
    search_query: Mapped[Optional[str]] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    
    # Activity metadata
    activity_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="activity_logs")
    measure: Mapped[Optional["Measure"]] = relationship("Measure")


# ============================================================================
# PHASE 1: LEGISLATORS & VOTING DATA 
# ============================================================================

class Legislator(Base):
    __tablename__ = 'legislators'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    session_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('legislative_sessions.id'), nullable=False)
    
    # OLIS identifiers
    session_key: Mapped[str] = mapped_column(String(20), nullable=False)
    legislator_code: Mapped[str] = mapped_column(String(100), nullable=False)  # "Rep Andersen"
    
    # Personal information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(50))  # "Representative"
    chamber: Mapped[str] = mapped_column(String(10))  # "H" or "S"
    party: Mapped[Optional[str]] = mapped_column(String(50))  # "Democrat"
    district_number: Mapped[Optional[str]] = mapped_column(String(10))  # "19"
    
    # Contact information
    capitol_address: Mapped[Optional[str]] = mapped_column(Text)
    capitol_phone: Mapped[Optional[str]] = mapped_column(String(50))
    email_address: Mapped[Optional[str]] = mapped_column(String(255))
    website_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # OLIS metadata
    olis_created_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    olis_modified_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Sync metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('session_key', 'legislator_code', name='uq_legislator_session_code'),
        Index('idx_legislator_session_key', 'session_key'),
        Index('idx_legislator_chamber', 'chamber'),
        Index('idx_legislator_party', 'party'),
    )
    
    # Relationships
    session: Mapped["LegislativeSession"] = relationship("LegislativeSession")
    committee_memberships: Mapped[List["CommitteeMember"]] = relationship("CommitteeMember", back_populates="legislator")
    measure_votes: Mapped[List["MeasureVote"]] = relationship("MeasureVote", back_populates="legislator")
    committee_votes: Mapped[List["CommitteeVote"]] = relationship("CommitteeVote", back_populates="legislator")


class MeasureVote(Base):
    __tablename__ = 'measure_votes'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    session_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('legislative_sessions.id'), nullable=False)
    measure_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id'), nullable=False)
    legislator_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('legislators.id'), nullable=False)
    
    # OLIS identifiers
    measure_vote_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)  # OLIS ID
    measure_history_id: Mapped[Optional[int]] = mapped_column(Integer)
    session_key: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Measure reference
    measure_prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    measure_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Vote details
    vote: Mapped[str] = mapped_column(String(50), nullable=False)  # "Aye", "Nay", "Excused"
    vote_name: Mapped[str] = mapped_column(String(200), nullable=False)  # "Sen Atkinson"
    chamber: Mapped[str] = mapped_column(String(10))  # "S" or "H"
    action_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    action_text: Mapped[str] = mapped_column(Text)
    
    # OLIS metadata
    olis_created_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    olis_modified_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Sync metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Constraints
    __table_args__ = (
        Index('idx_measure_vote_session', 'session_key'),
        Index('idx_measure_vote_measure', 'measure_prefix', 'measure_number'),
        Index('idx_measure_vote_legislator', 'vote_name'),
        Index('idx_measure_vote_date', 'action_date'),
        Index('idx_measure_vote_chamber', 'chamber'),
        Index('idx_measure_vote_result', 'vote'),
    )
    
    # Relationships
    session: Mapped["LegislativeSession"] = relationship("LegislativeSession")
    measure: Mapped["Measure"] = relationship("Measure")
    legislator: Mapped["Legislator"] = relationship("Legislator", back_populates="measure_votes")


class CommitteeVote(Base):
    __tablename__ = 'committee_votes'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    session_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('legislative_sessions.id'), nullable=False)
    committee_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('committees.id'), nullable=False)
    measure_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id'), nullable=False)
    legislator_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('legislators.id'), nullable=False)
    
    # OLIS identifiers
    committee_vote_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)  # OLIS ID
    committee_report_id: Mapped[Optional[int]] = mapped_column(Integer)
    committee_agenda_item_id: Mapped[Optional[int]] = mapped_column(Integer)
    session_key: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Committee and measure reference
    committee_code: Mapped[str] = mapped_column(String(20), nullable=False)
    measure_prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    measure_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Vote details
    vote_name: Mapped[str] = mapped_column(String(200), nullable=False)  # "Rep Berger"
    meaning: Mapped[str] = mapped_column(String(50), nullable=False)  # "Aye", "Nay", etc.
    meeting_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # OLIS metadata
    olis_created_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    olis_modified_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Sync metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Constraints
    __table_args__ = (
        Index('idx_committee_vote_session', 'session_key'),
        Index('idx_committee_vote_committee', 'committee_code'),
        Index('idx_committee_vote_measure', 'measure_prefix', 'measure_number'),
        Index('idx_committee_vote_legislator', 'vote_name'),
        Index('idx_committee_vote_date', 'meeting_date'),
        Index('idx_committee_vote_result', 'meaning'),
    )
    
    # Relationships
    session: Mapped["LegislativeSession"] = relationship("LegislativeSession")
    committee: Mapped["Committee"] = relationship("Committee")
    measure: Mapped["Measure"] = relationship("Measure")
    legislator: Mapped["Legislator"] = relationship("Legislator", back_populates="committee_votes")


class CommitteeMember(Base):
    __tablename__ = 'committee_members'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    session_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('legislative_sessions.id'), nullable=False)
    committee_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('committees.id'), nullable=False)
    legislator_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('legislators.id'), nullable=False)
    
    # OLIS identifiers
    session_key: Mapped[str] = mapped_column(String(20), nullable=False)
    committee_code: Mapped[str] = mapped_column(String(20), nullable=False)
    legislator_code: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Membership details
    title: Mapped[Optional[str]] = mapped_column(String(100))  # "Co-Chair", "Vice Chair", etc.
    
    # OLIS metadata
    olis_created_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    olis_modified_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Sync metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('session_key', 'committee_code', 'legislator_code', name='uq_committee_member'),
        Index('idx_committee_member_session', 'session_key'),
        Index('idx_committee_member_committee', 'committee_code'),
        Index('idx_committee_member_legislator', 'legislator_code'),
    )
    
    # Relationships
    session: Mapped["LegislativeSession"] = relationship("LegislativeSession")
    committee: Mapped["Committee"] = relationship("Committee")
    legislator: Mapped["Legislator"] = relationship("Legislator", back_populates="committee_memberships")


class MeasureHistoryAction(Base):
    __tablename__ = 'measure_history_actions'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    session_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('legislative_sessions.id'), nullable=False)
    measure_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id'), nullable=False)
    
    # OLIS identifiers
    measure_history_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)  # OLIS ID
    session_key: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Measure reference
    measure_prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    measure_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Action details
    chamber: Mapped[Optional[str]] = mapped_column(String(10))  # "H", "S", or null
    action_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    action_text: Mapped[str] = mapped_column(Text, nullable=False)
    vote_text: Mapped[Optional[str]] = mapped_column(Text)
    public_notification: Mapped[bool] = mapped_column(Boolean, server_default=text('FALSE'))
    
    # OLIS metadata
    olis_created_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    olis_modified_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Sync metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Constraints
    __table_args__ = (
        Index('idx_history_action_session', 'session_key'),
        Index('idx_history_action_measure', 'measure_prefix', 'measure_number'),
        Index('idx_history_action_date', 'action_date'),
        Index('idx_history_action_chamber', 'chamber'),
    )
    
    # Relationships
    session: Mapped["LegislativeSession"] = relationship("LegislativeSession")
    measure: Mapped["Measure"] = relationship("Measure")

# ============================================================================
# PHASE 2: MEETINGS & DOCUMENTS
# ============================================================================

class CommitteeMeeting(Base):
    __tablename__ = 'committee_meetings'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    session_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('legislative_sessions.id'), nullable=False)
    committee_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('committees.id'), nullable=False)
    
    # OLIS identifiers
    session_key: Mapped[str] = mapped_column(String(20), nullable=False)
    committee_code: Mapped[str] = mapped_column(String(20), nullable=False)
    meeting_guid: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    
    # Meeting details
    meeting_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(500))
    alternate_location: Mapped[Optional[str]] = mapped_column(String(500))
    posted_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Meeting status
    meeting_status_code: Mapped[Optional[str]] = mapped_column(String(10))
    meeting_status: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Agenda details
    agenda_url: Mapped[Optional[str]] = mapped_column(String(1000))
    agenda_revision_number: Mapped[Optional[int]] = mapped_column(Integer)
    
    # OLIS metadata
    olis_created_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    olis_modified_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Sync metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Constraints
    __table_args__ = (
        Index('idx_meeting_session', 'session_key'),
        Index('idx_meeting_committee', 'committee_code'),
        Index('idx_meeting_date', 'meeting_date'),
        Index('idx_meeting_status', 'meeting_status_code'),
    )
    
    # Relationships
    session: Mapped["LegislativeSession"] = relationship("LegislativeSession")
    committee: Mapped["Committee"] = relationship("Committee")
    agenda_items: Mapped[List["CommitteeAgendaItem"]] = relationship("CommitteeAgendaItem", back_populates="meeting")
    meeting_documents: Mapped[List["CommitteeMeetingDocument"]] = relationship("CommitteeMeetingDocument", back_populates="meeting")


class CommitteeAgendaItem(Base):
    __tablename__ = 'committee_agenda_items'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    session_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('legislative_sessions.id'), nullable=False)
    committee_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('committees.id'), nullable=False)
    meeting_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('committee_meetings.id'))
    measure_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id'))
    
    # OLIS identifiers
    committee_agenda_item_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    session_key: Mapped[str] = mapped_column(String(20), nullable=False)
    committee_code: Mapped[str] = mapped_column(String(20), nullable=False)
    meeting_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Measure reference (optional)
    measure_prefix: Mapped[Optional[str]] = mapped_column(String(10))
    measure_number: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Agenda item details
    meeting_type: Mapped[Optional[str]] = mapped_column(String(100))
    action: Mapped[Optional[str]] = mapped_column(Text)
    print_order: Mapped[Optional[str]] = mapped_column(String(20))
    comments: Mapped[Optional[str]] = mapped_column(Text)
    
    # Executive appointments (if applicable)
    board_name: Mapped[Optional[str]] = mapped_column(String(200))
    executive_appointee: Mapped[Optional[str]] = mapped_column(String(200))
    
    # OLIS metadata
    olis_created_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    olis_modified_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Sync metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Constraints
    __table_args__ = (
        Index('idx_agenda_item_session', 'session_key'),
        Index('idx_agenda_item_committee', 'committee_code'),
        Index('idx_agenda_item_date', 'meeting_date'),
        Index('idx_agenda_item_measure', 'measure_prefix', 'measure_number'),
    )
    
    # Relationships
    session: Mapped["LegislativeSession"] = relationship("LegislativeSession")
    committee: Mapped["Committee"] = relationship("Committee")
    meeting: Mapped[Optional["CommitteeMeeting"]] = relationship("CommitteeMeeting", back_populates="agenda_items")
    measure: Mapped[Optional["Measure"]] = relationship("Measure")


class MeasureDocument(Base):
    __tablename__ = 'measure_documents'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    session_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('legislative_sessions.id'), nullable=False)
    measure_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id'), nullable=False)
    
    # OLIS identifiers
    session_key: Mapped[str] = mapped_column(String(20), nullable=False)
    measure_prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    measure_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Document details
    version_description: Mapped[str] = mapped_column(String(100), nullable=False)  # "Introduced", "Enrolled"
    document_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    
    # OLIS metadata
    olis_created_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    olis_modified_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Sync metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('session_key', 'measure_prefix', 'measure_number', 'version_description', name='uq_measure_document'),
        Index('idx_measure_doc_session', 'session_key'),
        Index('idx_measure_doc_measure', 'measure_prefix', 'measure_number'),
        Index('idx_measure_doc_version', 'version_description'),
    )
    
    # Relationships
    session: Mapped["LegislativeSession"] = relationship("LegislativeSession")
    measure: Mapped["Measure"] = relationship("Measure")


class CommitteeMeetingDocument(Base):
    __tablename__ = 'committee_meeting_documents'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    session_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('legislative_sessions.id'), nullable=False)
    committee_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('committees.id'), nullable=False)
    meeting_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('committee_meetings.id'))
    measure_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id'))
    
    # OLIS identifiers
    committee_meeting_document_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    session_key: Mapped[str] = mapped_column(String(20), nullable=False)
    committee_code: Mapped[str] = mapped_column(String(20), nullable=False)
    meeting_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Document details
    exhibit_reference: Mapped[Optional[str]] = mapped_column(String(50))
    exhibit_title: Mapped[str] = mapped_column(String(500), nullable=False)
    submitter: Mapped[str] = mapped_column(String(200), nullable=False)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    document_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    
    # Related measure (optional)
    measure_prefix: Mapped[Optional[str]] = mapped_column(String(10))
    measure_number: Mapped[Optional[int]] = mapped_column(Integer)
    
    # OLIS metadata
    olis_created_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    olis_modified_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Sync metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Constraints
    __table_args__ = (
        Index('idx_meeting_doc_session', 'session_key'),
        Index('idx_meeting_doc_committee', 'committee_code'),
        Index('idx_meeting_doc_date', 'meeting_date'),
        Index('idx_meeting_doc_type', 'document_type'),
        Index('idx_meeting_doc_measure', 'measure_prefix', 'measure_number'),
    )
    
    # Relationships
    session: Mapped["LegislativeSession"] = relationship("LegislativeSession")
    committee: Mapped["Committee"] = relationship("Committee")
    meeting: Mapped[Optional["CommitteeMeeting"]] = relationship("CommitteeMeeting", back_populates="meeting_documents")
    measure: Mapped[Optional["Measure"]] = relationship("Measure")


class CommitteeProposedAmendment(Base):
    __tablename__ = 'committee_proposed_amendments'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    session_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('legislative_sessions.id'), nullable=False)
    committee_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('committees.id'), nullable=False)
    measure_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id'))
    agenda_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('committee_agenda_items.id'))
    
    # OLIS identifiers
    proposed_amendment_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    committee_agenda_item_id: Mapped[Optional[int]] = mapped_column(Integer)
    session_key: Mapped[str] = mapped_column(String(20), nullable=False)
    committee_code: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Amendment details
    meeting_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    measure_prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    measure_number: Mapped[int] = mapped_column(Integer, nullable=False)
    amendment_number: Mapped[str] = mapped_column(String(50), nullable=False)
    meaning: Mapped[str] = mapped_column(String(50), nullable=False)  # "Proposed", "Adopted", etc.
    proposed_amendment_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    
    # OLIS metadata
    olis_created_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    olis_modified_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Sync metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Constraints
    __table_args__ = (
        Index('idx_proposed_amendment_session', 'session_key'),
        Index('idx_proposed_amendment_committee', 'committee_code'),
        Index('idx_proposed_amendment_measure', 'measure_prefix', 'measure_number'),
        Index('idx_proposed_amendment_date', 'meeting_date'),
        Index('idx_proposed_amendment_meaning', 'meaning'),
    )
    
    # Relationships
    session: Mapped["LegislativeSession"] = relationship("LegislativeSession")
    committee: Mapped["Committee"] = relationship("Committee")
    measure: Mapped[Optional["Measure"]] = relationship("Measure")
    agenda_item: Mapped[Optional["CommitteeAgendaItem"]] = relationship("CommitteeAgendaItem")


class FloorSessionAgendaItem(Base):
    __tablename__ = 'floor_session_agenda_items'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    session_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('legislative_sessions.id'), nullable=False)
    measure_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id'))
    
    # OLIS identifiers
    agenda_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    session_key: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Measure reference
    measure_prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    measure_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Floor session details
    schedule_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    version: Mapped[Optional[str]] = mapped_column(String(50))
    chamber: Mapped[str] = mapped_column(String(10), nullable=False)  # "H" or "S"
    completed: Mapped[bool] = mapped_column(Boolean, server_default=text('FALSE'))
    order_of_business: Mapped[str] = mapped_column(String(200), nullable=False)
    carrier_code: Mapped[Optional[str]] = mapped_column(String(100))
    
    # OLIS metadata
    olis_created_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    olis_modified_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Sync metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Constraints
    __table_args__ = (
        Index('idx_floor_agenda_session', 'session_key'),
        Index('idx_floor_agenda_measure', 'measure_prefix', 'measure_number'),
        Index('idx_floor_agenda_chamber', 'chamber'),
        Index('idx_floor_agenda_date', 'schedule_date'),
        Index('idx_floor_agenda_completed', 'completed'),
        Index('idx_floor_agenda_order', 'order_of_business'),
    )
    
    # Relationships
    session: Mapped["LegislativeSession"] = relationship("LegislativeSession")
    measure: Mapped[Optional["Measure"]] = relationship("Measure")


class FloorLetter(Base):
    __tablename__ = 'floor_letters'
    
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    session_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('legislative_sessions.id'), nullable=False)
    measure_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey('measures.id'))
    
    # OLIS identifiers
    floor_letter_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)  # OLIS ID
    session_key: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Measure reference (optional as some floor letters may not be tied to specific measures)
    measure_prefix: Mapped[Optional[str]] = mapped_column(String(10))
    measure_number: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Floor letter details
    letter_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    chamber: Mapped[str] = mapped_column(String(10), nullable=False)  # "H" or "S"
    letter_description: Mapped[str] = mapped_column(String(500), nullable=False)
    letter_title: Mapped[str] = mapped_column(String(500), nullable=False)
    floor_letter_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    
    # Sync metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Constraints
    __table_args__ = (
        Index('idx_floor_letter_session', 'session_key'),
        Index('idx_floor_letter_measure', 'measure_prefix', 'measure_number'),
        Index('idx_floor_letter_chamber', 'chamber'),
        Index('idx_floor_letter_date', 'letter_date'),
        Index('idx_floor_letter_title', 'letter_title'),
    )
    
    # Relationships
    session: Mapped["LegislativeSession"] = relationship("LegislativeSession")
    measure: Mapped[Optional["Measure"]] = relationship("Measure")
