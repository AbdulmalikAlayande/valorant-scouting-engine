from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
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
    side_bias: float = 0.0
    game_win_rate: float

class PlayerStat(BaseModel):
    player_id: str
    nickname: Optional[str] = None
    kd_ratio: float
    first_kill_pct: float
    avg_plants: float
    signature_agents: List[str] = Field(default_factory=list)

class TeamComposition(BaseModel):
    lineup: List[str]
    win_rate: float
    game_count: int

class HeadToHeadMatchup(BaseModel):
    opponent_id: str
    opponent_name: str
    total_series: int
    win_rate: float
    recent_results: List[str] # ["W", "L", "W"]

class ScoutingReport(BaseModel):
    report_request_id: int
    team_id: str
    team_name: str
    total_matches: int
    total_games: int
    win_rate: float
    current_streak: int
    
    # Core Analysis
    top_agents: List[AgentPick] = Field(default_factory=list)
    map_performance: List[MapPerformance] = Field(default_factory=list)
    player_stats: List[PlayerStat] = Field(default_factory=list)
    
    # Advanced Analysis
    top_compositions: List[TeamComposition] = Field(default_factory=list)
    head_to_head: Optional[HeadToHeadMatchup] = None
    
    # Insights
    actionable_insights: List[str] = Field(default_factory=list)
    
    # Context
    time_window: str
    report_type: str = "full" # full, map, tournament, etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

    def to_db_dict(self):
        """
        Convert to format for PostgreSQL JSONB columns
        """
        return {
            "report_request_id": self.report_request_id,
            "team_id": self.team_id,
            "team_name": self.team_name,
            "total_matches": self.total_matches,
            "total_games": self.total_games,
            "win_rate": self.win_rate,
            "current_streak": self.current_streak,
            "top_agents": [a.model_dump() for a in self.top_agents],
            "map_performance": [m.model_dump() for m in self.map_performance],
            "player_stats": [s.model_dump() for s in self.player_stats],
            "top_compositions": [c.model_dump() for c in self.top_compositions],
            "head_to_head": self.head_to_head.model_dump() if self.head_to_head else None,
            "actionable_insights": self.actionable_insights,
            "time_window": self.time_window,
            "report_type": self.report_type,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


class ReportRequest(BaseModel):
    """
    Represents a report generation request in the job queue.

    New Architecture: Stores natural language prompts instead of structured params.
    The LLM router interprets the prompt and routes to the appropriate handler.
    """
    id: Optional[int] = None
    user_prompt: str = Field(..., description="Natural language prompt from user")
    status: str = Field(default='pending', description="pending|processing|completed|failed")
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    # Optional: Keep these for backwards compatibility, but they're not required anymore
    team_id: Optional[str] = None
    time_window: Optional[str] = None
