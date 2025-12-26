from pydantic import BaseModel
from datetime import datetime


class AgentPick(BaseModel):
    agent: str
    pick_count: int
    pick_rate: float


class MapPerformance(BaseModel):
    map_name: str
    wins: int
    losses: int
    win_rate: float


class ScoutingReport(BaseModel):
    team_id: str
    team_name: str
    total_matches: int
    win_rate: float
    top_agents: list[AgentPick]
    map_performance: list[MapPerformance]
    actionable_insights: list[str]
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
            "top_agents": [a.model_dump() for a in self.top_agents],
            "map_performance": [m.model_dump() for m in self.map_performance],
            "actionable_insights": self.actionable_insights
        }