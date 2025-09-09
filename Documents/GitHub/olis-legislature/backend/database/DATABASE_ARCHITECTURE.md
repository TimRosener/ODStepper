# OLIS Legislature Tracker - Database Architecture

## Overview

This document describes the comprehensive database architecture for the OLIS Legislature Tracker system, including the extensible analysis framework designed for future expansion.

## Architecture Principles

### 1. **Clear Data Source Separation**
- **OLIS Import**: Raw legislative data from Oregon's OLIS API
- **Internal Generation**: User management, analysis, and insights created by our system

### 2. **Extensibility Through JSONB**
- Heavy use of PostgreSQL JSONB fields for flexible, schema-less storage
- Enables adding new analysis types without database migrations
- Supports evolving AI/ML model outputs

### 3. **Multi-Tenant Architecture**
- Row-level security for company data isolation
- UUID primary keys throughout for global uniqueness
- Company-based access control

## Data Sources

### 📥 **IMPORTED FROM OLIS API**

These tables mirror data from the Oregon Legislative Information System:

| Table | Description | Key Fields |
|-------|-------------|------------|
| `legislative_sessions` | Oregon legislative sessions | session_key, session_name, session_year |
| `measures` | Bills and resolutions (25 OLIS fields) | measure_prefix, measure_number, catch_line |
| `committees` | Legislative committees | committee_code, committee_name, chamber |
| `testimonies` | Public testimony | position_code (3981/3982/3983), testimony_text |
| `measure_sponsors` | Bill sponsors | sponsor_name, sponsor_type |

**OLIS Position Codes:**
- `3981` = Neutral
- `3982` = In Favor  
- `3983` = Against

### 💻 **GENERATED INTERNALLY**

These tables are created and managed by our system:

#### User & Company Management
| Table | Purpose |
|-------|---------|
| `companies` | Organizations using the system |
| `users` | Individual user accounts |
| `user_tracked_measures` | Bills users are monitoring |
| `user_measure_alerts` | Notification system |
| `company_bill_priorities` | Company-level bill tracking |

#### Extensible Analysis Framework
| Table | Purpose |
|-------|---------|
| `analysis_types` | Define types of analysis (testimony, fiscal, etc.) |
| `measure_analyses` | Store ANY type of analysis results |
| `amendment_analyses` | Amendment impact analysis |
| `analysis_configurations` | AI prompts and parameters |
| `analysis_history` | Complete audit trail |

## The Extensible Analysis Framework

### Core Design: Polymorphic Analysis Storage

The system uses a flexible pattern where ANY type of analysis can be stored without schema changes:

```sql
-- Define a new analysis type
INSERT INTO analysis_types (type_code, type_name, category)
VALUES ('sentiment_analysis', 'Public Sentiment Analysis', 'text');

-- Store analysis results in JSONB
INSERT INTO measure_analyses (
    measure_id, 
    analysis_type_id,
    raw_analysis,
    structured_data
) VALUES (
    'measure-uuid',
    'analysis-type-uuid',
    '{"raw_output": "AI model response..."}',
    '{"sentiment": 0.75, "topics": ["healthcare", "education"]}'
);
```

### Key Tables

#### `analysis_types`
Defines what kinds of analyses can be performed:
- `type_code`: Unique identifier (e.g., 'testimony_sentiment')
- `default_parameters`: JSONB configuration
- `default_prompt_template`: AI prompt template
- `auto_analyze`: Whether to run automatically

#### `measure_analyses`
Stores all analysis results with versioning:
- `raw_analysis`: JSONB - Raw AI/ML output
- `structured_data`: JSONB - Parsed results
- `confidence_scores`: JSONB - Confidence per component
- `is_current_version`: Latest analysis flag
- `analysis_version`: Track multiple runs

#### `analysis_configurations`
Manages different analysis approaches:
- `prompt_template`: Customizable prompts
- `parameters`: JSONB - Model parameters
- `is_experiment`: A/B testing support
- `validation_rules`: Quality checks

### Adding New Analysis Types (No Schema Changes!)

To add a new type of analysis in the future:

1. **Insert new analysis type:**
```sql
INSERT INTO analysis_types (type_code, type_name, category, description)
VALUES ('lobbying_influence', 'Lobbying Influence Analysis', 'stakeholder', 
        'Analyze lobbying patterns and influence on legislation');
```

2. **Store results in existing tables:**
```sql
INSERT INTO measure_analyses (measure_id, analysis_type_id, structured_data)
VALUES (
    'measure-id',
    'lobbying-analysis-type-id',
    '{
        "influence_score": 0.82,
        "key_lobbyists": ["Org A", "Org B"],
        "spending_estimate": 250000,
        "tactics": ["testimony", "meetings", "campaigns"]
    }'::jsonb
);
```

3. **Query the results:**
```sql
SELECT 
    m.bill_number,
    ma.structured_data->>'influence_score' as influence_score,
    ma.structured_data->'key_lobbyists' as lobbyists
FROM measure_analyses ma
JOIN measures m ON ma.measure_id = m.id
WHERE ma.analysis_type_id = 'lobbying-analysis-type-id';
```

## Future Analysis Capabilities

The framework supports adding these analyses WITHOUT database changes:

### Text Analysis
- **Testimony Sentiment**: Emotional analysis of public testimony
- **Bill Similarity**: Find related legislation
- **Amendment Impact**: Understand changes between versions
- **Readability Scoring**: Complexity analysis

