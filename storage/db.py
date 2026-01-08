from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from config.settings import DATABASES
from config.globalutilitylogger import get_logger

logger = get_logger(__name__)


def get_connection():
    """
    Creates a single database connection.
    Why separate function?
    - Testable (can mock this)
    - Can add connection pooling later
    - Single source of truth for connection config
    """
    db_config = DATABASES['default']
    return psycopg2.connect(
        host=db_config['HOST'],
        port=db_config['PORT'],
        database=db_config['NAME'],
        user=db_config['USER'],
        password=db_config['PASSWORD']
    )


@contextmanager
def get_db_cursor(commit=True):
    """
    Context manager for database operations.
    Args:
        commit: Whether to auto-commit (default True)
    Usage:
        with get_db_cursor() as cursor:
            cursor.execute("INSERT INTO ...")
            # Auto-commits when the block ends
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)  # Returns dicts, not tuples
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()


def run_migration(sql_file_path: str):
    """
    Execute a SQL migration file.

    Usage:
        run_migration("migrations/001_initial_schema.sql")
    """
    with open(sql_file_path, 'r') as f:
        sql = f.read()

    with get_db_cursor() as cursor:
        cursor.execute(sql)

    logger.info(f"Migration completed: {sql_file_path}")


def test_connection():
    """
    Usage:
        python storage/db.py
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            logger.info(f"Connected to PostgreSQL: {version['version']}")
            return True
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing database connection...")
    test_connection()

    from pathlib import Path
    migration_file = Path(__file__).parent.parent / "migrations" / "001_initial_schema.sql"
    if migration_file.exists():
        print(f"\nRunning migration: {migration_file}")
        run_migration(str(migration_file))
