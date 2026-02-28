import copy
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List

from models.feature_bundle import (
    ActionableInsightsFeature,
    AgentPerformanceContractFeature,
    DetailedAnalysisFeature,
    FeatureBundle,
    HeadToHeadContractFeature,
    MacroAnalysisFeature,
    MapReportContractFeature,
    MicroAnalysisFeature,
    MidGameAnalysisFeature,
    PlayerHeadToHeadContractFeature,
    PlayerPerformanceContractFeature,
    ReportSpecificFeature,
    RequestContextFeature,
    StrategyCallContractFeature,
    TellExploitContractFeature,
    TournamentReportContractFeature,
)
from models.report import MacroAnalysis, MicroAnalysis, MidGameAnalysis


class FeatureProducer(ABC):
    key: str
    version: str

    @abstractmethod
    def apply(self, report_data: Dict[str, Any], bundle: FeatureBundle) -> None:
        raise NotImplementedError


class RequestContextProducer(FeatureProducer):
    key = "request_context"
    version = "request-context.v1"

    def apply(self, report_data: Dict[str, Any], bundle: FeatureBundle) -> None:
        bundle.request_context = RequestContextFeature(
            report_type=report_data.get("report_type", "full"),
            team_id=report_data.get("team_id"),
            team_name=report_data.get("team_name"),
            player_id=report_data.get("player_id"),
            player_name=report_data.get("player_name"),
            map_name=report_data.get("map_name"),
            time_window=report_data.get("time_window"),
        )
        bundle.producer_versions[self.key] = self.version


class MacroAnalysisProducer(FeatureProducer):
    key = "macro_analysis"
    version = "macro-analysis.v1"

    def apply(self, report_data: Dict[str, Any], bundle: FeatureBundle) -> None:
        raw = report_data.get("macro_analysis")
        value = raw if isinstance(raw, dict) else {}
        bundle.macro_analysis = MacroAnalysisFeature(value=MacroAnalysis.model_validate(value))
        bundle.producer_versions[self.key] = self.version


class MidGameAnalysisProducer(FeatureProducer):
    key = "mid_game_analysis"
    version = "mid-game-analysis.v1"

    def apply(self, report_data: Dict[str, Any], bundle: FeatureBundle) -> None:
        raw = report_data.get("mid_game_analysis")
        value = raw if isinstance(raw, dict) else {}
        bundle.mid_game_analysis = MidGameAnalysisFeature(value=MidGameAnalysis.model_validate(value))
        bundle.producer_versions[self.key] = self.version


class MicroAnalysisProducer(FeatureProducer):
    key = "micro_analysis"
    version = "micro-analysis.v1"

    def apply(self, report_data: Dict[str, Any], bundle: FeatureBundle) -> None:
        raw = report_data.get("micro_analysis")
        value = raw if isinstance(raw, dict) else {}
        bundle.micro_analysis = MicroAnalysisFeature(value=MicroAnalysis.model_validate(value))
        bundle.producer_versions[self.key] = self.version


class ActionableInsightsProducer(FeatureProducer):
    key = "actionable_insights"
    version = "actionable-insights.v1"

    def apply(self, report_data: Dict[str, Any], bundle: FeatureBundle) -> None:
        raw = report_data.get("actionable_insights")
        if isinstance(raw, list):
            items = [str(item) for item in raw if item is not None]
        else:
            items = []

        bundle.actionable_insights = ActionableInsightsFeature(items=items)
        bundle.producer_versions[self.key] = self.version


class DetailedAnalysisProducer(FeatureProducer):
    key = "detailed_analysis"
    version = "detailed-analysis.v1"

    def apply(self, report_data: Dict[str, Any], bundle: FeatureBundle) -> None:
        raw = report_data.get("detailed_analysis")
        sections = copy.deepcopy(raw) if isinstance(raw, dict) else {}
        bundle.detailed_analysis = DetailedAnalysisFeature(sections=sections)
        bundle.producer_versions[self.key] = self.version


