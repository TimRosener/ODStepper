-- ============================================================================
-- OLIS LEGISLATURE TRACKER - ENHANCED SCHEMA WITH ANALYSIS FRAMEWORK
-- ============================================================================
-- Complete database schema for Oregon Legislative Information System (OLIS)
-- Includes OLIS data mirroring + User/Company Management + Extensible Analysis
-- Created: 2025-01-08
-- Version: 2.0 - Added comprehensive analysis framework
-- ============================================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For similarity matching

-- ============================================================================
-- SCHEMA MANAGEMENT
-- ============================================================================

CREATE TABLE schema_versions (
    version INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    checksum TEXT
);

-- Insert schema versions
INSERT INTO schema_versions (version, description) VALUES 
    (1, 'Initial OLIS database schema with user management'),
    (2, 'Added extensible analysis framework for AI/ML insights');

-- ============================================================================
-- COMPANY & USER MANAGEMENT SYSTEM (Unchanged from v1)
-- ============================================================================

CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    website VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(20),
    country VARCHAR(50) DEFAULT 'US',
    -- Subscription & Access
    subscription_tier VARCHAR(50) DEFAULT 'basic', -- basic, premium, enterprise
    max_users INTEGER DEFAULT 10,
    is_active BOOLEAN DEFAULT TRUE,
    -- Billing
    billing_contact_name VARCHAR(255),
    billing_contact_email VARCHAR(255),
    billing_contact_phone VARCHAR(50),
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_user_id UUID,
    notes TEXT
);

CREATE INDEX idx_companies_slug ON companies(slug);
CREATE INDEX idx_companies_active ON companies(is_active);
CREATE INDEX idx_companies_tier ON companies(subscription_tier);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Authentication
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    username VARCHAR(100) UNIQUE,
    
    -- Profile
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    title VARCHAR(100),
    phone VARCHAR(50),
    
    -- Access & Permissions
    role VARCHAR(50) DEFAULT 'user', -- admin, manager, user, viewer
    is_active BOOLEAN DEFAULT TRUE,
    is_company_admin BOOLEAN DEFAULT FALSE,
    
    -- Authentication metadata
    email_verified_at TIMESTAMP WITH TIME ZONE,
    password_reset_token VARCHAR(255),
    password_reset_expires_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0,
    
    -- Preferences
    timezone VARCHAR(50) DEFAULT 'America/Los_Angeles',
    notification_preferences JSONB DEFAULT '{}',
    ui_preferences JSONB DEFAULT '{}',
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_user_id UUID
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_company ON users(company_id);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_role ON users(role);

-- ============================================================================
-- OLIS DATA MIRRORING - LEGISLATIVE SESSIONS
-- ============================================================================

CREATE TABLE legislative_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- OLIS Fields
    session_key VARCHAR(10) UNIQUE NOT NULL, -- e.g., "2025R1"
    session_name VARCHAR(100) NOT NULL,      -- e.g., "2025 Regular Session"
    session_type VARCHAR(50),                -- Regular, Special, Interim
    session_year INTEGER,
    
    -- Dates
    begin_date DATE,
    end_date DATE,
    
    -- Status
    is_current BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_synced_at TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(50) DEFAULT 'pending' -- pending, syncing, completed, failed
);

CREATE INDEX idx_sessions_key ON legislative_sessions(session_key);
CREATE INDEX idx_sessions_current ON legislative_sessions(is_current);
CREATE INDEX idx_sessions_year ON legislative_sessions(session_year);

-- ============================================================================
-- OLIS DATA MIRRORING - COMMITTEES
-- ============================================================================

CREATE TABLE committees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES legislative_sessions(id),
    
    -- Committee identification
    committee_code VARCHAR(20) NOT NULL,     -- e.g., "HJUD", "SRUL"
    committee_name VARCHAR(255) NOT NULL,
    chamber VARCHAR(20),                     -- House, Senate, Joint
    committee_type VARCHAR(50),              -- Standing, Special, Sub
    
    -- Details
    description TEXT,
    chair_name VARCHAR(255),
    vice_chair_name VARCHAR(255),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_synced_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_committees_code ON committees(committee_code);
CREATE INDEX idx_committees_session ON committees(session_id);
CREATE INDEX idx_committees_chamber ON committees(chamber);

