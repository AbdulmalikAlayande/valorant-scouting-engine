import copy
import os
import sys
import types
import unittest
from unittest.mock import patch

# To help me ensure that settings imports do not fail when tests run outside full runtime env.
os.environ.setdefault("GRID_API_KEY", "test-key")
os.environ.setdefault("GRID_QUERY_API", "http://mock")
os.environ.setdefault("GRID_STATS_API", "http://mock")
os.environ.setdefault("GRID_SERIES_STATE_API", "http://mock")
os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
os.environ.setdefault("GEMINI_API_KEY", "test-key")

# A stub prompt_router to avoid importing runtime-only pydantic-ai symbols in unit tests.
prompt_router_stub = types.ModuleType("jobs.prompt_router")


class _StubGeneralPromptRouter:
    async def resolve_user_prompt(self, user_prompt: str):
        return {"output": {}}


prompt_router_stub.GeneralPromptRouter = _StubGeneralPromptRouter
sys.modules["jobs.prompt_router"] = prompt_router_stub

import jobs.report_generator as report_generator
import storage.upsert as upsert_module


class _CursorContext:
    def __init__(self, cursor):
        self._cursor = cursor

    def __enter__(self):
        return self._cursor

    def __exit__(self, exc_type, exc, tb):
        return False


class _DummyCursor:
    def __init__(self):
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return {"id": 101}


class StoragePlanePersistenceTests(unittest.TestCase):
    def test_extract_storage_planes_prefers_explicit_bundle(self):
        report_data = {
            "report_type": "full",
            "metadata": {"feature_version": "features-v9"},
            "__storage_planes": {
                "raw": {"Team Stats": {"games": 12}},
                "normalized": {"context": {"team": "Cloud9"}},
                "features": {"macro": {"bias": "attack"}},
            },
        }

        raw_plane, normalized_plane, feature_plane = (
            report_generator._extract_storage_planes(report_data)
        )

        self.assertNotIn("__storage_planes", report_data)
        self.assertEqual(raw_plane["Team Stats"], {"games": 12})
        self.assertEqual(normalized_plane["context"], {"team": "Cloud9"})
        self.assertEqual(feature_plane["macro"], {"bias": "attack"})

    def test_extract_storage_planes_builds_fallback_planes(self):
        report_data = {
            "report_type": "map",
            "team_id": "1079",
            "team_name": "Cloud9",
            "map_name": "Ascent",
            "time_window": "LAST_3_MONTHS",
            "meta": {"status": "success"},
            "detailed_analysis": {"maps": {"best": "Ascent"}},
            "macro_analysis": {"tempo": "fast"},
            "actionable_insights": ["Hold B main"],
        }

        raw_plane, normalized_plane, feature_plane = (
            report_generator._extract_storage_planes(report_data)
        )

        self.assertEqual(raw_plane, {})
        self.assertEqual(normalized_plane["request_context"]["report_type"], "map")
        self.assertEqual(normalized_plane["request_context"]["map_name"], "Ascent")
        self.assertEqual(normalized_plane["meta"], {"status": "success"})
        self.assertIn("detailed_analysis", normalized_plane)
        self.assertEqual(feature_plane["macro_analysis"], {"tempo": "fast"})
        self.assertEqual(
            feature_plane["actionable_insights"], {"items": ["Hold B main"]}
        )

    def test_persist_storage_planes_is_deterministic_on_rerun(self):
        report_data = {
            "metadata": {"feature_version": "features-v42"},
            "__storage_planes": {
                "raw": {
                    "Team Stats": {"wins": 8},
                    "Match Details": [{"series_id": "s1"}],
                },
                "normalized": {
                    "Team Overview": {"games": 10},
                },
                "features": {
                    "Weakness Analysis": {"eco": "fragile"},
                    "Actionable Insights": ["Abuse eco rounds"],
                },
            },
        }

        with (
            patch("jobs.report_generator.upsert_raw_payload") as raw_upsert,
            patch(
                "jobs.report_generator.upsert_normalized_payload"
            ) as normalized_upsert,
            patch("jobs.report_generator.upsert_feature_payload") as feature_upsert,
        ):
            report_generator._persist_storage_planes(55, copy.deepcopy(report_data))
            first_raw_keys = [
                c.kwargs["payload_key"] for c in raw_upsert.call_args_list
            ]
            first_norm_keys = [
                c.kwargs["payload_key"] for c in normalized_upsert.call_args_list
            ]
            first_feature_keys = [
                c.kwargs["payload_key"] for c in feature_upsert.call_args_list
            ]

            report_generator._persist_storage_planes(55, copy.deepcopy(report_data))
            second_raw_keys = [
                c.kwargs["payload_key"]
                for c in raw_upsert.call_args_list[len(first_raw_keys) :]
            ]
            second_norm_keys = [
                c.kwargs["payload_key"]
                for c in normalized_upsert.call_args_list[len(first_norm_keys) :]
            ]
            second_feature_keys = [
                c.kwargs["payload_key"]
                for c in feature_upsert.call_args_list[len(first_feature_keys) :]
            ]

            self.assertEqual(first_raw_keys, second_raw_keys)
            self.assertEqual(first_norm_keys, second_norm_keys)
            self.assertEqual(first_feature_keys, second_feature_keys)

            for key in first_raw_keys + first_norm_keys + first_feature_keys:
                self.assertLessEqual(len(key), 64)

            for call in feature_upsert.call_args_list:
                self.assertEqual(call.kwargs["feature_version"], "features-v42")
                self.assertEqual(call.kwargs["source_stage"], "FEATURIZING")

    def test_finalize_report_dual_write_is_repeatable(self):
        report_data = {
            "report_request_id": 99,
            "report_type": "full",
            "macro_analysis": {"pace": "fast"},
            "generated_report": "Summary output",
            "metadata": {
                "model_version": "gemini-3-flash",
                "feature_version": "features-v1",
            },
        }

        with (
            patch("jobs.report_generator.upsert_scouting_report") as scouting_upsert,
            patch("jobs.report_generator.upsert_report_artifact") as artifact_upsert,
        ):
            report_generator.finalize_report(99, copy.deepcopy(report_data))
            report_generator.finalize_report(99, copy.deepcopy(report_data))

            self.assertEqual(scouting_upsert.call_count, 2)
            self.assertEqual(artifact_upsert.call_count, 2)
            for call in artifact_upsert.call_args_list:
                self.assertEqual(call.kwargs["report_request_id"], 99)
                self.assertEqual(call.kwargs["report_type"], "full")


