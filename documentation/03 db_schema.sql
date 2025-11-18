-- Purpose
-- The "What" for the data layer. Crucial for consistency across the 'Body' and 'Brain' services.

-- What to Include
-- The full, current SQL Data Definition Language (DDL) for all tables, indexes, extensions (pgvector), and Row-Level Security (RLS) policies.

-- CRITICAL INSTRUCTION: Any schema change that involves user-owned data MUST include RLS using get_current_user_id().

# 03_DB_SCHEMA.sql: Current Database Schema (Version 1.1) - Cultivate → Execute → Contribute

-- =========================================================================
-- 0. EXTENSIONS & RLS SETUP
-- =========================================================================

-- Ensure the vector extension is enabled (required for pgvector)
CREATE EXTENSION IF NOT EXISTS vector;

-- Set a custom configuration setting that the application will use to hold the authenticated user's ID.
-- The application must execute: SET app.current_user_id = 'the-user-uuid';
ALTER DATABASE postgres SET app.current_user_id TO '';

-- Define a reusable function to get the current user ID from the application context.
CREATE OR REPLACE FUNCTION get_current_user_id()
RETURNS UUID AS $$
    SELECT current_setting('app.current_user_id', true)::UUID;
$$ LANGUAGE SQL STABLE;


-- =========================================================================
-- 1. USER AUTHENTICATION & PROFILE
-- =========================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password BYTEA NOT NULL,
    username VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- The 'users' table is updated to support different roles for RLS and portal access.
ALTER TABLE users ADD COLUMN user_type VARCHAR(20) NOT NULL DEFAULT 'PRIMARY' 
    CHECK (user_type IN ('PRIMARY', 'PROFESSIONAL', 'RESEARCHER'));

-- =========================================================================
-- 2. ACTIONABLE ITEMS (The 'Goal/Task' definition - EXECUTE component)
-- =========================================================================

CREATE TABLE actionable_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Key for H1 (Execution Quality)
    item_type VARCHAR(50) NOT NULL CHECK (item_type IN ('HOLISTIC', 'MANDATED')), 

    priority SMALLINT DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    is_recurring BOOLEAN NOT NULL DEFAULT FALSE,
    recurrence_pattern VARCHAR(50), 
    
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- The 'user_preferences' table is updated to store the user-defined Synthesis Matrix.
-- This JSONB object controls data retrieval and weighting for the Cognitive Engine.
ALTER TABLE user_preferences ADD COLUMN synthesis_matrix JSONB;

-- ------------------------------
-- RLS Policy on actionable_items
-- ------------------------------
ALTER TABLE actionable_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_isolation_action_items ON actionable_items
    USING (user_id = get_current_user_id())
    WITH CHECK (user_id = get_current_user_id());


-- =========================================================================
-- 3. ADHERENCE LOG (The 'Execution' tracking - EXECUTE component)
-- =========================================================================

CREATE TABLE adherence_log (
    actionable_item_id UUID NOT NULL REFERENCES actionable_items(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id), -- Redundant user_id for RLS and query performance
    log_date DATE NOT NULL,
    
    status VARCHAR(50) NOT NULL CHECK (status IN ('COMPLETE', 'INCOMPLETE', 'SKIPPED')),
    notes TEXT,
    
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (actionable_item_id, log_date)
);

-- ------------------------------
-- RLS Policy on adherence_log
-- ------------------------------
ALTER TABLE adherence_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_isolation_adherence_log ON adherence_log
    USING (user_id = get_current_user_id())
    WITH CHECK (user_id = get_current_user_id());


-- =========================================================================
-- 4. DOCUMENTS (Unstructured Cognitive Data - CULTIVATE component)
-- =========================================================================

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    
    document_type VARCHAR(50) NOT NULL CHECK (document_type IN ('DREAM', 'SPIRITUAL', 'QNA_USER')), 
    
    content TEXT NOT NULL,
    source_metadata JSONB, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------
-- RLS Policy on documents
-- ------------------------------
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_isolation_documents ON documents
    USING (user_id = get_current_user_id())
    WITH CHECK (user_id = get_current_user_id());


-- =========================================================================
-- 5. HEALTH METRICS (Structured Clinical Data - CONTRIBUTE component)
-- =========================================================================

CREATE TABLE health_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    
    metric_name VARCHAR(100) NOT NULL CHECK (metric_name IN ('RHR', 'SLEEP_SCORE', 'BLOOD_GLUCOSE', 'WEIGHT')),
    
    metric_value DOUBLE PRECISION NOT NULL,
    unit VARCHAR(50), 
    
    recorded_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    
    source_metadata JSONB, 
    
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------
-- RLS Policy on health_metrics
-- ------------------------------
ALTER TABLE health_metrics ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_isolation_health_metrics ON health_metrics
    USING (user_id = get_current_user_id())
    WITH CHECK (user_id = get_current_user_id());


-- =========================================================================
-- 6. VECTOR STORAGE (Digital Memory - Supports CULTIVATE retrieval)
-- =========================================================================

CREATE TABLE document_vectors (
    document_id UUID PRIMARY KEY REFERENCES documents(id) ON DELETE CASCADE,
    embedding VECTOR(1536) NOT NULL,
    
    user_id UUID NOT NULL REFERENCES users(id) -- Required for security filtering (PoLP)
);