-- ============================================================================
-- OLIS DATA MIRRORING - MEASURES/BILLS (Enhanced with Analysis Fields)
-- ============================================================================

CREATE TABLE measures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES legislative_sessions(id),
    
    -- OLIS Identification Fields (6 fields)
    session_key VARCHAR(10) NOT NULL,
    measure_prefix VARCHAR(10) NOT NULL,     -- HB, SB, HCR, SCR, etc.
    measure_number INTEGER NOT NULL,
    prefix_meaning VARCHAR(255),             -- "House Bill", "Senate Concurrent Resolution"
    lc_number INTEGER,                       -- Legislative Counsel number
    chapter_number INTEGER,
    
    -- OLIS Content Fields
    measure_summary TEXT,
    catch_line TEXT,                         -- Brief description
    minority_catch_line TEXT,
    relating_to TEXT,                        -- What the bill relates to
    relating_to_full TEXT,
    at_the_request_of TEXT,
    
    -- OLIS Status & Location Fields
    current_location VARCHAR(500),
    current_version VARCHAR(50),
    
    -- OLIS Committee Fields
    current_committee_code VARCHAR(20),
    current_subcommittee VARCHAR(255),
    
    -- OLIS Date/Time Fields
    created_date TIMESTAMP WITH TIME ZONE,
    modified_date TIMESTAMP WITH TIME ZONE,
    effective_date DATE,
    
    -- OLIS Other Fields
    fiscal_impact TEXT,
    revenue_impact TEXT,
    fiscal_analyst VARCHAR(255),
    revenue_economist VARCHAR(255),
    emergency_clause BOOLEAN DEFAULT FALSE,
    vetoed BOOLEAN DEFAULT FALSE,
    
    -- Additional computed/derived fields
    bill_number VARCHAR(20) GENERATED ALWAYS AS (measure_prefix || measure_number) STORED,
    chamber VARCHAR(20),
    bill_type VARCHAR(50),
    status_category VARCHAR(50),
    priority_score INTEGER DEFAULT 0,
    
    -- NEW: Analysis metadata fields
    analysis_metadata JSONB DEFAULT '{}',           -- Flexible storage for any analysis
    last_comprehensive_analysis TIMESTAMP WITH TIME ZONE,
    analysis_flags JSONB DEFAULT '{}',              -- What needs re-analysis
    ai_insights JSONB DEFAULT '{}',                 -- AI-generated insights
    
    -- Foreign key references
    current_committee_id UUID REFERENCES committees(id),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_synced_at TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(50) DEFAULT 'pending'
);

-- Indexes for measures
CREATE UNIQUE INDEX idx_measures_unique ON measures(session_key, measure_prefix, measure_number);
CREATE INDEX idx_measures_session ON measures(session_id);
CREATE INDEX idx_measures_bill_number ON measures(bill_number);
CREATE INDEX idx_measures_chamber ON measures(chamber);
CREATE INDEX idx_measures_committee ON measures(current_committee_id);
CREATE INDEX idx_measures_status ON measures(status_category);
CREATE INDEX idx_measures_priority ON measures(priority_score DESC);
-- NEW: GIN index for JSONB analysis fields
CREATE INDEX idx_measures_analysis_gin ON measures USING gin(analysis_metadata);
CREATE INDEX idx_measures_insights_gin ON measures USING gin(ai_insights);

-- ============================================================================
-- NEW: EXTENSIBLE ANALYSIS FRAMEWORK
-- ============================================================================

-- Define types of analyses that can be performed
CREATE TABLE analysis_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Type definition
    type_code VARCHAR(50) UNIQUE NOT NULL,      -- testimony_analysis, amendment_analysis, etc.
    type_name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50),                       -- text, fiscal, legal, stakeholder, etc.
    
    -- Configuration
    default_parameters JSONB DEFAULT '{}',      -- Default params for this analysis type
    required_fields JSONB DEFAULT '[]',         -- Fields required for this analysis
    output_schema JSONB,                        -- Expected output structure
    
    -- AI/ML Configuration
    default_model VARCHAR(100),                 -- GPT-4, Claude, custom model
    default_prompt_template TEXT,
    confidence_threshold DECIMAL(3,2) DEFAULT 0.7,
    
    -- Scheduling
    auto_analyze BOOLEAN DEFAULT FALSE,         -- Run automatically on new data
    analysis_frequency VARCHAR(50),             -- daily, weekly, on_change, etc.
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_user_id UUID REFERENCES users(id)
);

