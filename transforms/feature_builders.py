from typing import Any, Dict, List

from models.feature_bundle import (
    ActionableInsightsFeature,
    DetailedAnalysisFeature,
    MacroAnalysisFeature,
    MicroAnalysisFeature,
    MidGameAnalysisFeature,
)
from models.report import MacroAnalysis, MicroAnalysis, MidGameAnalysis


def build_macro_feature(
    map_analysis: Dict[str, Any],
    team_analysis: Dict[str, Any],
    composition_analysis: Dict[str, Any],
    weakness_analysis: Dict[str, Any],
) -> MacroAnalysisFeature:
    payload = {
        "win_rates": map_analysis.get("win_rates", []),
        "pistol_rounds": team_analysis.get("pistol_rounds"),
        "map_vetoes": map_analysis.get("veto_strategy"),
        "default_compositions": composition_analysis.get("default_comps", [])[:3],
        "early_aggression": weakness_analysis.get("early_aggression"),
        "recurring_tells": weakness_analysis.get("recurring_tells", []),
    }
    return MacroAnalysisFeature(value=MacroAnalysis.model_validate(payload))


def build_mid_game_feature(
    team_analysis: Dict[str, Any],
    weakness_analysis: Dict[str, Any],
) -> MidGameAnalysisFeature:
    payload = {
        "side_balance": team_analysis.get("side_balance"),
        "objective_control": team_analysis.get("objective_control"),
        "economy_patterns": weakness_analysis.get("economy_patterns"),
        "retake_efficiency": team_analysis.get("retake_efficiency"),
    }
    return MidGameAnalysisFeature(value=MidGameAnalysis.model_validate(payload))


def build_micro_feature(player_analysis: Dict[str, Any]) -> MicroAnalysisFeature:
    payload = {
        "star_player": player_analysis.get("star_player"),
        "target_player": player_analysis.get("target_player"),
        "agent_pools": player_analysis.get("agent_pools"),
        "role_distribution": player_analysis.get("role_distribution"),
        "rankings": player_analysis.get("rankings", []),
    }
    return MicroAnalysisFeature(value=MicroAnalysis.model_validate(payload))


def build_actionable_feature(insights: List[str]) -> ActionableInsightsFeature:
    sanitized = [str(item) for item in insights if item is not None]
    return ActionableInsightsFeature(items=sanitized)


def build_detailed_feature(
    team_analysis: Dict[str, Any],
    map_analysis: Dict[str, Any],
    player_analysis: Dict[str, Any],
    composition_analysis: Dict[str, Any],
    weakness_analysis: Dict[str, Any],
) -> DetailedAnalysisFeature:
    return DetailedAnalysisFeature(
        sections={
            "team": team_analysis,
            "maps": map_analysis,
            "players": player_analysis,
            "compositions": composition_analysis,
            "weaknesses": weakness_analysis,
        }
    )