### Stakeholder Analysis  
- **Interest Group Mapping**: Who supports/opposes
- **Lobbying Patterns**: Track influence networks
- **Geographic Impact**: Regional effects
- **Industry Analysis**: Business sector impacts

### Predictive Analytics
- **Passage Likelihood**: ML predictions of success
- **Timeline Forecasting**: When will bills move
- **Vote Prediction**: Likely voting patterns
- **Hot Bill Detection**: Automatic priority scoring

### Fiscal Analysis
- **Budget Impact**: Deep fiscal analysis
- **Revenue Projections**: Tax/fee implications
- **Cost-Benefit**: Economic modeling
- **Department Impact**: Agency-specific effects

### Legal Analysis
- **Constitutional Review**: Legal implications
- **Precedent Matching**: Similar past legislation
- **Regulatory Impact**: Administrative rule changes
- **Conflict Detection**: Laws that may conflict

## Database Performance Optimizations

### Indexing Strategy
- **B-tree indexes**: For exact matches (IDs, codes)
- **GIN indexes**: For JSONB queries
- **Partial indexes**: For filtered queries
- **Composite indexes**: For multi-column lookups

### Key Indexes
```sql
-- JSONB search optimization
CREATE INDEX idx_measure_analyses_raw_gin 
ON measure_analyses USING gin(raw_analysis);

-- Partial index for current analyses only
CREATE INDEX idx_measure_analyses_current 
ON measure_analyses(is_current_version) 
WHERE is_current_version = TRUE;

-- Full-text search on testimony
CREATE INDEX idx_testimonies_fulltext 
ON testimonies USING gin(
    to_tsvector('english', testimony_text)
);
```

## Security & Access Control

### Row-Level Security (RLS)
Companies can only see their own data:

```sql
-- Users see only their company's users
CREATE POLICY user_company_isolation ON users
FOR ALL USING (
    company_id = current_setting('app.current_user_id')::UUID
    OR role = 'admin'
);

-- Users see only their tracked measures
CREATE POLICY user_tracked_isolation 
ON user_tracked_measures
FOR ALL USING (
    user_id = current_setting('app.current_user_id')::UUID
);
```

### Data Privacy
- Password hashing with bcrypt
- No storage of sensitive data in logs
- Audit trails for compliance
- GDPR-ready data structure

## Migration Strategy

### Using Alembic
```bash
# Create new migration
alembic revision --autogenerate -m "Add new analysis type"

# Apply migrations
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Version Control
- Each schema change tracked in `schema_versions` table
- Alembic manages migration history
- Rollback capabilities for all changes

## Maintenance & Operations

### Regular Tasks
1. **Update OLIS data**: Sync with Oregon API
2. **Run analyses**: Process new bills/testimony
3. **Clean old analyses**: Archive expired results
4. **Update statistics**: Refresh materialized views

### Monitoring Queries
```sql
-- Check analysis backlog
SELECT COUNT(*) FROM measure_analyses 
WHERE status = 'pending';

-- Recent analysis performance
SELECT 
    analysis_type_id,
    AVG(processing_time_ms) as avg_time,
    AVG(overall_confidence) as avg_confidence
FROM measure_analyses
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY analysis_type_id;
```

## Example Use Cases

### 1. Adding Sentiment Analysis
```python
# Define analysis type
analysis_type = create_analysis_type(
    type_code='testimony_sentiment',
    type_name='Testimony Sentiment Analysis',
    default_model='gpt-4'
)

# Run analysis
result = analyze_testimony(testimony_id, analysis_type_id)

# Store results
save_analysis(
    measure_id=testimony.measure_id,
    analysis_type_id=analysis_type.id,
    structured_data={
        'sentiment': result.sentiment_score,
        'emotions': result.emotion_breakdown,
        'key_phrases': result.important_phrases
    }
)
```

### 2. Querying Analysis Results
```sql
-- Get all analyses for a bill
SELECT 
    at.type_name,
    ma.summary,
    ma.overall_confidence,
    ma.created_at
FROM measure_analyses ma
JOIN analysis_types at ON ma.analysis_type_id = at.id
WHERE ma.measure_id = 'bill-uuid'
AND ma.is_current_version = TRUE;
```

### 3. Company-Specific Views
```sql
-- Company's high-priority bills with recent analysis
SELECT 
    m.bill_number,
    m.catch_line,
    cbp.priority_level,
    ma.structured_data->>'risk_score' as risk_score
FROM company_bill_priorities cbp
JOIN measures m ON cbp.measure_id = m.id
LEFT JOIN measure_analyses ma ON m.id = ma.measure_id
WHERE cbp.company_id = 'company-uuid'
AND cbp.priority_level = 'critical'
ORDER BY ma.created_at DESC;
```

## Conclusion

This architecture provides:
- ✅ **Complete OLIS data mirroring** with 25-field bill structure
- ✅ **Extensible analysis framework** using JSONB for flexibility
- ✅ **Multi-tenant support** with row-level security
- ✅ **Future-proof design** for adding new analysis types
- ✅ **Performance optimized** with proper indexing
- ✅ **Audit trails** for compliance and debugging

The key innovation is the **polymorphic analysis storage** pattern that allows adding ANY type of analysis without database schema changes, making the system infinitely extensible for future AI/ML capabilities.