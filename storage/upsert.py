# storage/upsert.py
from config.globalutilitylogger import get_logger
from storage.db import get_db_cursor
from psycopg2.extras import Json
from typing import Dict, Any, Optional

_logger = get_logger(__name__)


def upsert_team(team_id: str, team_name: str, **extra_fields):
    """
    Insert or update a team record.
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            """
                INSERT INTO teams (team_id, team_name, logo_url, color_primary, updated_at)
                VALUES (%(team_id)s, %(team_name)s, %(logo_url)s, %(color_primary)s, NOW())
                ON CONFLICT (team_id)
                    DO UPDATE SET team_name    = EXCLUDED.team_name,
                                 logo_url      = EXCLUDED.logo_url,
                                 color_primary = EXCLUDED.color_primary,
                                 updated_at    = NOW()
                RETURNING id
            """,
            {
                'team_id': team_id,
                'team_name': team_name,
                'logo_url': extra_fields.get('logo_url'),
                'color_primary': extra_fields.get('color_primary')
            }
        )

        result = cursor.fetchone()
        return result['id']


def upsert_match(match_data: Dict[str, Any]):
    """
    Insert or update a match record.
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            """
                INSERT INTO matches (series_id, team_id, team_fk_id, team_name,
                                    opponent_id, opponent_fk_id, opponent_name,
                                    map_name, won, kills, deaths, assists, played_at)
                VALUES (%(series_id)s, %(team_id)s,
                        get_or_create_team_fk(%(team_id)s, %(team_name)s),
                        %(team_name)s, %(opponent_id)s,
                        get_or_create_team_fk(%(opponent_id)s, %(opponent_name)s),
                       %(map_name)s, %(won)s, %(kills)s, %(deaths)s, %(assists)s, %(played_at)s)
                ON CONFLICT (series_id)
                    DO UPDATE SET team_name    = EXCLUDED.team_name,
                                 opponent_name = EXCLUDED.opponent_name,
                                 won           = EXCLUDED.won,
                                 kills         = EXCLUDED.kills,
                                 deaths        = EXCLUDED.deaths,
                                 assists       = EXCLUDED.assists
                RETURNING id
            """,
            match_data
        )

        result = cursor.fetchone()
        return result['id']


def upsert_scouting_report(report_data: Dict[str, Any]):
    """
    Insert or update a scouting report.
    """
    _logger.info(f"Upserting scouting report for request {report_data.get('report_request_id')}")
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id FROM scouting_reports WHERE report_request_id = %s", (report_data.get('report_request_id'),))
        existing = cursor.fetchone()

        metadata = report_data.get('metadata', {})
        if report_data.get('macro_analysis'):
            metadata['macro_analysis'] = report_data.get('macro_analysis')
        if report_data.get('mid_game_analysis'):
            metadata['mid_game_analysis'] = report_data.get('mid_game_analysis')
        if report_data.get('micro_analysis'):
            metadata['micro_analysis'] = report_data.get('micro_analysis')

        flash_card = report_data.get('flash_card')
        coach_read = report_data.get('coach_read')
        analyst_appendix = report_data.get('analyst_appendix')

        db_params = {
            'report_request_id': report_data.get('report_request_id'),
            'report_data': Json({
                'flash_card': flash_card,
                'coach_read': coach_read,
                'analyst_appendix': analyst_appendix,
                'metadata': metadata
            }),
            'report_type': report_data.get('report_type', 'full'),
            'generated_report': report_data.get('generated_report', '')
        }

        if existing:
            cursor.execute("""
                           UPDATE scouting_reports SET
                               report_data         = %(report_data)s,
                               generated_report    = %(generated_report)s
                           WHERE report_request_id = %(report_request_id)s
                           RETURNING id
                           """, db_params)
        else:
            cursor.execute("""
                           INSERT INTO scouting_reports (report_request_id, report_type,
                                                         report_data, generated_report)
                           VALUES (%(report_request_id)s, %(report_type)s,
                                   %(report_data)s, %(generated_report)s)
                           RETURNING id
                           """, db_params)

        result = cursor.fetchone()
        return result['id']


