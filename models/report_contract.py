from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from models.feature_bundle import FeatureBundle
from models.report import MacroAnalysis, MidGameAnalysis, MicroAnalysis

REPORT_CONTRACT_VERSION = "scouting-report.v1"
KNOWN_REPORT_TYPES = {
    "full",
    "map",
    "player_performance",
    "h2h",
    "head_to_head",
    "tournament",
    "strategy_call",
    "agent_performance",
    "tell_exploit",
    "player_h2h",
}

REPORT_TYPE_TO_FEATURE_KIND = {
    "map": "map",
    "player_performance": "player_performance",
    "h2h": "head_to_head",
    "head_to_head": "head_to_head",
    "tournament": "tournament",
    "strategy_call": "strategy_call",
    "agent_performance": "agent_performance",
    "tell_exploit": "tell_exploit",
    "player_h2h": "player_h2h",
}


class ReportContractMetadata(BaseModel):
    contract_version: str = REPORT_CONTRACT_VERSION
    model_version: Optional[str] = None
    feature_version: str
    composer_version: str
    feature_producer_versions: Dict[str, str] = Field(default_factory=dict)
    lineage: Dict[str, Any] = Field(default_factory=dict)


class ReportContractV1(BaseModel):
    report_type: str
    report_request_id: Optional[int] = None
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    player_id: Optional[str] = None
    player_name: Optional[str] = None
    map_name: Optional[str] = None
    time_window: Optional[str] = None
    macro_analysis: MacroAnalysis = Field(default_factory=MacroAnalysis)
    mid_game_analysis: MidGameAnalysis = Field(default_factory=MidGameAnalysis)
    micro_analysis: MicroAnalysis = Field(default_factory=MicroAnalysis)
    actionable_insights: List[str] = Field(default_factory=list)
    detailed_analysis: Dict[str, Any] = Field(default_factory=dict)
    report_specific: Dict[str, Any] = Field(default_factory=dict)
    metadata: ReportContractMetadata
    flash_card: Optional[Dict[str, Any]] = None
    coach_read: Optional[Dict[str, Any]] = None
    analyst_appendix: Optional[Dict[str, Any]] = None
    generated_report: Optional[str] = None


def validate_pre_persist_contract(report_data: Dict[str, Any], feature_bundle: FeatureBundle) -> None:
    report_type = str(report_data.get("report_type", "full")).lower()
    if report_type not in KNOWN_REPORT_TYPES:
        raise ValueError(f"Unsupported report_type '{report_type}' for {REPORT_CONTRACT_VERSION}")

    expected_kind = REPORT_TYPE_TO_FEATURE_KIND.get(report_type)
    if expected_kind and feature_bundle.report_specific.kind != expected_kind:
        raise ValueError(
            f"report_specific contract mismatch: expected kind '{expected_kind}', got '{feature_bundle.report_specific.kind}'"
        )

    typed_fields_by_kind = {
        "map": feature_bundle.report_specific.map_report,
        "player_performance": feature_bundle.report_specific.player_report,
        "head_to_head": feature_bundle.report_specific.head_to_head_report,
        "tournament": feature_bundle.report_specific.tournament_report,
        "strategy_call": feature_bundle.report_specific.strategy_call_report,
        "agent_performance": feature_bundle.report_specific.agent_performance_report,
        "tell_exploit": feature_bundle.report_specific.tell_exploit_report,
        "player_h2h": feature_bundle.report_specific.player_h2h_report,
    }

    if expected_kind and typed_fields_by_kind.get(expected_kind) is None:
        raise ValueError(f"report_specific contract '{expected_kind}' is missing typed payload")


def validate_pre_finalize_contract(report_data: Dict[str, Any]) -> None:
    report_type = str(report_data.get("report_type", "full")).lower()
    if report_type not in KNOWN_REPORT_TYPES:
        raise ValueError(f"Unsupported report_type '{report_type}' for {REPORT_CONTRACT_VERSION}")

    ReportContractV1.model_validate(report_data)
