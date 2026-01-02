"""Shared safety patterns for code scanning.

Keep prohibited patterns here so the App service source files do not contain
the literal pattern list and cause self-matches.
"""
IMPORT_PATTERNS = [
    # Match real import statements only (from/import at start of line)
    r"^\s*(from|import)\s+(psycopg2)\b",
    r"^\s*(from|import)\s+(sqlalchemy)\b",
    r"^\s*(from|import)\s+(pgvector)\b",
]

# Host/endpoint patterns to detect hard-coded service references.
HOST_PATTERNS = [
    r"\bollama\b",
    r"\blifebuddy-db\b",
    r"\bollama:11434\b",
    r"\blocalhost:11434\b",
    r"\bopenai\b",
]
