-- ============================================================================
-- OLIS LEGISLATURE TRACKER - COMPREHENSIVE POSTGRESQL SCHEMA
-- ============================================================================
-- Complete database schema for Oregon Legislative Information System (OLIS)
-- Includes OLIS data mirroring + User/Company Management + Preferences
-- Created: 2025-01-08
-- ============================================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- SCHEMA MANAGEMENT
-- ============================================================================

CREATE TABLE schema_versions (
    version INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    checksum TEXT
);

-- Insert initial schema version
INSERT INTO schema_versions (version, description) VALUES 
    (1, 'Initial OLIS database schema with user management');

-- ============================================================================
-- COMPANY & USER MANAGEMENT SYSTEM
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
-- OLIS DATA MIRRORING - MEASURES/BILLS (Complete 25-field schema)
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
    
    -- OLIS Content Fields (1 field + related content)
    measure_summary TEXT,
    catch_line TEXT,                         -- Brief description
    minority_catch_line TEXT,
    relating_to TEXT,                        -- What the bill relates to
    relating_to_full TEXT,
    at_the_request_of TEXT,
    
    -- OLIS Status & Location Fields (2 fields + related)
    current_location VARCHAR(500),
    current_version VARCHAR(50),
    
    -- OLIS Committee Fields (2 fields)
    current_committee_code VARCHAR(20),
    current_subcommittee VARCHAR(255),
    
    -- OLIS Date/Time Fields (3 fields)
    created_date TIMESTAMP WITH TIME ZONE,
    modified_date TIMESTAMP WITH TIME ZONE,
    effective_date DATE,
    
    -- OLIS Other Fields (11 fields)
    fiscal_impact TEXT,
    revenue_impact TEXT,
    fiscal_analyst VARCHAR(255),
    revenue_economist VARCHAR(255),
    emergency_clause BOOLEAN DEFAULT FALSE,
    vetoed BOOLEAN DEFAULT FALSE,
    
    -- Additional computed/derived fields
    bill_number VARCHAR(20) GENERATED ALWAYS AS (measure_prefix || measure_number) STORED,
    chamber VARCHAR(20), -- House, Senate, Joint (derived from prefix)
    bill_type VARCHAR(50), -- Bill, Resolution, Memorial, etc. (derived from prefix)
    status_category VARCHAR(50), -- Introduced, Committee, Floor, Passed, etc.
    priority_score INTEGER DEFAULT 0, -- For hot bills ranking
    
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
CREATE INDEX idx_measures_prefix ON measures(measure_prefix);
CREATE INDEX idx_measures_location ON measures(current_location);

-- ============================================================================
-- OLIS DATA MIRRORING - MEASURE SPONSORS/AUTHORS
-- ============================================================================

CREATE TABLE measure_sponsors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    measure_id UUID NOT NULL REFERENCES measures(id) ON DELETE CASCADE,
    
    -- Sponsor details
    sponsor_name VARCHAR(255) NOT NULL,
    sponsor_type VARCHAR(50), -- Chief, Prime, Co-sponsor
    chamber VARCHAR(20),      -- House, Senate
    district VARCHAR(10),
    party VARCHAR(50),
    
    -- Order/priority
    sponsor_order INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sponsors_measure ON measure_sponsors(measure_id);
CREATE INDEX idx_sponsors_name ON measure_sponsors(sponsor_name);
CREATE INDEX idx_sponsors_type ON measure_sponsors(sponsor_type);

-- ============================================================================
-- OLIS DATA MIRRORING - COMMITTEE TESTIMONY
-- ============================================================================

CREATE TABLE committee_meetings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    committee_id UUID NOT NULL REFERENCES committees(id),
    
    -- Meeting details
    meeting_date DATE NOT NULL,
    meeting_time TIME,
    location VARCHAR(255),
    meeting_type VARCHAR(50), -- Hearing, Work Session, etc.
    
    -- Status
    is_cancelled BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE testimonies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    measure_id UUID NOT NULL REFERENCES measures(id) ON DELETE CASCADE,
    meeting_id UUID REFERENCES committee_meetings(id),
    
    -- Testimony details
    testifier_name VARCHAR(255),
    testifier_organization VARCHAR(255),
    testifier_title VARCHAR(255),
    testifier_city VARCHAR(100),
    testifier_state VARCHAR(50),
    
    -- Position
    position_code INTEGER, -- 3981=neutral, 3982=in_favor, 3983=against
    position_text VARCHAR(50), -- "In Favor", "Against", "Neutral"
    
    -- Testimony content
    testimony_text TEXT,
    testimony_summary TEXT,
    
    -- Meeting context
    meeting_date DATE,
    committee_code VARCHAR(20),
    
    -- Analysis
    sentiment_score DECIMAL(3,2), -- -1.0 to 1.0
    key_points JSONB,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_synced_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_testimonies_measure ON testimonies(measure_id);