class StoragePlaneUpsertQueryTests(unittest.TestCase):
    def test_plane_upserts_use_conflict_key_for_idempotency(self):
        cursor = _DummyCursor()

        with patch(
            "storage.upsert.get_db_cursor",
            side_effect=lambda: _CursorContext(cursor),
        ):
            upsert_module.upsert_raw_payload(1, "raw_key", {"v": 1})
            upsert_module.upsert_normalized_payload(1, "norm_key", {"v": 2})
            upsert_module.upsert_feature_payload(
                1, "feature_key", {"v": 3}, feature_version="features-v9"
            )

        queries = [q for q, _ in cursor.executed]
        self.assertEqual(len(queries), 3)
        for query in queries:
            self.assertIn("ON CONFLICT (report_request_id, payload_key)", query)

    def test_report_artifact_upsert_uses_request_conflict(self):
        cursor = _DummyCursor()

        with patch(
            "storage.upsert.get_db_cursor",
            side_effect=lambda: _CursorContext(cursor),
        ):
            upsert_module.upsert_report_artifact(
                report_request_id=3,
                report_type="full",
                report_payload={"summary": "x"},
                summary="x",
                model_version="gemini-3-flash",
                feature_version="features-v1",
            )

        self.assertEqual(len(cursor.executed), 1)
        query, _ = cursor.executed[0]
        self.assertIn("ON CONFLICT (report_request_id)", query)
        self.assertIn("DO UPDATE SET", query)


if __name__ == "__main__":
    unittest.main()
