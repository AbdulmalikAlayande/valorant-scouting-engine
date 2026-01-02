from typing import List

from pydantic import BaseModel
from datetime import datetime


class AgentPick(BaseModel):
    agent: str
    pick_count: int
    pick_rate: float

class MapPerformance(BaseModel):
    map_filter: str
    wins: int
    losses: int
    game_count: int
    side_bias: float
    game_win_rate: float

class PlayerStat(BaseModel):
    player_id: str
    kd_ratio: float
    first_kill_pct: float
    avg_plants: float

class ScoutingReport(BaseModel):
    team_id: str
    team_name: str
    total_matches: int
    win_rate: float
    current_streak: int
    top_agents: List[AgentPick]
    map_performance: List[MapPerformance]
    player_stats: List[PlayerStat]
    actionable_insights: List[str]
    time_window: str
    created_at: datetime = datetime.now()

    def to_db_dict(self):
        """
        Convert to format for PostgreSQL JSONB columns
        """
        return {
            "team_id": self.team_id,
            "team_name": self.team_name,
            "total_matches": self.total_matches,
            "win_rate": self.win_rate,
            "current_streak": self.current_streak,
            "top_agents": [a.model_dump() for a in self.top_agents],
            "map_performance": [m.model_dump() for m in self.map_performance],
            "player_stats": [s.model_dump() for s in self.player_stats],
            "actionable_insights": self.actionable_insights,
            "time_window": self.time_window,
            "created_at": self.created_at
        }
