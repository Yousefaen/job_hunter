"""Database operations for job hunter application."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from job_hunter.models import Application, ApplicationStatus, Job
from job_hunter.storage.schemas import initialize_database

# Allowed ORDER BY clauses to prevent SQL injection
ALLOWED_ORDER_BY = frozenset({
    "created_at DESC",
    "created_at ASC",
    "updated_at DESC",
    "updated_at ASC",
    "match_score DESC",
    "match_score ASC",
    "company ASC",
    "company DESC",
    "title ASC",
    "title DESC",
})


class Database:
    """SQLite database manager for jobs and applications."""

    def __init__(self, db_path: Path):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        initialize_database(self.conn)

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()

    # ===== Job Operations =====

    def save_job(self, job: Job) -> None:
        """
        Save or update a job in the database.

        Args:
            job: Job object to save
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT INTO jobs (
                job_id, title, company, location, description, posted_date, url,
                easy_apply, company_size, experience_level, job_type,
                match_score, match_reasoning, keywords, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                title = excluded.title,
                company = excluded.company,
                location = excluded.location,
                description = excluded.description,
                posted_date = excluded.posted_date,
                url = excluded.url,
                easy_apply = excluded.easy_apply,
                company_size = excluded.company_size,
                experience_level = excluded.experience_level,
                job_type = excluded.job_type,
                match_score = excluded.match_score,
                match_reasoning = excluded.match_reasoning,
                keywords = excluded.keywords,
                updated_at = excluded.updated_at
            """,
            (
                job.job_id,
                job.title,
                job.company,
                job.location,
                job.description,
                job.posted_date,
                str(job.url),
                job.easy_apply,
                job.company_size,
                job.experience_level,
                job.job_type,
                job.match_score,
                job.match_reasoning,
                json.dumps(job.keywords),
                job.created_at.isoformat(),
                job.updated_at.isoformat(),
            ),
        )

        self.conn.commit()

    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Retrieve a job by ID.

        Args:
            job_id: LinkedIn job ID

        Returns:
            Job object if found, None otherwise
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()

        if row:
            return self._row_to_job(row)
        return None

    def get_all_jobs(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        order_by: str = "created_at DESC"
    ) -> list[Job]:
        """
        Get all jobs from database.

        Args:
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            order_by: SQL ORDER BY clause (must be in ALLOWED_ORDER_BY)

        Returns:
            List of Job objects

        Raises:
            ValueError: If order_by is not in allowed list
        """
        # Validate order_by to prevent SQL injection
        if order_by not in ALLOWED_ORDER_BY:
            raise ValueError(
                f"Invalid order_by value: '{order_by}'. "
                f"Allowed values: {', '.join(sorted(ALLOWED_ORDER_BY))}"
            )

        cursor = self.conn.cursor()
        params: list = []

        query = f"SELECT * FROM jobs ORDER BY {order_by}"
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [self._row_to_job(row) for row in rows]

    def search_jobs(
        self,
        company: Optional[str] = None,
        location: Optional[str] = None,
        min_score: Optional[float] = None,
        easy_apply: Optional[bool] = None,
    ) -> list[Job]:
        """
        Search jobs with filters.

        Args:
            company: Filter by company name (partial match)
            location: Filter by location (partial match)
            min_score: Minimum match score
            easy_apply: Filter by Easy Apply support

        Returns:
            List of matching Job objects
        """
        cursor = self.conn.cursor()
        query = "SELECT * FROM jobs WHERE 1=1"
        params = []

        if company:
            query += " AND company LIKE ?"
            params.append(f"%{company}%")

        if location:
            query += " AND location LIKE ?"
            params.append(f"%{location}%")

        if min_score is not None:
            query += " AND match_score >= ?"
            params.append(min_score)

        if easy_apply is not None:
            query += " AND easy_apply = ?"
            params.append(1 if easy_apply else 0)

        query += " ORDER BY match_score DESC, created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [self._row_to_job(row) for row in rows]

    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job from database.

        Args:
            job_id: Job ID to delete

        Returns:
            True if job was deleted, False if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    # ===== Application Operations =====

    def save_application(self, application: Application) -> int:
        """
        Save or update an application in the database.

        Args:
            application: Application object to save

        Returns:
            Application ID (newly created or existing)
        """
        cursor = self.conn.cursor()

        if application.application_id:
            # Update existing application
            cursor.execute(
                """
                UPDATE applications SET
                    job_id = ?,
                    status = ?,
                    applied_at = ?,
                    updated_at = ?,
                    error_message = ?,
                    custom_questions = ?,
                    custom_answers = ?,
                    notes = ?,
                    follow_up_date = ?
                WHERE application_id = ?
                """,
                (
                    application.job_id,
                    application.status.value,
                    application.applied_at.isoformat() if application.applied_at else None,
                    application.updated_at.isoformat(),
                    application.error_message,
                    json.dumps(application.custom_questions),
                    json.dumps(application.custom_answers),
                    application.notes,
                    application.follow_up_date.isoformat() if application.follow_up_date else None,
                    application.application_id,
                ),
            )
            app_id = int(application.application_id)
        else:
            # Insert new application
            cursor.execute(
                """
                INSERT INTO applications (
                    job_id, status, applied_at, updated_at,
                    error_message, custom_questions, custom_answers,
                    notes, follow_up_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    application.job_id,
                    application.status.value,
                    application.applied_at.isoformat() if application.applied_at else None,
                    application.updated_at.isoformat(),
                    application.error_message,
                    json.dumps(application.custom_questions),
                    json.dumps(application.custom_answers),
                    application.notes,
                    application.follow_up_date.isoformat() if application.follow_up_date else None,
                ),
            )
            app_id = cursor.lastrowid
            application.application_id = str(app_id)

        self.conn.commit()
        return app_id

    def get_application(self, application_id: int) -> Optional[Application]:
        """
        Retrieve an application by ID.

        Args:
            application_id: Application ID

        Returns:
            Application object if found, None otherwise
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE application_id = ?", (application_id,))
        row = cursor.fetchone()

        if row:
            return self._row_to_application(row)
        return None

    def get_application_by_job(self, job_id: str) -> Optional[Application]:
        """
        Get application for a specific job.

        Args:
            job_id: Job ID

        Returns:
            Application object if found, None otherwise
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE job_id = ? ORDER BY updated_at DESC LIMIT 1", (job_id,))
        row = cursor.fetchone()

        if row:
            return self._row_to_application(row)
        return None

    def get_all_applications(
        self,
        status: Optional[ApplicationStatus] = None,
        limit: Optional[int] = None,
    ) -> list[Application]:
        """
        Get all applications, optionally filtered by status.

        Args:
            status: Filter by application status
            limit: Maximum number of applications to return

        Returns:
            List of Application objects
        """
        cursor = self.conn.cursor()
        params: list = []

        if status:
            query = "SELECT * FROM applications WHERE status = ? ORDER BY updated_at DESC"
            params.append(status.value)
        else:
            query = "SELECT * FROM applications ORDER BY updated_at DESC"

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [self._row_to_application(row) for row in rows]

    def count_applications_today(self) -> int:
        """
        Count applications submitted today.

        Returns:
            Number of applications submitted today
        """
        cursor = self.conn.cursor()
        today = datetime.now(timezone.utc).date().isoformat()

        cursor.execute(
            """
            SELECT COUNT(*) FROM applications
            WHERE status = 'submitted'
            AND DATE(applied_at) = ?
            """,
            (today,),
        )

        return cursor.fetchone()[0]

    def get_statistics(self) -> dict:
        """
        Get application statistics.

        Returns:
            Dictionary with various statistics
        """
        cursor = self.conn.cursor()

        stats = {}

        # Total jobs
        cursor.execute("SELECT COUNT(*) FROM jobs")
        stats["total_jobs"] = cursor.fetchone()[0]

        # Jobs with Easy Apply
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE easy_apply = 1")
        stats["easy_apply_jobs"] = cursor.fetchone()[0]

        # Average match score
        cursor.execute("SELECT AVG(match_score) FROM jobs WHERE match_score IS NOT NULL")
        avg_score = cursor.fetchone()[0]
        stats["avg_match_score"] = round(avg_score, 2) if avg_score else 0

        # Application counts by status
        cursor.execute("SELECT status, COUNT(*) FROM applications GROUP BY status")
        stats["applications_by_status"] = dict(cursor.fetchall())

        # Applications today
        stats["applications_today"] = self.count_applications_today()

        return stats

    # ===== Helper Methods =====

    def _row_to_job(self, row: sqlite3.Row) -> Job:
        """Convert database row to Job object."""
        return Job(
            job_id=row["job_id"],
            title=row["title"],
            company=row["company"],
            location=row["location"],
            description=row["description"],
            posted_date=row["posted_date"],
            url=row["url"],
            easy_apply=bool(row["easy_apply"]),
            company_size=row["company_size"],
            experience_level=row["experience_level"],
            job_type=row["job_type"],
            match_score=row["match_score"],
            match_reasoning=row["match_reasoning"],
            keywords=json.loads(row["keywords"]) if row["keywords"] else [],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_application(self, row: sqlite3.Row) -> Application:
        """Convert database row to Application object."""
        return Application(
            application_id=str(row["application_id"]),
            job_id=row["job_id"],
            status=ApplicationStatus(row["status"]),
            applied_at=datetime.fromisoformat(row["applied_at"]) if row["applied_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]),
            error_message=row["error_message"],
            custom_questions=json.loads(row["custom_questions"]) if row["custom_questions"] else {},
            custom_answers=json.loads(row["custom_answers"]) if row["custom_answers"] else {},
            notes=row["notes"] or "",
            follow_up_date=datetime.fromisoformat(row["follow_up_date"]) if row["follow_up_date"] else None,
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