def create_report_request(user_prompt: str) -> int:
    """
    Create a new report request and queue a report job.
    """
    import uuid
    public_id = str(uuid.uuid4())
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO report_requests (user_prompt, status, public_id)
            VALUES (%s, 'PENDING', %s)
            RETURNING id
            """,
            (user_prompt, public_id)
        )
        result = cursor.fetchone()
        request_id = result['id']

        cursor.execute(
            """
            INSERT INTO report_jobs (report_request_id, state, current_stage, attempt, max_attempts)
            VALUES (%s, 'QUEUED', 'INGESTING', 0, 5)
            ON CONFLICT (report_request_id) DO NOTHING
            """,
            (request_id,)
        )

        _logger.info(f"Report creation result ID: {request_id}")
        return request_id


def ensure_pending_jobs_backfilled(limit: int = 10) -> int:
    """
    Backfill report_jobs for legacy PENDING report_requests that do not yet have job rows.
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            WITH pending_requests AS (
                SELECT rr.id
                FROM report_requests rr
                LEFT JOIN report_jobs rj ON rj.report_request_id = rr.id
                WHERE rr.status = 'PENDING'
                  AND rj.id IS NULL
                ORDER BY rr.created_at
                LIMIT %s
            )
            INSERT INTO report_jobs (report_request_id, state, current_stage, attempt, max_attempts)
            SELECT id, 'QUEUED', 'INGESTING', 0, 5
            FROM pending_requests
            ON CONFLICT (report_request_id) DO NOTHING
            RETURNING id
            """,
            (limit,)
        )
        inserted = cursor.fetchall()
        return len(inserted)


def claim_next_report_job(worker_id: str, lock_ttl_minutes: int = 10) -> Optional[Dict[str, Any]]:
    """
    Claim the next queued job using SKIP LOCKED semantics.
    """
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            WITH candidate AS (
                SELECT rj.id
                FROM report_jobs rj
                JOIN report_requests rr ON rr.id = rj.report_request_id
                WHERE rr.status IN ('PENDING', 'PROCESSING')
                  AND COALESCE(rj.next_run_at, NOW()) <= NOW()
                  AND rj.attempt < rj.max_attempts
                  AND (
                        rj.state = 'QUEUED'
                        OR (rj.state = 'RUNNING' AND rj.locked_at < NOW() - (%s || ' minutes')::interval)
                  )
                ORDER BY rr.created_at
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            UPDATE report_jobs rj
            SET state = 'RUNNING',
                current_stage = 'INGESTING',
                attempt = rj.attempt + 1,
                locked_by = %s,
                locked_at = NOW(),
                last_modified_at = NOW()
            FROM candidate c
            WHERE rj.id = c.id
            RETURNING rj.id, rj.report_request_id, rj.attempt, rj.max_attempts
            """,
            (lock_ttl_minutes, worker_id)
        )
        claimed = cursor.fetchone()
        if not claimed:
            return None

        cursor.execute(
            """
            SELECT id, user_prompt, status, created_at
            FROM report_requests
            WHERE id = %s
            """,
            (claimed['report_request_id'],)
        )
        request_row = cursor.fetchone()
        if not request_row:
            return None

        return {
            'job_id': claimed['id'],
            'report_request_id': claimed['report_request_id'],
            'attempt': claimed['attempt'],
            'max_attempts': claimed['max_attempts'],
            'user_prompt': request_row['user_prompt'],
            'request_status': request_row['status'],
            'created_at': request_row['created_at']
        }


def update_report_job_stage(job_id: int, stage: str):
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            UPDATE report_jobs
            SET current_stage = %s,
                last_modified_at = NOW()
            WHERE id = %s
            """,
            (stage, job_id)
        )


def complete_report_job(job_id: int):
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            UPDATE report_jobs
            SET state = 'COMPLETED',
                current_stage = 'READY',
                locked_by = NULL,
                locked_at = NULL,
                last_modified_at = NOW()
            WHERE id = %s
            """,
            (job_id,)
        )


def fail_report_job(
    job_id: int,
    error_code: str,
    error_message: str,
    retryable: bool,
    retry_delay_seconds: int,
) -> Dict[str, Any]:
    with get_db_cursor() as cursor:
        cursor.execute("SELECT attempt, max_attempts FROM report_jobs WHERE id = %s", (job_id,))
        row = cursor.fetchone()
        if not row:
            return {'state': 'FAILED', 'attempt': 0, 'max_attempts': 0}

        attempt = row['attempt']
        max_attempts = row['max_attempts']
        can_retry = retryable and attempt < max_attempts

        if can_retry:
            cursor.execute(
                """
                UPDATE report_jobs
                SET state = 'QUEUED',
                    current_stage = 'INGESTING',
                    next_run_at = NOW() + (%s || ' seconds')::interval,
                    locked_by = NULL,
                    locked_at = NULL,
                    last_error_code = %s,
                    last_error_message = %s,
                    retryable = TRUE,
                    last_modified_at = NOW()
                WHERE id = %s
                """,
                (retry_delay_seconds, error_code, error_message, job_id)
            )
            return {'state': 'QUEUED', 'attempt': attempt, 'max_attempts': max_attempts}

        cursor.execute(
            """
            UPDATE report_jobs
            SET state = 'FAILED',
                current_stage = 'FAILED',
                locked_by = NULL,
                locked_at = NULL,
                last_error_code = %s,
                last_error_message = %s,
                retryable = %s,
                last_modified_at = NOW()
            WHERE id = %s
            """,
            (error_code, error_message, retryable, job_id)
        )
        return {'state': 'FAILED', 'attempt': attempt, 'max_attempts': max_attempts}


def update_report_request_status(request_id: int, status: str, error_message: str = None):
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            UPDATE report_requests
            SET status        = %s,
                error_message = %s,
                completed_at  = CASE WHEN %s IN ('COMPLETED', 'FAILED') THEN NOW() ELSE NULL END
            WHERE id = %s
            """,
            (status, error_message, status, request_id)
        )


if __name__ == "__main__":
    print("🧪 Testing upsert functions...")
    request_id = create_report_request("Test prompt")
    print(f"✅ Report request created with ID: {request_id}")
    update_report_request_status(request_id, 'PROCESSING')
    print("✅ Status updated to 'PROCESSING'")
