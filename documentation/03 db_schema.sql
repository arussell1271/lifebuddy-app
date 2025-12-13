-- Purpose
-- The "What" for the data layer. Crucial for consistency across the 'Body' and 'Brain' services.

-- What to Include
-- The full, current SQL Data Definition Language (DDL) for all tables, indexes, extensions (pgvector), and Row-Level Security (RLS) policies.

-- CRITICAL INSTRUCTION: Any schema change that involves user-owned data MUST include RLS using get_current_user_id().

-- 03_DB_SCHEMA.sql: Current Database Schema (Version 1.2 - Consolidated DDL) - Cultivate → Execute → Contribute

-- =========================================================================
-- 0. EXTENSIONS & RLS SETUP
-- =========================================================================

-- Ensure the vector extension is enabled (required for pgvector)
CREATE EXTENSION IF NOT EXISTS vector;
-- Ensure uuid-ossp is enabled (used by data_access_grants)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; 

-- =========================================================================
-- 1. ENGINE SERVICE ROLES SETUP (MANDATORY RLS ENFORCEMENT)
-- =========================================================================

-- Role 1: 'cognitive_engine_full'
-- Purpose: For Administrative/Maintenance tasks ONLY (e.g., nightly purge, schema updates).
-- This role MUST NOT be used for serving live user requests. It BYPASSES RLS.
-- REPLACE 'ChangeThisToYourActualPassword' with the value from your .env file
DO
$$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'cognitive_engine_full') THEN
        -- NOTE: This line requires substituting the actual password if running manually in pgAdmin.
        -- When run via Docker (after init.sql), this block is skipped, so the password here doesn't matter.
        EXECUTE 'CREATE ROLE cognitive_engine_full WITH LOGIN PASSWORD ''FULL_ACCESS_PASS_CRITICAL''';
    END IF;
END
$$;

-- Role 2: 'cognitive_engine_rls'
-- Purpose: For Standard User Operations (App Service Proxy).
-- This role MUST be used for all user-facing queries. It ENFORCES RLS.
-- REPLACE 'ChangeThisToYourActualPassword' with the value from your .env file
DO
$$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'cognitive_engine_rls') THEN
        -- NOTE: This line requires substituting the actual password if running manually in pgAdmin.
        EXECUTE 'CREATE ROLE cognitive_engine_rls WITH LOGIN PASSWORD ''RLS_ACCESS_PASS_CRITICAL''';
    END IF;
END
$$;

-- GRANT PERMISSIONS
-- Allow these roles to connect to the specific database
GRANT CONNECT ON DATABASE postgres TO cognitive_engine_full;
GRANT CONNECT ON DATABASE postgres TO cognitive_engine_rls;

-- Grant usage on schema public
GRANT USAGE ON SCHEMA public TO cognitive_engine_full;
GRANT USAGE ON SCHEMA public TO cognitive_engine_rls;


-- Set a custom configuration setting that the application will use to hold the authenticated user's ID.
-- The Engine RLS Proxy MUST execute: SET app.current_user_id = 'the-user-uuid';
ALTER DATABASE postgres SET app.current_user_id TO '';


-- The application context setting used for Row-Level Security: 
-- The Engine RLS Proxy MUST execute: SELECT set_config('app.current_user_id', 'the-user-uuid', FALSE); 
-- RLS policies will reference this setting directly: current_setting('app.current_user_id')::uuid 

-- =========================================================================
-- 0.5. RLS HELPER FUNCTION
-- =========================================================================
-- Function to retrieve the current user's ID from the application context
CREATE OR REPLACE FUNCTION get_current_user_id() 
RETURNS UUID 
LANGUAGE sql 
STABLE 
AS $$ 
    SELECT NULLIF(current_setting('app.current_user_id', TRUE), '')::uuid; 
$$;

-- =========================================================================
-- 1.5 USERS (Identity & Auth Root)
-- =========================================================================

CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL, -- **CRITICAL ADDITION:** Required for login as per functional specification
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    
    -- Metadata
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Enable RLS immediately so Section 11 policies can attach later
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- =========================================================================
-- 2. USER PREFERENCES (Configuration - Supports all components)
-- =========================================================================

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE, -- One-to-one relationship with users
    
    -- Advisor Naming
    advisor_name_spiritual VARCHAR(100) DEFAULT 'The Cultivator',
    advisor_name_action VARCHAR(100) DEFAULT 'The Executor',
    advisor_name_health VARCHAR(100) DEFAULT 'The Contributor',
    
    -- User-defined Synthesis Matrix (Consolidated from ALTER)
    synthesis_matrix JSONB,

    -- Spiritual Advisor Configuration (Used by the Cognitive Engine)
    spiritual_mode VARCHAR(50) NOT NULL CHECK (spiritual_mode IN ('TAROT', 'GOD', 'NEUTRAL')) DEFAULT 'NEUTRAL', 
    spiritual_tone VARCHAR(50) NOT NULL CHECK (spiritual_tone IN ('GUIDANCE', 'MENTOR', 'EXPERT')) DEFAULT 'MENTOR',
    
    -- Health Advisor Configuration (Data Ingestion)
    health_data_ingestion VARCHAR(50) NOT NULL CHECK (health_data_ingestion IN ('APPLE_HEALTH', 'DIRECT_DB')) DEFAULT 'DIRECT_DB',
    
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Stores explicit, revokable consent for professionals (Secondary Users) to access a Primary User's data.
CREATE TABLE IF NOT EXISTS data_access_grants (
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
-- RLS Policy on user_preferences (PRIMARY ISOLATION ONLY) 
-- --------------------------------- 
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY; 
DROP POLICY IF EXISTS user_isolation_preferences ON user_preferences; 
CREATE POLICY user_isolation_preferences ON user_preferences 
-- CRITICAL FIX: Use the project's standard RLS context setting 
    USING (user_id = current_setting('app.current_user_id')::uuid) 
    WITH CHECK (user_id = current_setting('app.current_user_id')::uuid); 
        
ALTER TABLE user_preferences FORCE ROW LEVEL SECURITY;

-- Index for performance on the primary access column (moved to section 12)

ALTER TABLE data_access_grants ENABLE ROW LEVEL SECURITY; 
CREATE POLICY user_isolation_data_access_grants ON data_access_grants 
    USING (primary_user_id = current_setting('app.current_user_id')::uuid) 
    WITH CHECK (primary_user_id = current_setting('app.current_user_id')::uuid); 
    
ALTER TABLE data_access_grants FORCE ROW LEVEL SECURITY;


-- =========================================================================
-- 3. ACTIONABLE ITEMS (The 'Goal/Task' definition - EXECUTE component)
-- =========================================================================

CREATE TABLE IF NOT EXISTS actionable_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
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

-- ------------------------------ 
-- RLS Policy on actionable_items (DUAL-MODE ACCESS IMPLEMENTED) 
-- ------------------------------ 
ALTER TABLE actionable_items ENABLE ROW LEVEL SECURITY; 
DROP POLICY IF EXISTS user_isolation_action_items ON actionable_items; 
CREATE POLICY user_isolation_action_items ON actionable_items 
    USING ( -- Condition 1: Primary Owner Isolation 
        (user_id = current_setting('app.current_user_id')::uuid) 
    OR ( -- Condition 2: Delegated Access (Grantee must be active and scoped) 
    EXISTS ( SELECT 1 FROM data_access_grants dag WHERE dag.primary_user_id = actionable_items.user_id 
        AND dag.professional_user_id = current_setting('app.current_user_id')::uuid 
        AND dag.revoked_at IS NULL 
        -- MANDATORY: Granular scope check for this data type 
        AND dag.access_scope -> 'action_items' ? 'read' 
        ) ) ) 
        -- Write Isolation: Only Primary Owner can modify/insert 
        WITH CHECK (user_id = current_setting('app.current_user_id')::uuid); 

ALTER TABLE actionable_items FORCE ROW LEVEL SECURITY;

-- =========================================================================
-- 4. ADHERENCE LOG (The 'Execution' tracking - EXECUTE component)
-- =========================================================================

CREATE TABLE IF NOT EXISTS adherence_log (
    actionable_item_id UUID NOT NULL REFERENCES actionable_items(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id), -- Redundant user_id for RLS and query performance
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
-- 5. DOCUMENTS (Unstructured Cognitive Data - CULTIVATE component)
-- =========================================================================

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    
    document_type VARCHAR(50) NOT NULL CHECK (document_type IN ('DREAM', 'SPIRITUAL', 'QNA_USER')), 
    
    content TEXT NOT NULL,
    source_metadata JSONB, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------
-- DUAL-MODE RLS POLICY TEMPLATE (Replace ALL policy blocks for user-owned data tables)
-- Example for 'documents' table (Replace documents with table name and scope key)
-- ------------------------------
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS user_isolation_documents ON documents;
CREATE POLICY user_isolation_documents
    ON documents
    USING (
        -- Condition 1: Primary Owner Isolation
        (user_id = current_setting('app.current_user_id')::uuid) 
        OR
        (
            -- Condition 2: Delegated Access via Active Grant WITH Granular Scope Check
            EXISTS (
                SELECT 1
                FROM data_access_grants dag
                WHERE dag.primary_user_id = documents.user_id             
                  AND dag.professional_user_id = current_setting('app.current_user_id')::uuid
                  AND dag.revoked_at IS NULL
                  -- MANDATORY: JSONB check using the appropriate scope key
                  AND dag.access_scope -> 'documents' ? 'read' 
            )
        )
    )
    -- Write isolation remains for the primary user only
    WITH CHECK (user_id = current_setting('app.current_user_id')::uuid); 

ALTER TABLE documents FORCE ROW LEVEL SECURITY;


-- =========================================================================
-- 6. HEALTH METRICS (Structured Clinical Data - CONTRIBUTE component)
-- =========================================================================

CREATE TABLE IF NOT EXISTS health_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    
    metric_name VARCHAR(100) NOT NULL CHECK (metric_name IN ('RHR', 'SLEEP_SCORE', 'BLOOD_GLUCOSE', 'WEIGHT')),
    
    metric_value DOUBLE PRECISION NOT NULL,
    unit VARCHAR(50), 
    
    recorded_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    
    source_metadata JSONB, 
    
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------
-- RLS Policy on health_metrics (DUAL-MODE ACCESS IMPLEMENTED)
-- ----------------------------------------------------
ALTER TABLE health_metrics ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS user_isolation_health_metrics ON health_metrics;

CREATE POLICY user_isolation_health_metrics
    ON health_metrics
    USING (
        -- Condition 1: Primary Owner Isolation
        (user_id = current_setting('app.current_user_id')::uuid) 
        OR
        (
            -- Condition 2: Delegated Access (Grantee must be active and scoped)
            EXISTS (
                SELECT 1
                FROM data_access_grants dag
                WHERE dag.primary_user_id = health_metrics.user_id              
                  AND dag.professional_user_id = current_setting('app.current_user_id')::uuid
                  AND dag.revoked_at IS NULL
                  -- MANDATORY: Granular scope check for Health Metrics
                  AND dag.access_scope -> 'health_metrics' ? 'read' 
            )
        )
    )
    -- Write Isolation: Only Primary Owner can modify/insert
    WITH CHECK (user_id = current_setting('app.current_user_id')::uuid);

ALTER TABLE health_metrics FORCE ROW LEVEL SECURITY;

-- =========================================================================
-- 7. VECTOR STORAGE (Digital Memory - Supports CULTIVATE retrieval)
-- =========================================================================

CREATE TABLE IF NOT EXISTS document_vectors (
    document_id UUID PRIMARY KEY REFERENCES documents(id) ON DELETE CASCADE,
    embedding VECTOR(1536) NOT NULL,
    
    user_id UUID NOT NULL REFERENCES users(user_id) -- Required for security filtering (PoLP)
);

-- ------------------------------
-- RLS Policy on document_vectors
-- ------------------------------
ALTER TABLE document_vectors ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_isolation_document_vectors ON document_vectors
    USING (user_id = get_current_user_id())
    WITH CHECK (user_id = get_current_user_id());


-- =========================================================================
-- 8. COGNITIVE DEFINITIONS (System Configuration - Non-RLS Global Data)
-- =========================================================================

-- Stores the base prompts, modifier prompts (e.g., 'TAROT' mode), and roles 
-- for the Cognitive Engine (The Brain).
CREATE TABLE IF NOT EXISTS cognitive_definitions (
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
CREATE TABLE IF NOT EXISTS cognitive_efficacy_metrics (
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
-- 9. PRE-SYNTHESIS QUESTIONS (Engine Configuration Data)
-- =========================================================================

CREATE TABLE IF NOT EXISTS pre_synthesis_questions (
    question_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- The advisor area this question belongs to: 'CULTIVATE', 'EXECUTE', 'CONTRIBUTE'
    advisor_type VARCHAR(50) NOT NULL 
        CHECK (advisor_type IN ('CULTIVATE', 'EXECUTE', 'CONTRIBUTE')),
        
    question_text TEXT NOT NULL UNIQUE, -- ADDED UNIQUE CONSTRAINT HERE
    
    -- Expected answer format to guide the client (e.g., 'TEXT', 'NUMBER', 'DATE')
    expected_format VARCHAR(50) NOT NULL, 
    
    -- Priority for ordering the questions in the client UI
    display_order INTEGER DEFAULT 1,
    
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);

-- NOTE: This table is NOT RLS-enabled. It contains global system data.

-- =========================================================================
-- 10. USER COGNITIVE STATE (Daily Check Gating Mechanism)
-- =========================================================================

-- Tracks the completion status of mandatory daily/contextual questions per user.
-- CRITICAL RETENTION MANDATE: Data MUST be purged after a 4-day rolling window.

CREATE TABLE IF NOT EXISTS user_cognitive_state (
    user_id UUID NOT NULL REFERENCES users(user_id),
    
    -- Date of the status check (ensures a reset every day)
    state_date DATE NOT NULL DEFAULT CURRENT_DATE, 
    
    -- ID of the mandatory question being tracked (from pre_synthesis_questions)
    question_id UUID NOT NULL REFERENCES pre_synthesis_questions(question_id),
    
    -- The answer provided by the user (or extracted implicitly by the Engine)
    user_answer TEXT,
    
    -- Status flag: 'PENDING', 'ANSWERED_EXPLICIT', 'ANSWERED_IMPLICIT'
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING' 
        CHECK (status IN ('PENDING', 'ANSWERED_EXPLICIT', 'ANSWERED_IMPLICIT')),
    
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (user_id, state_date, question_id) 
);

-- ------------------------------
-- RLS Policy on user_cognitive_state (MANDATORY)
-- ------------------------------
ALTER TABLE user_cognitive_state ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_isolation_cognitive_state ON user_cognitive_state
    USING (user_id = get_current_user_id())
    WITH CHECK (user_id = get_current_user_id());
    
CREATE INDEX idx_cognitive_state_user_date ON user_cognitive_state (user_id, state_date, status);

-- =========================================================================
-- 11. TABLE: pre_synthesis_answers
-- Purpose: Stores the user's daily answers to mandatory pre-synthesis questions.
-- This data is a prerequisite for the Cognitive Synthesis process.
-- =========================================================================
CREATE TABLE IF NOT EXISTS pre_synthesis_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES pre_synthesis_questions(question_id) ON DELETE RESTRICT, 
    answer_text TEXT NOT NULL, -- Stores the user's textual or numerical answer
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'ANSWERED_EXPLICIT', 'ANSWERED_IMPLICIT')),
    log_date DATE NOT NULL DEFAULT CURRENT_DATE, -- Tracks the calendar day for the answer
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- CRITICAL CONSTRAINT: A user can only answer a specific question once per day.
    UNIQUE (user_id, question_id, log_date)
);

-- RLS Enforcement: Enforce Row-Level Security (PoLP)
ALTER TABLE pre_synthesis_answers ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_access_pre_synthesis_answers ON pre_synthesis_answers
    USING (user_id = get_current_user_id())
    WITH CHECK (user_id = get_current_user_id());

-- Index for fast lookup by user and day
CREATE INDEX idx_pre_synthesis_answers_user_date ON pre_synthesis_answers (user_id, log_date);

-- =========================================================================
-- 12. CRITICAL ROW-LEVEL SECURITY (RLS) POLICIES
--     MANDATORY ENFORCEMENT using get_current_user_id() for multi-tenancy.
-- =========================================================================

-- Ensure RLS is enabled on the users table (if not already)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Drop existing policy if running the script multiple times
DROP POLICY IF EXISTS rls_users_isolation ON users;

-- Users Table: Primary users can only see their own record (uses 'user_id').
CREATE POLICY rls_users_isolation ON users
    FOR ALL
    -- CRITICAL FIX: Changed 'id' to 'user_id'
    USING (user_id = get_current_user_id())
    WITH CHECK (user_id = get_current_user_id());

-- =========================================================================
-- 13. STORED PROCEDURES (MAINTENANCE & PURGE)
-- =========================================================================

-- Procedure to enforce the 4-Day Rolling Window for user_cognitive_state AND pre_synthesis_answers.
-- This MUST be run by a privileged user (e.g., 'cognitive_engine_full') on a nightly schedule.
CREATE OR REPLACE PROCEDURE db_maintenance_purge_old_state()
LANGUAGE plpgsql
AS $$
DECLARE
    state_deleted_count INTEGER;
    answers_deleted_count INTEGER;
BEGIN
    RAISE NOTICE 'Starting purge of transient data older than 4 days...';

    -- 1. Purge Old User Cognitive State
    DELETE FROM user_cognitive_state
    WHERE created_at < NOW() - INTERVAL '4 days';
    GET DIAGNOSTICS state_deleted_count = ROW_COUNT;

    -- 2. Purge Old Pre-Synthesis Answers (New Requirement)
    DELETE FROM pre_synthesis_answers
    WHERE created_at < NOW() - INTERVAL '4 days';
    GET DIAGNOSTICS answers_deleted_count = ROW_COUNT;

    -- Log the operation success with counts
    RAISE NOTICE 'Purge complete: % user_cognitive_state rows deleted, % pre_synthesis_answers rows deleted.', state_deleted_count, answers_deleted_count;
END;
$$;

-- DEVOPS REQUIREMENT: Ensure a privileged cron task is configured to execute: 
-- CALL db_maintenance_purge_old_state(); once daily.

-- =========================================================================
-- 14. MANDATORY SEED DATA (DML) - Application Fails Without This 🚨
-- =========================================================================

-- Purpose: Contains all mandatory Data Manipulation Language (DML) statements to populate
-- application-critical tables that define business logic.

-- 14.1 SEED DATA: cognitive_definitions (LLM Prompt Templates/Initial Prompts)

-- Defines the core prompt used for the CULTIVATE Synthesis phase.
INSERT INTO cognitive_definitions (definition_key, system_prompt_template, advisor_role) VALUES
('CULTIVATE_SYNTHESIS_PROMPT', 
'You are an analytical, non-judgmental health coach. Your task is to review the provided user journal entries, dream logs, and actionable item adherence history. Identify the single most dominant "Limiting Subconscious Misalignment" theme. Your output MUST be a JSON object: {"theme": "THEME_NAME", "summary": "CONCISE_EXPLANATION"}.',
'CULTIVATE')
ON CONFLICT (definition_key) DO NOTHING;

-- Defines the prompt used for the EXECUTE Action Item generation phase.
INSERT INTO cognitive_definitions (definition_key, system_prompt_template, advisor_role) VALUES
('EXECUTE_ITEM_GENERATION_PROMPT', 
'Based on the identified Limiting Subconscious Misalignment (THEME: {theme}), generate a single "Holistic Actionable Item" (identity-focused, not task-focused) to address it. Your output MUST be a JSON object: {"title": "ITEM_TITLE", "description": "ITEM_DESCRIPTION"}.',
'EXECUTE')
ON CONFLICT (definition_key) DO NOTHING;


-- 14.2 SEED DATA: pre_synthesis_questions (Mandatory Daily Check)

-- Essential questions to gather CULTIVATE/EXECUTE data before full Synthesis.
-- Essential questions to gather CULTIVATE/EXECUTE data before full Synthesis.
INSERT INTO pre_synthesis_questions (question_text, advisor_type, expected_format, display_order) VALUES
('What was the dominant emotion in your most recent dream?', 'CULTIVATE', 'single-word emotion', 1),
('What is the single most important action item you failed to adhere to yesterday?', 'EXECUTE', 'short description or item reference', 2),
('On a scale of 1 to 10 (10 being fully aligned), how aligned do you feel with your future self today?', 'CULTIVATE', 'integer 1-10', 3)
-- The single ON CONFLICT clause applies to all rows above
ON CONFLICT (question_text) DO NOTHING;

-- =========================================================================
-- 15. SYNTHESIS_LOG (The Digital Memory / Cultivate Data Store)
-- This table stores the results of the Cognitive Engine's analysis, including
-- the vectors used for Disalignment Frequency Count (DFC) lookups.
-- =========================================================================
CREATE TABLE IF NOT EXISTS synthesis_log (
    synthesis_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- The Core Insight: Extracted Limiting Subconscious Theme (e.g., 'Fear of Commitment')
    theme_title VARCHAR(255) NOT NULL,
    
    -- The Vector Representation of the Theme (pgvector required)
    theme_vector vector(1536) NOT NULL, -- Assuming OpenAI/Cohere 1536 dimension standard
    
    -- Summary of the synthesis run (LLM output)
    synthesis_summary TEXT NOT NULL, 
    
    -- Count of related documents/data points used in this synthesis run
    data_points_analyzed INTEGER NOT NULL DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- MANDATORY RLS ENFORCEMENT for the new table
ALTER TABLE synthesis_log ENABLE ROW LEVEL SECURITY;

-- ----------------------------------------------------
-- RLS Policy on synthesis_log (DUAL-MODE ACCESS IMPLEMENTED)
-- ----------------------------------------------------
DROP POLICY IF EXISTS user_isolation_synthesis_log ON synthesis_log;

CREATE POLICY user_isolation_synthesis_log
    ON synthesis_log
    USING (
        -- Condition 1: Primary Owner Isolation
        (user_id = current_setting('app.current_user_id')::uuid) 
        OR
        (
            -- Condition 2: Delegated Access (Grantee must be active and scoped)
            EXISTS (
                SELECT 1
                FROM data_access_grants dag
                WHERE dag.primary_user_id = synthesis_log.user_id              
                  AND dag.professional_user_id = current_setting('app.current_user_id')::uuid
                  AND dag.revoked_at IS NULL
                  -- MANDATORY: Granular scope check for Synthesis Log
                  AND dag.access_scope -> 'synthesis_log' ? 'read' 
            )
        )
    )
    -- Write Isolation: Only Primary Owner can modify/insert
    WITH CHECK (user_id = current_setting('app.current_user_id')::uuid);

ALTER TABLE synthesis_log FORCE ROW LEVEL SECURITY;

-- =========================================================================
-- 15. INDEXES FOR PERFORMANCE
-- =========================================================================

-- Add the Vector Index required for fast Disalignment Frequency Count (DFC)
-- lookups in the Cultivate Synthesis Logic (07 engine logic specifications.md).
-- Using IVFFLAT for efficient approximate nearest neighbor search on the theme vectors.
CREATE INDEX idx_synthesis_theme_vector ON synthesis_log USING ivfflat (theme_vector vector_l2_ops)
WITH (lists = 100); -- 'lists' should be ~sqrt(num_rows), setting 100 as a standard starting point for a growing table.

CREATE INDEX idx_actionable_user_type ON actionable_items (user_id, item_type);
CREATE INDEX idx_adherence_user_date ON adherence_log (user_id, log_date);
CREATE INDEX idx_documents_user_type ON documents (user_id, document_type);
CREATE INDEX idx_health_metrics_user_date ON health_metrics (user_id, recorded_at);
CREATE INDEX idx_preferences_user ON user_preferences (user_id);