class ReportSpecificContractProducer(FeatureProducer):
    key = "report_specific"
    version = "report-contract.v1"

    def apply(self, report_data: Dict[str, Any], bundle: FeatureBundle) -> None:
        report_type = str(report_data.get("report_type", "full")).lower()

        if report_type == "map":
            macro = report_data.get("macro_analysis") if isinstance(report_data.get("macro_analysis"), dict) else {}
            map_report = MapReportContractFeature(
                map_name=report_data.get("map_name") or report_data.get("meta", {}).get("map"),
                team_name=report_data.get("team_name"),
                win_rates=macro.get("win_rates", []) if isinstance(macro.get("win_rates", []), list) else [],
                map_meta=report_data.get("meta") if isinstance(report_data.get("meta"), dict) else {},
            )
            bundle.report_specific = ReportSpecificFeature(kind="map", map_report=map_report)
            bundle.producer_versions[self.key] = f"map.{self.version}"
            return

        if report_type == "player_performance":
            micro = report_data.get("micro_analysis") if isinstance(report_data.get("micro_analysis"), dict) else {}
            player_report = PlayerPerformanceContractFeature(
                player_id=report_data.get("player_id"),
                player_name=report_data.get("player_name"),
                win_rate=float(report_data.get("win_rate", 0.0) or 0.0),
                star_player=micro.get("star_player") if isinstance(micro.get("star_player"), dict) else {},
                agent_pools=micro.get("agent_pools") if isinstance(micro.get("agent_pools"), list) else [],
            )
            bundle.report_specific = ReportSpecificFeature(kind="player_performance", player_report=player_report)
            bundle.producer_versions[self.key] = f"player.{self.version}"
            return

        if report_type in {"h2h", "head_to_head"}:
            macro = report_data.get("macro_analysis") if isinstance(report_data.get("macro_analysis"), dict) else {}
            head_to_head = HeadToHeadContractFeature(
                team_name_1=report_data.get("team_name_1"),
                team_name_2=report_data.get("team_name_2"),
                comparison=macro.get("comparison") if isinstance(macro.get("comparison"), dict) else {},
                team_1_maps=macro.get("team_1_maps") if isinstance(macro.get("team_1_maps"), list) else [],
                team_2_maps=macro.get("team_2_maps") if isinstance(macro.get("team_2_maps"), list) else [],
            )
            bundle.report_specific = ReportSpecificFeature(kind="head_to_head", head_to_head_report=head_to_head)
            bundle.producer_versions[self.key] = f"h2h.{self.version}"
            return

        if report_type == "tournament":
            macro = report_data.get("macro_analysis") if isinstance(report_data.get("macro_analysis"), dict) else {}
            tournament_report = TournamentReportContractFeature(
                tournament_name=report_data.get("tournament_name") or report_data.get("meta", {}).get("tournament"),
                team_name=report_data.get("team_name"),
                tournament_stats=macro.get("tournament_stats") if isinstance(macro.get("tournament_stats"), dict) else {},
                map_breakdown=macro.get("map_breakdown") if isinstance(macro.get("map_breakdown"), list) else [],
                win_rate=float(report_data.get("win_rate", 0.0) or 0.0),
            )
            bundle.report_specific = ReportSpecificFeature(kind="tournament", tournament_report=tournament_report)
            bundle.producer_versions[self.key] = f"tournament.{self.version}"
            return

        if report_type == "strategy_call":
            metadata = report_data.get("metadata") if isinstance(report_data.get("metadata"), dict) else {}
            insights = report_data.get("actionable_insights") if isinstance(report_data.get("actionable_insights"), list) else []
            strategy = str(insights[0]) if insights else ""
            strategy_report = StrategyCallContractFeature(
                team_id=report_data.get("team_id"),
                team_name=report_data.get("team_name"),
                game_state_event=report_data.get("game_state_event"),
                context_time_minutes=report_data.get("context_time_minutes"),
                strategy=strategy,
                risk_level=metadata.get("risk_level"),
                confidence_score=metadata.get("confidence_score"),
            )
            bundle.report_specific = ReportSpecificFeature(kind="strategy_call", strategy_call_report=strategy_report)
            bundle.producer_versions[self.key] = f"strategy.{self.version}"
            return

        if report_type == "agent_performance":
            micro = report_data.get("micro_analysis") if isinstance(report_data.get("micro_analysis"), dict) else {}
            agent_report = AgentPerformanceContractFeature(
                team_id=report_data.get("team_id"),
                team_name=report_data.get("team_name"),
                agent_pools=micro.get("agent_pools") if isinstance(micro.get("agent_pools"), list) else [],
                actionable_insights=[str(v) for v in report_data.get("actionable_insights", []) if v is not None],
            )
            bundle.report_specific = ReportSpecificFeature(
                kind="agent_performance",
                agent_performance_report=agent_report,
            )
            bundle.producer_versions[self.key] = f"agent.{self.version}"
            return

        if report_type == "tell_exploit":
            detailed = report_data.get("detailed_analysis") if isinstance(report_data.get("detailed_analysis"), dict) else {}
            insights = report_data.get("actionable_insights") if isinstance(report_data.get("actionable_insights"), list) else []
            tell_report = TellExploitContractFeature(
                opponent_name=report_data.get("opponent_name"),
                tell_description=str(detailed.get("tell")) if detailed.get("tell") is not None else None,
                exploit_recommendation=str(insights[0]) if insights else "",
            )
            bundle.report_specific = ReportSpecificFeature(kind="tell_exploit", tell_exploit_report=tell_report)
            bundle.producer_versions[self.key] = f"tell.{self.version}"
            return

        if report_type == "player_h2h":
            micro = report_data.get("micro_analysis") if isinstance(report_data.get("micro_analysis"), dict) else {}
            player_h2h = PlayerHeadToHeadContractFeature(
                player_name_1=report_data.get("player_name_1"),
                player_name_2=report_data.get("player_name_2"),
                comparison=micro.get("comparison") if isinstance(micro.get("comparison"), dict) else {},
            )
            bundle.report_specific = ReportSpecificFeature(kind="player_h2h", player_h2h_report=player_h2h)
            bundle.producer_versions[self.key] = f"player-h2h.{self.version}"
            return

        bundle.report_specific = ReportSpecificFeature(kind="generic", generic_payload={})
        bundle.producer_versions[self.key] = f"generic.{self.version}"


class FeatureRegistry:
    def __init__(self, producers: Iterable[FeatureProducer], feature_version: str = "features-v2"):
        self._producers: List[FeatureProducer] = list(producers)
        self.feature_version = feature_version

    def build(self, report_data: Dict[str, Any]) -> FeatureBundle:
        bundle = FeatureBundle(feature_version=self.feature_version)
        for producer in self._producers:
            producer.apply(report_data, bundle)
        return bundle

    @staticmethod
    def build_synthesis_context(report_data: Dict[str, Any], bundle: FeatureBundle) -> Dict[str, Any]:
        context = copy.deepcopy(report_data)
        context.update(bundle.to_analysis_payload())
        return context


DEFAULT_FEATURE_REGISTRY = FeatureRegistry(
    producers=[
        RequestContextProducer(),
        MacroAnalysisProducer(),
        MidGameAnalysisProducer(),
        MicroAnalysisProducer(),
        ActionableInsightsProducer(),
        DetailedAnalysisProducer(),
        ReportSpecificContractProducer(),
    ],
    feature_version="features-v2",
)
