from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from models.report import MacroAnalysis, MidGameAnalysis, MicroAnalysis


class RequestContextFeature(BaseModel):
    report_type: str = "full"
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    player_id: Optional[str] = None
    player_name: Optional[str] = None
    map_name: Optional[str] = None
    time_window: Optional[str] = None


class MacroAnalysisFeature(BaseModel):
    value: MacroAnalysis = Field(default_factory=MacroAnalysis)


class MidGameAnalysisFeature(BaseModel):
    value: MidGameAnalysis = Field(default_factory=MidGameAnalysis)


class MicroAnalysisFeature(BaseModel):
    value: MicroAnalysis = Field(default_factory=MicroAnalysis)


class ActionableInsightsFeature(BaseModel):
    items: List[str] = Field(default_factory=list)


class DetailedAnalysisFeature(BaseModel):
    sections: Dict[str, Any] = Field(default_factory=dict)


class MapReportContractFeature(BaseModel):
    map_name: Optional[str] = None
    team_name: Optional[str] = None
    win_rates: List[Dict[str, Any]] = Field(default_factory=list)
    map_meta: Dict[str, Any] = Field(default_factory=dict)


class PlayerPerformanceContractFeature(BaseModel):
    player_id: Optional[str] = None
    player_name: Optional[str] = None
    win_rate: float = 0.0
    star_player: Dict[str, Any] = Field(default_factory=dict)
    agent_pools: List[Dict[str, Any]] = Field(default_factory=list)


class HeadToHeadContractFeature(BaseModel):
    team_name_1: Optional[str] = None
    team_name_2: Optional[str] = None
    comparison: Dict[str, Any] = Field(default_factory=dict)
    team_1_maps: List[Dict[str, Any]] = Field(default_factory=list)
    team_2_maps: List[Dict[str, Any]] = Field(default_factory=list)


class TournamentReportContractFeature(BaseModel):
    tournament_name: Optional[str] = None
    team_name: Optional[str] = None
    tournament_stats: Dict[str, Any] = Field(default_factory=dict)
    map_breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    win_rate: float = 0.0


class StrategyCallContractFeature(BaseModel):
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    game_state_event: Optional[str] = None
    context_time_minutes: Optional[int] = None
    strategy: str = ""
    risk_level: Optional[str] = None
    confidence_score: Optional[float] = None


class AgentPerformanceContractFeature(BaseModel):
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    agent_pools: List[Dict[str, Any]] = Field(default_factory=list)
    actionable_insights: List[str] = Field(default_factory=list)


class TellExploitContractFeature(BaseModel):
    opponent_name: Optional[str] = None
    tell_description: Optional[str] = None
    exploit_recommendation: str = ""


class PlayerHeadToHeadContractFeature(BaseModel):
    player_name_1: Optional[str] = None
    player_name_2: Optional[str] = None
    comparison: Dict[str, Any] = Field(default_factory=dict)


class ReportSpecificFeature(BaseModel):
    kind: str = "generic"
    map_report: Optional[MapReportContractFeature] = None
    player_report: Optional[PlayerPerformanceContractFeature] = None
    head_to_head_report: Optional[HeadToHeadContractFeature] = None
    tournament_report: Optional[TournamentReportContractFeature] = None
    strategy_call_report: Optional[StrategyCallContractFeature] = None
    agent_performance_report: Optional[AgentPerformanceContractFeature] = None
    tell_exploit_report: Optional[TellExploitContractFeature] = None
    player_h2h_report: Optional[PlayerHeadToHeadContractFeature] = None
    generic_payload: Dict[str, Any] = Field(default_factory=dict)


class FeatureBundle(BaseModel):
    feature_version: str = "features-v2"
    producer_versions: Dict[str, str] = Field(default_factory=dict)
    request_context: RequestContextFeature = Field(default_factory=RequestContextFeature)
    macro_analysis: MacroAnalysisFeature = Field(default_factory=MacroAnalysisFeature)
    mid_game_analysis: MidGameAnalysisFeature = Field(default_factory=MidGameAnalysisFeature)
    micro_analysis: MicroAnalysisFeature = Field(default_factory=MicroAnalysisFeature)
    actionable_insights: ActionableInsightsFeature = Field(default_factory=ActionableInsightsFeature)
    detailed_analysis: DetailedAnalysisFeature = Field(default_factory=DetailedAnalysisFeature)
    report_specific: ReportSpecificFeature = Field(default_factory=ReportSpecificFeature)

    def to_feature_plane_payloads(self) -> Dict[str, Dict[str, Any]]:
        return {
            "request_context": self.request_context.model_dump(exclude_none=True),
            "macro_analysis": self.macro_analysis.value.model_dump(exclude_none=True),
            "mid_game_analysis": self.mid_game_analysis.value.model_dump(exclude_none=True),
            "micro_analysis": self.micro_analysis.value.model_dump(exclude_none=True),
            "actionable_insights": {"items": self.actionable_insights.items},
            "detailed_analysis": self.detailed_analysis.sections,
            "report_specific": self.report_specific.model_dump(exclude_none=True),
        }

    def to_analysis_payload(self) -> Dict[str, Any]:
        payload = {
            "macro_analysis": self.macro_analysis.value.model_dump(exclude_none=True),
            "mid_game_analysis": self.mid_game_analysis.value.model_dump(exclude_none=True),
            "micro_analysis": self.micro_analysis.value.model_dump(exclude_none=True),
            "actionable_insights": self.actionable_insights.items,
            "detailed_analysis": self.detailed_analysis.sections,
        }

        if self.report_specific.kind != "generic":
            payload["report_specific"] = self.report_specific.model_dump(exclude_none=True)

        return payload
