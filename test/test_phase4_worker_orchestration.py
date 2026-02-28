import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# Ensure settings imports do not fail when tests run outside full runtime env.
os.environ.setdefault("GRID_API_KEY", "test-key")
os.environ.setdefault("GRID_QUERY_API", "http://mock")
os.environ.setdefault("GRID_STATS_API", "http://mock")
os.environ.setdefault("GRID_SERIES_STATE_API", "http://mock")
os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
os.environ.setdefault("GEMINI_API_KEY", "test-key")

# Stub prompt_router to avoid importing runtime-only pydantic-ai symbols in unit tests.
prompt_router_stub = types.ModuleType("jobs.prompt_router")


class _StubGeneralPromptRouter:
    async def resolve_user_prompt(self, user_prompt: str):
        return {"output": {}}


prompt_router_stub.GeneralPromptRouter = _StubGeneralPromptRouter
sys.modules["jobs.prompt_router"] = prompt_router_stub

# Stub synthesis module to avoid pydantic-ai dependency mismatch and control call order.
insight_stub = types.ModuleType("transforms.insight_generator")
insight_stub._order = None


async def _stub_generate_90_5_60_report(_ctx):
    if isinstance(insight_stub._order, list):
        insight_stub._order.append("synthesis")
    return {"flash_card": {}, "coach_read": {}}


insight_stub.generate_90_5_60_report = _stub_generate_90_5_60_report
sys.modules["transforms.insight_generator"] = insight_stub

import jobs.report_generator as report_generator


class _Router:
    def __init__(self, order):
        self._order = order

    async def resolve_user_prompt(self, user_prompt: str):
        self._order.append("resolve")
        return {
            "output": {
                "report_type": "full",
                "team_name": "Cloud9",
                "macro_analysis": {},
                "mid_game_analysis": {},
                "micro_analysis": {},
                "actionable_insights": ["A"],
                "detailed_analysis": {},
            }
        }


class Phase4WorkerOrchestrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_run_job_pipeline_order_registry_synthesis_composer(self):
        order = []
        insight_stub._order = order
        router = _Router(order)

        fake_bundle = MagicMock()
        fake_bundle.feature_version = "features-v2"

        fake_registry = MagicMock()
        fake_registry.feature_version = "features-v2"

        def _build_side_effect(_report_data):
            order.append("registry.build")
            return fake_bundle

        def _context_side_effect(_report_data, _bundle):
            order.append("registry.context")
            return {
                "report_type": "full",
                "macro_analysis": {},
                "mid_game_analysis": {},
                "micro_analysis": {},
                "actionable_insights": ["A"],
                "detailed_analysis": {},
            }

        fake_registry.build.side_effect = _build_side_effect
        fake_registry.build_synthesis_context.side_effect = _context_side_effect

        with (
            patch.object(report_generator, "DEFAULT_FEATURE_REGISTRY", fake_registry),
            patch.object(report_generator, "update_report_job_stage", side_effect=lambda _job_id, stage: order.append(f"stage:{stage}")),
            patch.object(report_generator, "validate_pre_persist_contract", side_effect=lambda **_kwargs: order.append("contract.pre_persist")),
            patch.object(report_generator, "_persist_storage_planes", side_effect=lambda *_args, **_kwargs: order.append("persist")),
            patch.object(
                report_generator,
                "compose_report",
                side_effect=lambda **_kwargs: order.append("compose")
                or {
                    "report_type": "full",
                    "metadata": {
                        "contract_version": "scouting-report.v1",
                        "feature_version": "features-v2",
                        "composer_version": "report-composer.v1",
                        "lineage": {},
                    },
                },
            ),
            patch.object(report_generator, "validate_pre_finalize_contract", side_effect=lambda _report: order.append("contract.pre_finalize")),
            patch.object(report_generator, "finalize_report", side_effect=lambda *_args, **_kwargs: order.append("finalize")),
        ):
            await report_generator._run_job_pipeline(
                job_id=1,
                request_id=2,
                user_prompt="Scout Cloud9",
                router=router,
            )

        self.assertEqual(
            order,
            [
                "stage:FEATURIZING",
                "resolve",
                "registry.build",
                "contract.pre_persist",
                "persist",
                "registry.context",
                "stage:SYNTHESIZING",
                "synthesis",
                "stage:COMPOSING",
                "compose",
                "contract.pre_finalize",
                "finalize",
            ],
        )


class FeatureRegistryCompatibilityTests(unittest.TestCase):
    def test_validate_feature_registry_compatibility_accepts_matching_version(self):
        report_generator.validate_feature_registry_compatibility("features-v2", "features-v2")

    def test_validate_feature_registry_compatibility_rejects_mismatch(self):
        with self.assertRaises(RuntimeError):
            report_generator.validate_feature_registry_compatibility("features-v1", "features-v2")


if __name__ == "__main__":
    unittest.main()
