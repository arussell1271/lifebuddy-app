-- postgres/init.sql
-- Enable the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Create the secure user roles with passwords from the environment variables.
--    These roles are required for RLS and PoLP standards.

CREATE ROLE cognitive_engine_full WITH LOGIN PASSWORD '${POSTGRES_USER_FULL_PASS}';
CREATE ROLE cognitive_engine_rls WITH LOGIN PASSWORD '${POSTGRES_USER_RLS_PASS}';

-- 2. Create the main database and grant connection privileges (if not handled by default)
--    The POSTGRES_DB name is also read from your .env.dev file.
--    NOTE: The default process often creates the DB, but it's safe to include.

-- 3. Execute the full DDL (Data Definition Language) from your main schema file.
--    The file must be copied into the container's entrypoint directory for this to work.
\i /docker-entrypoint-initdb.d/03 db_schema.sql

-- 4. Set the default search path for the roles
--    This is often a good practice to ensure roles can find objects without schema prefixes.
ALTER ROLE cognitive_engine_full SET search_path TO public;
ALTER ROLE cognitive_engine_rls SET search_path TO public;