import dj_database_url
from environment import env

GRID_API_KEY = env.str("GRID_API_KEY")

DATABASE_URL = env.str("DATABASE_URL")
DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL)
}