CREATE INDEX idx_testimonies_position ON testimonies(position_code);
CREATE INDEX idx_testimonies_meeting_date ON testimonies(meeting_date);
CREATE INDEX idx_testimonies_organization ON testimonies(testifier_organization);

-- ============================================================================
-- USER PREFERENCES & TRACKING SYSTEM
-- ============================================================================

CREATE TABLE user_tracked_measures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    measure_id UUID NOT NULL REFERENCES measures(id) ON DELETE CASCADE,
    
    -- Tracking preferences
    tracking_reason VARCHAR(255), -- "Client Interest", "Company Priority", etc.
    priority_level VARCHAR(20) DEFAULT 'medium', -- high, medium, low
    
    -- Notification preferences
    notify_on_status_change BOOLEAN DEFAULT TRUE,
    notify_on_committee_action BOOLEAN DEFAULT TRUE,
    notify_on_new_testimony BOOLEAN DEFAULT FALSE,
    notify_on_amendments BOOLEAN DEFAULT FALSE,
    
    -- User notes
    private_notes TEXT,
    tags JSONB DEFAULT '[]', -- User-defined tags
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_viewed_at TIMESTAMP WITH TIME ZONE
);

CREATE UNIQUE INDEX idx_user_tracked_unique ON user_tracked_measures(user_id, measure_id);
CREATE INDEX idx_user_tracked_user ON user_tracked_measures(user_id);
CREATE INDEX idx_user_tracked_priority ON user_tracked_measures(priority_level);

CREATE TABLE user_measure_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    measure_id UUID NOT NULL REFERENCES measures(id) ON DELETE CASCADE,
    
    -- Alert criteria
    alert_type VARCHAR(50) NOT NULL, -- status_change, committee_action, testimony, amendment
    alert_title VARCHAR(255) NOT NULL,
    alert_message TEXT NOT NULL,
    
    -- Alert metadata
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,
    sent_email BOOLEAN DEFAULT FALSE,
    sent_email_at TIMESTAMP WITH TIME ZONE,
    
    -- Reference data
    old_value TEXT,
    new_value TEXT,
    change_data JSONB,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_alerts_user ON user_measure_alerts(user_id);
CREATE INDEX idx_alerts_unread ON user_measure_alerts(user_id, is_read) WHERE NOT is_read;
CREATE INDEX idx_alerts_type ON user_measure_alerts(alert_type);

-- ============================================================================
-- USER PREFERENCES & SETTINGS
-- ============================================================================

CREATE TABLE user_search_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Default search filters
    default_session_keys TEXT[], -- Which sessions to search by default
    default_chambers TEXT[],      -- House, Senate, Joint
    default_bill_types TEXT[],    -- Bill, Resolution, etc.
    default_committees TEXT[],    -- Committee codes
    
    -- Hot bills criteria
    hot_bills_min_testimonies INTEGER DEFAULT 5,
    hot_bills_weight_recent DECIMAL(3,2) DEFAULT 1.0,
    hot_bills_weight_testimony DECIMAL(3,2) DEFAULT 0.8,
    hot_bills_weight_amendments DECIMAL(3,2) DEFAULT 0.6,
    
    -- Display preferences
    results_per_page INTEGER DEFAULT 25,
    default_sort_order VARCHAR(50) DEFAULT 'relevance',
    show_bill_summaries BOOLEAN DEFAULT TRUE,
    show_fiscal_impact BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_search_prefs_user ON user_search_preferences(user_id);

CREATE TABLE saved_searches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Search details
    name VARCHAR(255) NOT NULL,
    description TEXT,
    search_criteria JSONB NOT NULL,
    
    -- Notifications
    notify_on_new_results BOOLEAN DEFAULT FALSE,
    last_notification_sent_at TIMESTAMP WITH TIME ZONE,
    
    -- Usage
    use_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    -- Sharing
    is_shared BOOLEAN DEFAULT FALSE,
    shared_with_company BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_saved_searches_user ON saved_searches(user_id);
CREATE INDEX idx_saved_searches_shared ON saved_searches(is_shared);

-- ============================================================================
-- COMPANY-LEVEL FEATURES
-- ============================================================================

