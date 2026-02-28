import copy
import unittest

from composer.report_composer import compose_report
from features.registry import DEFAULT_FEATURE_REGISTRY


class Phase4FeatureRegistryTests(unittest.TestCase):
    def test_registry_builds_typed_bundle_and_versions(self):
        report_data = {
            "report_type": "full",
            "team_id": "1079",
            "team_name": "Cloud9",
            "time_window": "LAST_3_MONTHS",
            "macro_analysis": {
                "win_rates": [{"map": "Ascent", "win_rate": 0.72}],
                "recurring_tells": [{"tell": "eco push"}],
            },
            "mid_game_analysis": {
                "side_balance": {"attack": 0.61, "defense": 0.54},
            },
            "micro_analysis": {
                "star_player": {"player_name": "leaf", "impact": 0.88},
            },
            "actionable_insights": ["Pressure mid", 42],
            "detailed_analysis": {"team": {"form": "hot"}},
        }

        bundle = DEFAULT_FEATURE_REGISTRY.build(copy.deepcopy(report_data))

        self.assertEqual(bundle.feature_version, "features-v2")
        self.assertEqual(bundle.request_context.team_name, "Cloud9")
        self.assertEqual(bundle.request_context.report_type, "full")
        self.assertIn("macro_analysis", bundle.producer_versions)
        self.assertIn("mid_game_analysis", bundle.producer_versions)
        self.assertIn("micro_analysis", bundle.producer_versions)
        self.assertEqual(bundle.actionable_insights.items, ["Pressure mid", "42"])
        self.assertEqual(bundle.report_specific.kind, "generic")

    def test_registry_builds_map_report_contract_feature(self):
        report_data = {
            "report_type": "map",
            "team_name": "Cloud9",
            "map_name": "Bind",
            "macro_analysis": {"win_rates": [{"map": "Bind", "win_rate": 0.64}]},
            "meta": {"map": "Bind", "status": "success"},
            "actionable_insights": ["Ban Bind"],
        }

        bundle = DEFAULT_FEATURE_REGISTRY.build(copy.deepcopy(report_data))

        self.assertEqual(bundle.report_specific.kind, "map")
        self.assertIsNotNone(bundle.report_specific.map_report)
        self.assertEqual(bundle.report_specific.map_report.map_name, "Bind")
        self.assertEqual(bundle.report_specific.map_report.team_name, "Cloud9")
        self.assertIn("report_specific", bundle.producer_versions)

    def test_registry_builds_player_report_contract_feature(self):
        report_data = {
            "report_type": "player_performance",
            "player_id": "p1",
            "player_name": "leaf",
            "win_rate": 0.55,
            "micro_analysis": {
                "star_player": {"player_name": "leaf", "impact_score": 0.88},
                "agent_pools": [{"agent": "Jett", "pick_rate": 0.42}],
            },
        }

        bundle = DEFAULT_FEATURE_REGISTRY.build(copy.deepcopy(report_data))

        self.assertEqual(bundle.report_specific.kind, "player_performance")
        self.assertIsNotNone(bundle.report_specific.player_report)
        self.assertEqual(bundle.report_specific.player_report.player_name, "leaf")
        self.assertGreater(bundle.report_specific.player_report.win_rate, 0.5)

    def test_registry_builds_head_to_head_contract_feature(self):
        report_data = {
            "report_type": "h2h",
            "team_name_1": "Cloud9",
            "team_name_2": "NRG",
            "macro_analysis": {
                "comparison": {"metrics": [{"metric": "Win Rate", "team_1": 0.61, "team_2": 0.56}]},
                "team_1_maps": [{"map": "Ascent"}],
                "team_2_maps": [{"map": "Bind"}],
            },
        }

        bundle = DEFAULT_FEATURE_REGISTRY.build(copy.deepcopy(report_data))

        self.assertEqual(bundle.report_specific.kind, "head_to_head")
        self.assertIsNotNone(bundle.report_specific.head_to_head_report)
        self.assertEqual(bundle.report_specific.head_to_head_report.team_name_1, "Cloud9")
        self.assertEqual(bundle.report_specific.head_to_head_report.team_name_2, "NRG")

    def test_registry_builds_tournament_contract_feature(self):
        report_data = {
            "report_type": "tournament",
            "team_name": "Cloud9",
            "tournament_name": "VCT Americas",
            "win_rate": 0.63,
            "macro_analysis": {
                "tournament_stats": {"wins": 12, "losses": 7},
                "map_breakdown": [{"map": "Ascent", "win_rate": 0.7}],
            },
        }

        bundle = DEFAULT_FEATURE_REGISTRY.build(copy.deepcopy(report_data))

        self.assertEqual(bundle.report_specific.kind, "tournament")
        self.assertEqual(bundle.report_specific.tournament_report.tournament_name, "VCT Americas")

    def test_registry_builds_strategy_call_contract_feature(self):
        report_data = {
            "report_type": "strategy_call",
            "team_id": "1079",
            "team_name": "Cloud9",
            "game_state_event": "eco_round",
            "context_time_minutes": 14,
            "actionable_insights": ["Execute fast B split"],
            "metadata": {"risk_level": "Medium", "confidence_score": 0.85},
        }

        bundle = DEFAULT_FEATURE_REGISTRY.build(copy.deepcopy(report_data))

        self.assertEqual(bundle.report_specific.kind, "strategy_call")
        self.assertEqual(bundle.report_specific.strategy_call_report.strategy, "Execute fast B split")

    def test_registry_builds_agent_performance_contract_feature(self):
        report_data = {
            "report_type": "agent_performance",
            "team_id": "1079",
            "team_name": "Cloud9",
            "micro_analysis": {
                "agent_pools": [{"player_id": "team", "top_agents": [{"agent_name": "Jett"}]}],
            },
            "actionable_insights": ["Lean into Jett-heavy comp"],
        }

        bundle = DEFAULT_FEATURE_REGISTRY.build(copy.deepcopy(report_data))

        self.assertEqual(bundle.report_specific.kind, "agent_performance")
        self.assertEqual(len(bundle.report_specific.agent_performance_report.agent_pools), 1)

    def test_registry_builds_tell_exploit_contract_feature(self):
        report_data = {
            "report_type": "tell_exploit",
            "opponent_name": "NRG",
            "actionable_insights": ["Punish predictable B retake timing"],
            "detailed_analysis": {"tell": "Late B retake utility dump"},
        }

        bundle = DEFAULT_FEATURE_REGISTRY.build(copy.deepcopy(report_data))

        self.assertEqual(bundle.report_specific.kind, "tell_exploit")
        self.assertEqual(bundle.report_specific.tell_exploit_report.opponent_name, "NRG")

    def test_registry_builds_player_h2h_contract_feature(self):
        report_data = {
            "report_type": "player_h2h",
            "player_name_1": "leaf",
            "player_name_2": "aspas",
            "micro_analysis": {
                "comparison": {
                    "player_1": {"impact_score": 0.77},
                    "player_2": {"impact_score": 0.83},
                }
            },
        }

        bundle = DEFAULT_FEATURE_REGISTRY.build(copy.deepcopy(report_data))

        self.assertEqual(bundle.report_specific.kind, "player_h2h")
        self.assertEqual(bundle.report_specific.player_h2h_report.player_name_1, "leaf")

    def test_registry_synthesis_context_uses_bundle_payload(self):
        report_data = {
            "report_type": "map",
            "macro_analysis": {"win_rates": [{"map": "Bind", "win_rate": 0.64}]},
            "actionable_insights": ["Ban Bind"],
        }

        bundle = DEFAULT_FEATURE_REGISTRY.build(copy.deepcopy(report_data))
        context = DEFAULT_FEATURE_REGISTRY.build_synthesis_context(report_data, bundle)

        self.assertIn("macro_analysis", context)
        self.assertIn("actionable_insights", context)
        self.assertEqual(context["actionable_insights"], ["Ban Bind"])
        self.assertEqual(context["macro_analysis"].get("win_rates", [])[0].get("map"), "Bind")
        self.assertIn("report_specific", context)