CREATE INDEX idx_analysis_types_code ON analysis_types(type_code);
CREATE INDEX idx_analysis_types_category ON analysis_types(category);

-- Generic table for storing any type of analysis
CREATE TABLE measure_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    measure_id UUID NOT NULL REFERENCES measures(id) ON DELETE CASCADE,
    analysis_type_id UUID NOT NULL REFERENCES analysis_types(id),
    
    -- Analysis versioning
    analysis_version INTEGER DEFAULT 1,
    is_current_version BOOLEAN DEFAULT TRUE,
    
    -- Analysis content
    raw_analysis JSONB,                         -- Raw AI/ML output
    structured_data JSONB,                      -- Parsed/structured results
    summary TEXT,                                -- Human-readable summary
    key_findings JSONB DEFAULT '[]',            -- Array of key findings
    
    -- Confidence and quality
    confidence_scores JSONB DEFAULT '{}',       -- Confidence per analysis component
    overall_confidence DECIMAL(3,2),            -- 0.00 to 1.00
    quality_score DECIMAL(3,2),                 -- 0.00 to 1.00
    
    -- Analysis metadata
    ai_model_used VARCHAR(100),
    prompt_version VARCHAR(50),
    processing_time_ms INTEGER,
    token_count INTEGER,
    
    -- Who/what performed it
    performed_by_user_id UUID REFERENCES users(id),
    performed_by_system BOOLEAN DEFAULT FALSE,
    
    -- Status
    status VARCHAR(50) DEFAULT 'completed',     -- pending, processing, completed, failed
    error_message TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE         -- For caching/refresh
);

CREATE INDEX idx_measure_analyses_measure ON measure_analyses(measure_id);
CREATE INDEX idx_measure_analyses_type ON measure_analyses(analysis_type_id);
CREATE INDEX idx_measure_analyses_current ON measure_analyses(is_current_version) WHERE is_current_version = TRUE;
CREATE INDEX idx_measure_analyses_confidence ON measure_analyses(overall_confidence);
-- GIN indexes for JSONB fields
CREATE INDEX idx_measure_analyses_raw_gin ON measure_analyses USING gin(raw_analysis);
CREATE INDEX idx_measure_analyses_structured_gin ON measure_analyses USING gin(structured_data);

-- ============================================================================
-- ENHANCED TESTIMONY WITH ANALYSIS
-- ============================================================================

CREATE TABLE testimonies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    measure_id UUID NOT NULL REFERENCES measures(id) ON DELETE CASCADE,
    meeting_id UUID,  -- Can reference committee_meetings when available
    
    -- Testimony details
    testifier_name VARCHAR(255),
    testifier_organization VARCHAR(255),
    testifier_title VARCHAR(255),
    testifier_city VARCHAR(100),
    testifier_state VARCHAR(50),
    
    -- Position
    position_code INTEGER,                      -- 3981=neutral, 3982=in_favor, 3983=against
    position_text VARCHAR(50),
    
    -- Testimony content
    testimony_text TEXT,
    testimony_summary TEXT,
    
    -- Meeting context
    meeting_date DATE,
    committee_code VARCHAR(20),
    
    -- ENHANCED: Analysis fields
    sentiment_score DECIMAL(3,2),               -- -1.0 to 1.0
    emotion_scores JSONB DEFAULT '{}',          -- anger, joy, fear, etc.
    key_points JSONB DEFAULT '[]',              -- Extracted key arguments
    
    -- NEW: Advanced analysis fields
    analysis_version INTEGER,
    analysis_metadata JSONB DEFAULT '{}',       -- Flexible analysis storage
    extracted_entities JSONB DEFAULT '{}',      -- People, orgs, topics mentioned
    policy_recommendations JSONB DEFAULT '[]',  -- Extracted policy suggestions
    stakeholder_classification VARCHAR(100),    -- Individual, Business, NGO, etc.
    credibility_indicators JSONB DEFAULT '{}',  -- Expertise markers, citations, etc.
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_synced_at TIMESTAMP WITH TIME ZONE,
    last_analyzed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_testimonies_measure ON testimonies(measure_id);
