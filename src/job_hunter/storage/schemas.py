"""SQLite database schemas for job hunter application."""

# SQL schema for jobs table
JOBS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT NOT NULL,
    description TEXT NOT NULL,
    posted_date TEXT,
    url TEXT NOT NULL,

    -- Job metadata
    easy_apply BOOLEAN DEFAULT 0,
    company_size TEXT,
    experience_level TEXT,
    job_type TEXT,

    -- Matching data
    match_score REAL,
    match_reasoning TEXT,
    keywords TEXT,  -- JSON array stored as text

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# SQL schema for applications table
APPLICATIONS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    application_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',

    -- Timestamps
    applied_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Application details
    error_message TEXT,
    custom_questions TEXT,  -- JSON object stored as text
    custom_answers TEXT,    -- JSON object stored as text
    notes TEXT DEFAULT '',
    follow_up_date TIMESTAMP,

    -- Foreign key
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);
"""

# Indexes for better query performance
JOBS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);
CREATE INDEX IF NOT EXISTS idx_jobs_easy_apply ON jobs(easy_apply);
CREATE INDEX IF NOT EXISTS idx_jobs_match_score ON jobs(match_score);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);
"""

APPLICATIONS_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_applied_at ON applications(applied_at);
CREATE INDEX IF NOT EXISTS idx_applications_follow_up_date ON applications(follow_up_date);
"""

# Trigger to update updated_at timestamp
JOBS_UPDATE_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS jobs_update_timestamp
AFTER UPDATE ON jobs
FOR EACH ROW
BEGIN
    UPDATE jobs SET updated_at = CURRENT_TIMESTAMP WHERE job_id = NEW.job_id;
END;
"""

APPLICATIONS_UPDATE_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS applications_update_timestamp
AFTER UPDATE ON applications
FOR EACH ROW
BEGIN
    UPDATE applications SET updated_at = CURRENT_TIMESTAMP WHERE application_id = NEW.application_id;
END;
"""

# All schemas combined
ALL_SCHEMAS = [
    JOBS_TABLE_SCHEMA,
    APPLICATIONS_TABLE_SCHEMA,
    JOBS_INDEXES,
    APPLICATIONS_INDEXES,
    JOBS_UPDATE_TRIGGER,
    APPLICATIONS_UPDATE_TRIGGER,
]


def initialize_database(conn) -> None:
    """
    Initialize database with all required tables, indexes, and triggers.

    Args:
        conn: SQLite database connection
    """
    cursor = conn.cursor()

    for schema in ALL_SCHEMAS:
        cursor.executescript(schema)

    conn.commit()
