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
    recent_results: List[str]  # ["W", "L", "W"]


class MacroAnalysis(BaseModel):
    win_rates: List[Dict[str, Any]] = Field(default_factory=list)
    pistol_rounds: Optional[Dict[str, Any]] = None
    map_vetoes: Optional[Dict[str, Any]] = None
    default_compositions: List[Dict[str, Any]] = Field(default_factory=list)
    early_aggression: Optional[Dict[str, Any]] = None
    recurring_tells: List[Dict[str, Any]] = Field(default_factory=list)


class MidGameAnalysis(BaseModel):
    side_balance: Optional[Dict[str, Any]] = None
    objective_control: Optional[Dict[str, Any]] = None
    economy_patterns: Optional[Dict[str, Any]] = None
    retake_efficiency: Optional[Dict[str, Any]] = None


class MicroAnalysis(BaseModel):
    star_player: Optional[Dict[str, Any]] = None
    target_player: Optional[Dict[str, Any]] = None
    agent_pools: List[Dict[str, Any]] = Field(default_factory=list)
    role_distribution: Optional[Dict[str, Any]] = None
    rankings: List[Dict[str, Any]] = Field(default_factory=list)


class InsightObject(BaseModel):
    """
    Structured data object for a tactical insight (90-5-60 framework).
    """
    title: str = Field(..., description="Scan-friendly header")
    recommendation: str = Field(..., description="Imperative action (e.g., 'Ban Ascent')")
    reason: str = Field(..., description="1-line justification")
    evidence: List[str] = Field(default_factory=list, description="2-4 supporting bullet facts with real numbers")
    confidence_score: float = Field(0.0, description="0-1 model certainty")
    impact_score: float = Field(0.0, description="0-1 win probability impact")
    priority: float = Field(0.0, description="Calculated as impact × confidence × freshness × sample_quality")
    freshness: float = Field(1.0, description="0-1 recency of data")
    sample_quality: float = Field(1.0, description="0-1 stability/size of data")
    scope: str = Field("general", description="map|side|pistol|eco|player|comp")
    counter_risk: Optional[str] = Field(None, description="What can go wrong")
    next_step: Optional[str] = Field(None, description="Actionable drill or callout")

class FlashCard(BaseModel):
    """Layer A: 15-second visual TL;DR"""
    game_plan: List[str] = Field(..., max_length=3, description="3 actionable bullets max")
    veto_recommendation: str = Field(..., description="Ban/Pick + 1-line justification")
    punish_patterns: List[str] = Field(default_factory=list, description="1-2 high-confidence punish patterns")
    risk_flags: List[str] = Field(default_factory=list, description="What can backfire")

class CoachRead(BaseModel):
    """Layer B: 90-second tactical playbook"""
    insights: List[InsightObject] = Field(default_factory=list, description="Tiered tactical insights")

class AnalystAppendix(BaseModel):
    """Layer C: 5-60 minute deep dive"""
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Full stats and charts")

class ScoutingReport(BaseModel):
    report_request_id: int
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    player_id: Optional[str] = None
    player_name: Optional[str] = None
    map_name: Optional[str] = None
    total_matches: int = 0
    total_games: int = 0
    win_rate: float = 0.0
    current_streak: int = 0

    # 90-5-60 Architecture
    flash_card: Optional[FlashCard] = None
    coach_read: Optional[CoachRead] = None
    analyst_appendix: Optional[AnalystAppendix] = None

    # Tiered Analysis (Backend structural data)
    macro_analysis: Optional[MacroAnalysis] = None
    mid_game_analysis: Optional[MidGameAnalysis] = None
    micro_analysis: Optional[MicroAnalysis] = None

    # Legacy fields (kept for backward compatibility if needed, or we can migrate)
    # top_agents: List[AgentPick] = Field(default_factory=list)
    # map_performance: List[MapPerformance] = Field(default_factory=list)
    # player_stats: List[PlayerStat] = Field(default_factory=list)

    # Advanced Analysis
    top_compositions: List[TeamComposition] = Field(default_factory=list)
    head_to_head: Optional[HeadToHeadMatchup] = None

    # Insights
    actionable_insights: List[str] = Field(default_factory=list)
    detailed_analysis: Dict[str, Any] = Field(default_factory=dict)

    # Context
    time_window: Optional[str] = None
    report_type: str = "full"  # full, map, tournament, etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

    def to_db_dict(self):
        """
        Convert to format for PostgreSQL JSONB columns
        """
        data = self.model_dump()
        data["created_at"] = self.created_at.isoformat()
        return data


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