CREATE INDEX idx_testimonies_position ON testimonies(position_code);
CREATE INDEX idx_testimonies_meeting_date ON testimonies(meeting_date);
CREATE INDEX idx_testimonies_organization ON testimonies(testifier_organization);
CREATE INDEX idx_testimonies_sentiment ON testimonies(sentiment_score);
-- GIN indexes for analysis fields
CREATE INDEX idx_testimonies_entities_gin ON testimonies USING gin(extracted_entities);
CREATE INDEX idx_testimonies_metadata_gin ON testimonies USING gin(analysis_metadata);

-- ============================================================================
-- NEW: AMENDMENT TRACKING AND ANALYSIS
-- ============================================================================

CREATE TABLE amendments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    measure_id UUID NOT NULL REFERENCES measures(id) ON DELETE CASCADE,
    
    -- Amendment identification
    amendment_number VARCHAR(50),
    amendment_type VARCHAR(50),                 -- committee, floor, conference
    sponsor_name VARCHAR(255),
    sponsor_type VARCHAR(50),                   -- member, committee
    
    -- Content
    original_text TEXT,
    amended_text TEXT,
    description TEXT,
    
    -- Status
    status VARCHAR(50),                         -- proposed, adopted, rejected, withdrawn
    action_date DATE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE amendment_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    amendment_id UUID NOT NULL REFERENCES amendments(id) ON DELETE CASCADE,
    measure_id UUID NOT NULL REFERENCES measures(id) ON DELETE CASCADE,
    
    -- Analysis content
    change_summary TEXT,
    change_impact_analysis JSONB DEFAULT '{}',  -- Impact on different sections
    stakeholder_impact JSONB DEFAULT '{}',      -- Who's affected and how
    fiscal_impact_delta NUMERIC(15,2),          -- Change in fiscal impact
    legal_implications JSONB DEFAULT '{}',      -- Legal analysis
    
    -- Comparison metrics
    text_similarity_score DECIMAL(3,2),         -- How similar to original
    substantive_change_score DECIMAL(3,2),      -- How significant the changes
    
    -- AI Analysis
    ai_interpretation TEXT,
    confidence_score DECIMAL(3,2),
    analysis_metadata JSONB DEFAULT '{}',
    
    -- Metadata
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    analyzed_by_user_id UUID REFERENCES users(id),
    analysis_version INTEGER DEFAULT 1
);

CREATE INDEX idx_amendment_analyses_amendment ON amendment_analyses(amendment_id);
CREATE INDEX idx_amendment_analyses_measure ON amendment_analyses(measure_id);

-- ============================================================================
-- NEW: ANALYSIS CONFIGURATION AND VERSIONING
-- ============================================================================

CREATE TABLE analysis_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_type_id UUID NOT NULL REFERENCES analysis_types(id),
    
    -- Configuration details
    config_name VARCHAR(255) NOT NULL,
    config_version VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Prompts and parameters
    prompt_template TEXT,
    system_prompt TEXT,
    parameters JSONB DEFAULT '{}',              -- Temperature, max_tokens, etc.
    preprocessing_steps JSONB DEFAULT '[]',     -- Steps before analysis
    postprocessing_steps JSONB DEFAULT '[]',    -- Steps after analysis
    
    -- Thresholds and rules
    confidence_threshold DECIMAL(3,2),
    quality_threshold DECIMAL(3,2),
    validation_rules JSONB DEFAULT '[]',
    
    -- A/B Testing
    is_experiment BOOLEAN DEFAULT FALSE,
    experiment_group VARCHAR(50),
    experiment_metrics JSONB DEFAULT '{}',
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_user_id UUID REFERENCES users(id)
);

CREATE INDEX idx_analysis_configs_type ON analysis_configurations(analysis_type_id);
CREATE INDEX idx_analysis_configs_active ON analysis_configurations(is_active);

-- ============================================================================
-- NEW: ANALYSIS HISTORY AND AUDIT TRAIL
-- ============================================================================