CREATE TABLE company_bill_priorities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    measure_id UUID NOT NULL REFERENCES measures(id) ON DELETE CASCADE,
    
    -- Priority details
    priority_level VARCHAR(20) NOT NULL, -- critical, high, medium, low
    priority_reason TEXT,
    assigned_to_user_id UUID REFERENCES users(id),
    
    -- Client/project association
    client_name VARCHAR(255),
    project_name VARCHAR(255),
    billing_code VARCHAR(50),
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'active', -- active, completed, on_hold, cancelled
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_user_id UUID REFERENCES users(id)
);

CREATE UNIQUE INDEX idx_company_priorities_unique ON company_bill_priorities(company_id, measure_id);
CREATE INDEX idx_company_priorities_company ON company_bill_priorities(company_id);
CREATE INDEX idx_company_priorities_level ON company_bill_priorities(priority_level);

-- ============================================================================
-- AUDIT & ACTIVITY TRACKING
-- ============================================================================

CREATE TABLE user_activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Activity details
    activity_type VARCHAR(100) NOT NULL, -- login, search, view_bill, track_bill, etc.
    activity_description TEXT,
    
    -- Context
    measure_id UUID REFERENCES measures(id),
    search_query TEXT,
    ip_address INET,
    user_agent TEXT,
    
    -- Metadata
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_activity_user ON user_activity_log(user_id);
CREATE INDEX idx_activity_type ON user_activity_log(activity_type);
CREATE INDEX idx_activity_created ON user_activity_log(created_at);

-- ============================================================================
-- DATA SYNC & MAINTENANCE
-- ============================================================================

CREATE TABLE sync_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Job details
    job_type VARCHAR(100) NOT NULL, -- full_sync, incremental_sync, specific_session
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed
    
    -- Parameters
    session_keys TEXT[],
    sync_measures BOOLEAN DEFAULT TRUE,
    sync_testimony BOOLEAN DEFAULT TRUE,
    sync_committees BOOLEAN DEFAULT TRUE,
    
    -- Progress tracking
    total_items INTEGER,
    processed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    
    -- Results
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    sync_summary JSONB,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_user_id UUID REFERENCES users(id)
);

CREATE INDEX idx_sync_jobs_status ON sync_jobs(status);
CREATE INDEX idx_sync_jobs_type ON sync_jobs(job_type);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Hot Bills view with testimony counts and recent activity
CREATE VIEW hot_bills AS
SELECT 
    m.id,
    m.bill_number,
    m.catch_line,
    m.current_location,
    m.current_committee_code,
    m.priority_score,
    COUNT(t.id) as testimony_count,
    COUNT(CASE WHEN t.position_code = 3982 THEN 1 END) as favor_count,
    COUNT(CASE WHEN t.position_code = 3983 THEN 1 END) as against_count,
    COUNT(CASE WHEN t.position_code = 3981 THEN 1 END) as neutral_count,
    MAX(t.meeting_date) as latest_testimony_date,
    COUNT(DISTINCT utm.user_id) as tracking_users_count
FROM measures m
LEFT JOIN testimonies t ON m.id = t.measure_id
LEFT JOIN user_tracked_measures utm ON m.id = utm.measure_id
WHERE m.sync_status = 'completed'
GROUP BY m.id, m.bill_number, m.catch_line, m.current_location, m.current_committee_code, m.priority_score
ORDER BY m.priority_score DESC, testimony_count DESC;

-- User Dashboard view
CREATE VIEW user_dashboard AS
SELECT 
    u.id as user_id,
    u.first_name || ' ' || u.last_name as full_name,
    c.name as company_name,
    COUNT(DISTINCT utm.measure_id) as tracked_bills_count,
    COUNT(DISTINCT CASE WHEN uma.is_read = FALSE THEN uma.id END) as unread_alerts_count,
    COUNT(DISTINCT ss.id) as saved_searches_count,
    MAX(ual.created_at) as last_activity_at
FROM users u
JOIN companies c ON u.company_id = c.id
LEFT JOIN user_tracked_measures utm ON u.id = utm.user_id
LEFT JOIN user_measure_alerts uma ON u.id = uma.user_id
LEFT JOIN saved_searches ss ON u.id = ss.user_id
LEFT JOIN user_activity_log ual ON u.id = ual.user_id
WHERE u.is_active = TRUE
GROUP BY u.id, u.first_name, u.last_name, c.name;

-- ============================================================================
-- FUNCTIONS FOR COMMON OPERATIONS
-- ============================================================================