-- ------------------------------
-- RLS Policy on document_vectors
-- ------------------------------
ALTER TABLE document_vectors ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_isolation_document_vectors ON document_vectors
    USING (user_id = get_current_user_id())
    WITH CHECK (user_id = get_current_user_id());

-- =========================================================================
-- 7. USER PREFERENCES (Configuration - Supports all components)
-- =========================================================================

CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE, -- One-to-one relationship with users
    
    -- Advisor Naming
    advisor_name_spiritual VARCHAR(100) DEFAULT 'The Cultivator',
    advisor_name_action VARCHAR(100) DEFAULT 'The Executor',
    advisor_name_health VARCHAR(100) DEFAULT 'The Contributor',

    -- Spiritual Advisor Configuration (Used by the Cognitive Engine)
    spiritual_mode VARCHAR(50) NOT NULL CHECK (spiritual_mode IN ('TAROT', 'GOD', 'NEUTRAL')) DEFAULT 'NEUTRAL', 
    spiritual_tone VARCHAR(50) NOT NULL CHECK (spiritual_tone IN ('GUIDANCE', 'MENTOR', 'EXPERT')) DEFAULT 'MENTOR',
    
    -- Health Advisor Configuration (Data Ingestion)
    health_data_ingestion VARCHAR(50) NOT NULL CHECK (health_data_ingestion IN ('APPLE_HEALTH', 'DIRECT_DB')) DEFAULT 'DIRECT_DB',
    
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Stores explicit, revokable consent for professionals (Secondary Users) to access a Primary User's data.
CREATE TABLE data_access_grants (
    grant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    primary_user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    professional_user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    
    -- Defines granular, user-scoped consent (e.g., {"health_metrics": true, "cultivate_data": false, "start_date": "YYYY-MM-DD"})
    access_scope JSONB NOT NULL, 
    
    granted_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP WITHOUT TIME ZONE, -- If populated, access is denied.
    
    UNIQUE (primary_user_id, professional_user_id)
);

-- RLS POLICY UPDATE MANDATE (CRITICAL):
-- All RLS-enabled tables (documents, health_metrics, adherence_log, etc.) MUST be updated 
-- to allow access if: 
-- 1. current_user_id = row.user_id (Primary User access), OR
-- 2. current_user_id is in data_access_grants AND the grant is NOT revoked AND the access_scope 
--    permits the data type being queried.

-- ---------------------------------
-- RLS Policy on user_preferences (CRITICAL)
-- ---------------------------------
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_isolation_preferences ON user_preferences
    USING (user_id = get_current_user_id())
    WITH CHECK (user_id = get_current_user_id());

-- Index for performance on the primary access column
CREATE INDEX idx_preferences_user ON user_preferences (user_id);

-- =========================================================================
-- 8. COGNITIVE DEFINITIONS (System Configuration - Non-RLS Global Data)
-- =========================================================================

-- Stores the base prompts, modifier prompts (e.g., 'TAROT' mode), and roles 
-- for the Cognitive Engine (The Brain).
CREATE TABLE cognitive_definitions (
    definition_key VARCHAR(100) PRIMARY KEY, -- Unique key (e.g., 'CULTIVATE_BASE', 'CULTIVATE_MODE_TAROT')
    
    advisor_role VARCHAR(50) NOT NULL CHECK (advisor_role IN ('CULTIVATE', 'EXECUTE', 'CONTRIBUTE')), -- The macro-advisor this definition belongs to
    
    -- The core instruction/prompt text used by the LLM
    system_prompt_template TEXT NOT NULL,
    
    description VARCHAR(255), -- Internal description for admin/version control
    version INT NOT NULL DEFAULT 1,
    
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- NOTE: This table is not RLS-enabled. It contains global configuration
-- accessible by the Engine's full-privilege user (`cognitive_engine_full`).

-- Stores aggregated, anonymized metrics to measure the system's effectiveness 
-- against the core hypotheses (H1, H2, H3).
CREATE TABLE cognitive_efficacy_metrics (
    metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- The hypothesis or area being measured (e.g., 'H3_OVERALL_ADHERENCE', 'H2_PREDICTION_ACCURACY')
    metric_key VARCHAR(100) NOT NULL, 
    
    -- The calculated effectiveness score (e.g., 0.84 for 84% adherence)
    metric_value NUMERIC(5, 4) NOT NULL, 
    
    time_period_start DATE NOT NULL,
    
    -- Optional: Allows filtering metrics by advisor or cohort
    advisor_scope VARCHAR(50), 
    cohort_identifier VARCHAR(50), 
    
    calculated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- NOTE: This table is not RLS-enabled. It contains global, aggregate metrics
-- for the Engine Service's internal analytics/reporting system.

-- =========================================================================
-- 9. INDEXES FOR PERFORMANCE
-- =========================================================================

CREATE INDEX idx_actionable_user_type ON actionable_items (user_id, item_type);
CREATE INDEX idx_adherence_user_date ON adherence_log (user_id, log_date);
CREATE INDEX idx_documents_user_type ON documents (user_id, document_type);
CREATE INDEX idx_health_metrics_user_date ON health_metrics (user_id, recorded_at);
CREATE INDEX idx_preferences_user ON user_preferences (user_id);
```eof