CREATE TABLE analysis_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- What was analyzed
    entity_type VARCHAR(50) NOT NULL,           -- measure, testimony, amendment, etc.
    entity_id UUID NOT NULL,                    -- ID of the analyzed entity
    analysis_type_id UUID REFERENCES analysis_types(id),
    
    -- Analysis details
    analysis_id UUID,                           -- Reference to specific analysis
    config_id UUID REFERENCES analysis_configurations(id),
    
    -- Performance metrics
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    processing_time_ms INTEGER,
    token_count INTEGER,
    cost_estimate DECIMAL(10,4),
    
    -- Results summary
    success BOOLEAN,
    confidence_score DECIMAL(3,2),
    key_metrics JSONB DEFAULT '{}',
    error_details JSONB,
    
    -- Who/what triggered it
    triggered_by VARCHAR(50),                   -- user, system, scheduler, api
    user_id UUID REFERENCES users(id),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_analysis_history_entity ON analysis_history(entity_type, entity_id);
CREATE INDEX idx_analysis_history_type ON analysis_history(analysis_type_id);
CREATE INDEX idx_analysis_history_created ON analysis_history(created_at);

-- ============================================================================
-- USER PREFERENCES & TRACKING SYSTEM (Enhanced)
-- ============================================================================

CREATE TABLE user_tracked_measures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    measure_id UUID NOT NULL REFERENCES measures(id) ON DELETE CASCADE,
    
    -- Tracking preferences
    tracking_reason VARCHAR(255),
    priority_level VARCHAR(20) DEFAULT 'medium',
    
    -- Notification preferences
    notify_on_status_change BOOLEAN DEFAULT TRUE,
    notify_on_committee_action BOOLEAN DEFAULT TRUE,
    notify_on_new_testimony BOOLEAN DEFAULT FALSE,
    notify_on_amendments BOOLEAN DEFAULT FALSE,
    notify_on_new_analysis BOOLEAN DEFAULT TRUE,  -- NEW
    
    -- User notes
    private_notes TEXT,
    tags JSONB DEFAULT '[]',
    
    -- NEW: Analysis preferences
    preferred_analysis_types JSONB DEFAULT '[]',   -- Which analyses to run
    analysis_frequency VARCHAR(50),                -- How often to analyze
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_viewed_at TIMESTAMP WITH TIME ZONE
);

CREATE UNIQUE INDEX idx_user_tracked_unique ON user_tracked_measures(user_id, measure_id);
CREATE INDEX idx_user_tracked_user ON user_tracked_measures(user_id);
CREATE INDEX idx_user_tracked_priority ON user_tracked_measures(priority_level);

-- ============================================================================
-- VIEWS FOR ANALYSIS QUERIES
-- ============================================================================

-- Current analyses for each measure
CREATE VIEW current_measure_analyses AS
SELECT 
    m.id as measure_id,
    m.bill_number,
    at.type_code,
    at.type_name,
    ma.summary,
    ma.overall_confidence,
    ma.key_findings,
    ma.created_at as analyzed_at
FROM measures m
JOIN measure_analyses ma ON m.id = ma.measure_id
JOIN analysis_types at ON ma.analysis_type_id = at.id
WHERE ma.is_current_version = TRUE
ORDER BY m.bill_number, at.type_code;

-- Testimony analysis summary
CREATE VIEW testimony_analysis_summary AS
SELECT 
    m.id as measure_id,
    m.bill_number,
    COUNT(t.id) as testimony_count,
    AVG(t.sentiment_score) as avg_sentiment,
    COUNT(DISTINCT t.testifier_organization) as unique_organizations,
    COUNT(CASE WHEN t.position_code = 3982 THEN 1 END) as favor_count,
    COUNT(CASE WHEN t.position_code = 3983 THEN 1 END) as against_count,
    COUNT(CASE WHEN t.position_code = 3981 THEN 1 END) as neutral_count,
    MAX(t.last_analyzed_at) as last_analysis_date
FROM measures m
LEFT JOIN testimonies t ON m.id = t.measure_id
GROUP BY m.id, m.bill_number;

-- ============================================================================
-- FUNCTIONS FOR ANALYSIS OPERATIONS
-- ============================================================================