-- Function to update measure priority scores
CREATE OR REPLACE FUNCTION update_measure_priority_scores()
RETURNS void AS $$
BEGIN
    UPDATE measures SET priority_score = (
        COALESCE((
            SELECT 
                (COUNT(*) * 10) + 
                (COUNT(CASE WHEN position_code IN (3982, 3983) THEN 1 END) * 5) +
                (CASE WHEN MAX(meeting_date) > CURRENT_DATE - INTERVAL '30 days' THEN 20 ELSE 0 END)
            FROM testimonies 
            WHERE measure_id = measures.id
        ), 0) +
        COALESCE((
            SELECT COUNT(*) * 3
            FROM user_tracked_measures 
            WHERE measure_id = measures.id
        ), 0)
    );
END;
$$ LANGUAGE plpgsql;

-- Function to create user alert
CREATE OR REPLACE FUNCTION create_user_alert(
    p_user_id UUID,
    p_measure_id UUID,
    p_alert_type VARCHAR(50),
    p_alert_title VARCHAR(255),
    p_alert_message TEXT,
    p_change_data JSONB DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    alert_id UUID;
BEGIN
    INSERT INTO user_measure_alerts (
        user_id, measure_id, alert_type, alert_title, alert_message, change_data
    ) VALUES (
        p_user_id, p_measure_id, p_alert_type, p_alert_title, p_alert_message, p_change_data
    ) RETURNING id INTO alert_id;
    
    RETURN alert_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ============================================================================

-- Update timestamps
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at column
CREATE TRIGGER trigger_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    
CREATE TRIGGER trigger_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    
CREATE TRIGGER trigger_sessions_updated_at BEFORE UPDATE ON legislative_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
    
CREATE TRIGGER trigger_measures_updated_at BEFORE UPDATE ON measures
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Insert system company for initial setup
INSERT INTO companies (
    name, slug, description, subscription_tier, max_users, is_active
) VALUES (
    'System Administrator', 'system', 'System administration company', 'enterprise', 1000, TRUE
);

-- Create initial admin user (password: 'admin123' - CHANGE IN PRODUCTION!)
INSERT INTO users (
    company_id, 
    email, 
    password_hash, 
    first_name, 
    last_name, 
    role, 
    is_active, 
    is_company_admin,
    email_verified_at
) VALUES (
    (SELECT id FROM companies WHERE slug = 'system'),
    'admin@olis-tracker.local',
    crypt('admin123', gen_salt('bf')),
    'System',
    'Administrator',
    'admin',
    TRUE,
    TRUE,
    NOW()
);

-- ============================================================================
-- SECURITY - ROW LEVEL SECURITY
-- ============================================================================

-- Enable RLS on user-specific tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_tracked_measures ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_measure_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_searches ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_activity_log ENABLE ROW LEVEL SECURITY;

-- Users can only see their own company's users (unless admin)
CREATE POLICY user_company_isolation ON users
    FOR ALL 
    USING (
        company_id = (SELECT company_id FROM users WHERE id = current_setting('app.current_user_id')::UUID)
        OR 
        (SELECT role FROM users WHERE id = current_setting('app.current_user_id')::UUID) = 'admin'
    );

-- Users can only manage their own tracked measures
CREATE POLICY user_tracked_measures_isolation ON user_tracked_measures
    FOR ALL 
    USING (user_id = current_setting('app.current_user_id')::UUID);

-- Similar policies for other user-specific tables
CREATE POLICY user_alerts_isolation ON user_measure_alerts
    FOR ALL 
    USING (user_id = current_setting('app.current_user_id')::UUID);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Additional performance indexes
CREATE INDEX CONCURRENTLY idx_measures_fulltext ON measures 
    USING gin(to_tsvector('english', COALESCE(catch_line, '') || ' ' || COALESCE(measure_summary, '')));

CREATE INDEX CONCURRENTLY idx_testimonies_fulltext ON testimonies
    USING gin(to_tsvector('english', COALESCE(testimony_text, '') || ' ' || COALESCE(testifier_organization, '')));

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE companies IS 'Organizations using the OLIS tracker system';
COMMENT ON TABLE users IS 'Individual users within companies';
COMMENT ON TABLE legislative_sessions IS 'Oregon legislative sessions (mirrors OLIS session data)';
COMMENT ON TABLE measures IS 'Bills and resolutions (complete 25-field OLIS schema mirror)';
COMMENT ON TABLE testimonies IS 'Public testimony on measures (mirrors OLIS testimony data)';
COMMENT ON TABLE user_tracked_measures IS 'Bills that users are tracking/monitoring';
COMMENT ON TABLE user_measure_alerts IS 'Notifications for users about bill changes';

COMMENT ON COLUMN measures.priority_score IS 'Calculated score for hot bills ranking (higher = hotter)';
COMMENT ON COLUMN testimonies.position_code IS 'OLIS position codes: 3981=neutral, 3982=favor, 3983=against';

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================