class Phase4ComposerTests(unittest.TestCase):
    def test_composer_merges_features_lineage_and_storage_plane(self):
        base_report = {
            "report_type": "full",
            "team_name": "Cloud9",
            "metadata": {"model_version": "gemini-3-flash"},
            "__storage_planes": {
                "raw": {"team_stats": {"games": 20}},
                "normalized": {"team_overview": {"wins": 12}},
            },
            "macro_analysis": {"win_rates": []},
            "actionable_insights": [],
            "detailed_analysis": {},
        }

        bundle = DEFAULT_FEATURE_REGISTRY.build(copy.deepcopy(base_report))
        composed = compose_report(
            base_report=base_report,
            feature_bundle=bundle,
            synthesized_report={
                "flash_card": {"game_plan": ["Take space"], "veto_recommendation": "Ban Icebox"},
                "coach_read": {"insights": []},
            },
        )

        self.assertEqual(composed["metadata"]["feature_version"], "features-v2")
        self.assertEqual(composed["metadata"]["composer_version"], "report-composer.v1")
        self.assertEqual(composed["metadata"]["contract_version"], "scouting-report.v1")
        self.assertIn("lineage", composed["metadata"])
        self.assertIn("feature_producers", composed["metadata"]["lineage"])
        self.assertIn("features", composed["__storage_planes"])
        self.assertIn("raw", composed["__storage_planes"])
        self.assertIn("normalized", composed["__storage_planes"])
        self.assertIn("flash_card", composed)
        self.assertIn("coach_read", composed)
        self.assertIn("report_specific", composed["__storage_planes"]["features"])


if __name__ == "__main__":
    unittest.main()