-- Function to queue an analysis
CREATE OR REPLACE FUNCTION queue_analysis(
    p_entity_type VARCHAR(50),
    p_entity_id UUID,
    p_analysis_type_code VARCHAR(50),
    p_user_id UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_analysis_id UUID;
    v_analysis_type_id UUID;
BEGIN
    -- Get analysis type ID
    SELECT id INTO v_analysis_type_id
    FROM analysis_types
    WHERE type_code = p_analysis_type_code AND is_active = TRUE;
    
    IF v_analysis_type_id IS NULL THEN
        RAISE EXCEPTION 'Analysis type % not found or inactive', p_analysis_type_code;
    END IF;
    
    -- Create analysis record based on entity type
    IF p_entity_type = 'measure' THEN
        INSERT INTO measure_analyses (
            measure_id, analysis_type_id, status, performed_by_user_id
        ) VALUES (
            p_entity_id, v_analysis_type_id, 'pending', p_user_id
        ) RETURNING id INTO v_analysis_id;
    END IF;
    
    -- Log to history
    INSERT INTO analysis_history (
        entity_type, entity_id, analysis_type_id, analysis_id,
        triggered_by, user_id, started_at
    ) VALUES (
        p_entity_type, p_entity_id, v_analysis_type_id, v_analysis_id,
        CASE WHEN p_user_id IS NOT NULL THEN 'user' ELSE 'system' END,
        p_user_id, NOW()
    );
    
    RETURN v_analysis_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get latest analysis for a measure
CREATE OR REPLACE FUNCTION get_latest_analysis(
    p_measure_id UUID,
    p_analysis_type_code VARCHAR(50)
)
RETURNS JSONB AS $$
DECLARE
    v_result JSONB;
BEGIN
    SELECT to_jsonb(ma.*) INTO v_result
    FROM measure_analyses ma
    JOIN analysis_types at ON ma.analysis_type_id = at.id
    WHERE ma.measure_id = p_measure_id
    AND at.type_code = p_analysis_type_code
    AND ma.is_current_version = TRUE
    ORDER BY ma.created_at DESC
    LIMIT 1;
    
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- INITIAL ANALYSIS TYPE DATA
-- ============================================================================

INSERT INTO analysis_types (type_code, type_name, category, description) VALUES
    ('testimony_sentiment', 'Testimony Sentiment Analysis', 'text', 'Analyze sentiment and emotion in public testimony'),
    ('testimony_summary', 'Testimony Summarization', 'text', 'Generate summaries of testimony content'),
    ('amendment_impact', 'Amendment Impact Analysis', 'legal', 'Analyze the impact of proposed amendments'),
    ('fiscal_analysis', 'Fiscal Impact Analysis', 'fiscal', 'Deep analysis of fiscal and revenue impacts'),
    ('stakeholder_mapping', 'Stakeholder Mapping', 'stakeholder', 'Identify and map stakeholder positions'),
    ('bill_similarity', 'Bill Similarity Analysis', 'text', 'Find similar bills and patterns'),
    ('outcome_prediction', 'Outcome Prediction', 'predictive', 'Predict likelihood of bill passage'),
    ('timeline_analysis', 'Timeline Analysis', 'temporal', 'Analyze bill progress and predict timeline');

-- ============================================================================
-- ENHANCED SECURITY POLICIES
-- ============================================================================

-- Enable RLS on analysis tables
ALTER TABLE measure_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_history ENABLE ROW LEVEL SECURITY;

-- Policy for measure analyses - users can see analyses for measures they track
CREATE POLICY measure_analyses_access ON measure_analyses
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_tracked_measures utm
            WHERE utm.measure_id = measure_analyses.measure_id
            AND utm.user_id = current_setting('app.current_user_id')::UUID
        )
        OR
        (SELECT role FROM users WHERE id = current_setting('app.current_user_id')::UUID) IN ('admin', 'manager')
    );

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE analysis_types IS 'Defines types of analyses that can be performed on legislative data';
COMMENT ON TABLE measure_analyses IS 'Stores all analyses performed on measures, with versioning';
COMMENT ON TABLE amendment_analyses IS 'Detailed analysis of legislative amendments and their impacts';
COMMENT ON TABLE analysis_configurations IS 'Configuration and prompts for different analysis types';
COMMENT ON TABLE analysis_history IS 'Complete audit trail of all analyses performed';

COMMENT ON COLUMN measure_analyses.raw_analysis IS 'Raw output from AI/ML models in JSON format';
COMMENT ON COLUMN measure_analyses.structured_data IS 'Parsed and structured analysis results';
COMMENT ON COLUMN testimonies.extracted_entities IS 'Named entities extracted from testimony (people, orgs, topics)';
COMMENT ON COLUMN amendments.change_impact_analysis IS 'Detailed analysis of what the amendment changes';

-- ============================================================================
-- END OF ENHANCED SCHEMA
-- ============================================================================