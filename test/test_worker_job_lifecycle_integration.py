import os
import sys
import types
import unittest
from unittest.mock import patch

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

import jobs.report_generator as report_generator


class _Router:
    async def resolve_user_prompt(self, _user_prompt: str):
        return {"output": {}}


class WorkerLifecycleIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_lifecycle_queued_retry_ready_and_terminal_failed(self):
        router = _Router()

        jobs = {
            1: {
                "job_id": 1,
                "report_request_id": 201,
                "attempt": 0,
                "max_attempts": 2,
                "state": "QUEUED",
                "current_stage": "INGESTING",
                "user_prompt": "Generate full scouting report for Cloud9",
            },
            2: {
                "job_id": 2,
                "report_request_id": 202,
                "attempt": 0,
                "max_attempts": 1,
                "state": "QUEUED",
                "current_stage": "INGESTING",
                "user_prompt": "Generate player performance for leaf",
            },
        }

        pipeline_attempts = {201: 0, 202: 0}
        request_statuses = {201: [], 202: []}
        fail_codes = []

        def _claim_next(_worker_id: str):
            for job_id in sorted(jobs.keys()):
                job = jobs[job_id]
                if job["state"] == "QUEUED" and job["attempt"] < job["max_attempts"]:
                    job["state"] = "RUNNING"
                    job["attempt"] += 1
                    return {
                        "job_id": job["job_id"],
                        "report_request_id": job["report_request_id"],
                        "attempt": job["attempt"],
                        "max_attempts": job["max_attempts"],
                        "user_prompt": job["user_prompt"],
                    }
            return None

        async def _run_pipeline(job_id: int, request_id: int, user_prompt: str, router):
            _ = (job_id, user_prompt, router)
            pipeline_attempts[request_id] += 1
            if request_id == 201 and pipeline_attempts[request_id] == 1:
                raise RuntimeError("provider timed out while generating output")
            if request_id == 202:
                raise ValueError("validation contract mismatch")

        def _complete_job(job_id: int):
            jobs[job_id]["state"] = "COMPLETED"
            jobs[job_id]["current_stage"] = "READY"

        def _fail_job(job_id: int, error_code: str, error_message: str, retryable: bool, retry_delay_seconds: int):
            _ = (error_message, retry_delay_seconds)
            fail_codes.append(error_code)
            job = jobs[job_id]
            can_retry = retryable and job["attempt"] < job["max_attempts"]
            if can_retry:
                job["state"] = "QUEUED"
                job["current_stage"] = "INGESTING"
                return {"state": "QUEUED", "attempt": job["attempt"], "max_attempts": job["max_attempts"]}

            job["state"] = "FAILED"
            job["current_stage"] = "FAILED"
            return {"state": "FAILED", "attempt": job["attempt"], "max_attempts": job["max_attempts"]}

        def _update_request(request_id: int, status: str, error_message=None):
            request_statuses[request_id].append((status, error_message))

        with (
            patch.object(report_generator, "ensure_pending_jobs_backfilled", return_value=0),
            patch.object(report_generator, "claim_next_report_job", side_effect=_claim_next),
            patch.object(report_generator, "_run_job_pipeline", side_effect=_run_pipeline),
            patch.object(report_generator, "complete_report_job", side_effect=_complete_job),
            patch.object(report_generator, "fail_report_job", side_effect=_fail_job),
            patch.object(report_generator, "update_report_request_status", side_effect=_update_request),
        ):
            first = await report_generator.process_next_job_once("worker-1", router)
            second = await report_generator.process_next_job_once("worker-1", router)
            third = await report_generator.process_next_job_once("worker-1", router)
            fourth = await report_generator.process_next_job_once("worker-1", router)

        self.assertTrue(first)
        self.assertTrue(second)
        self.assertTrue(third)
        self.assertFalse(fourth)

        self.assertEqual(jobs[1]["state"], "COMPLETED")
        self.assertEqual(jobs[1]["current_stage"], "READY")
        self.assertEqual(jobs[2]["state"], "FAILED")
        self.assertEqual(jobs[2]["current_stage"], "FAILED")

        self.assertEqual(
            request_statuses[201],
            [
                ("PROCESSING", None),
                ("PENDING", "provider timed out while generating output"),
                ("PROCESSING", None),
                ("COMPLETED", None),
            ],
        )
        self.assertEqual(
            request_statuses[202],
            [
                ("PROCESSING", None),
                ("FAILED", "validation contract mismatch"),
            ],
        )
        self.assertEqual(fail_codes, ["RETRYABLE_PROVIDER", "NON_RETRYABLE_CONTRACT"])


if __name__ == "__main__":
    unittest.main()
