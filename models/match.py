from pydantic import BaseModel
from datetime import datetime

class Match(BaseModel):
    series_id: str
    team_id: str
    team_name: str
    opponent_id: str
    opponent_name: str
    map_name: str | None = None
    won: bool
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    played_at: datetime