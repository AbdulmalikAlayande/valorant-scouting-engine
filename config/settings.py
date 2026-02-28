from pathlib import Path
import dj_database_url
from config.environment import env

GEMINI_API_KEY = env.str("GEMINI_API_KEY", default="")
GEMINI_MODEL = env.str("GEMINI_MODEL", default="gemini-3-flash")
GEMINI_API_BASE_URL = env.str(
    "GEMINI_API_BASE_URL",
    default="https://generativelanguage.googleapis.com/v1beta",
)


GRID_API_KEY = env.str("GRID_API_KEY")
GRID_QUERY_API_URL = env.str("GRID_QUERY_API")
GRID_STATS_API_URL = env.str("GRID_STATS_API")
GRID_SERIES_STATE_API_URL = env.str("GRID_SERIES_STATE_API")

POLL_TIME_IN_SECONDS = env.int("POLL_TIME_IN_SECONDS", default=10)

DATABASE_URL = env.str("DATABASE_URL")
DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL)
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent

WORKER_ID = env.str("WORKER_ID", default="engine-worker")
REPORT_JOB_MAX_ATTEMPTS = env.int("REPORT_JOB_MAX_ATTEMPTS", default=5)
REPORT_JOB_RETRY_DELAY_SECONDS = env.int("REPORT_JOB_RETRY_DELAY_SECONDS", default=30)
FEATURE_REGISTRY_VERSION = env.str("FEATURE_REGISTRY_VERSION", default="features-v2")
