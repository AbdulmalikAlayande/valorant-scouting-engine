import asyncio
import os
import re
import socket
import time
from typing import Any, Dict, Tuple

from config.globalutilitylogger import get_logger
from jobs.prompt_router import GeneralPromptRouter
from models.report import ScoutingReport
from storage.upsert import (
    claim_next_report_job,
    complete_report_job,
    ensure_pending_jobs_backfilled,
    fail_report_job,
    update_report_job_stage,
    update_report_request_status,
    upsert_feature_payload,
    upsert_normalized_payload,
    upsert_raw_payload,
    upsert_scouting_report,
)
from config.settings import (
    POLL_TIME_IN_SECONDS,
    REPORT_JOB_RETRY_DELAY_SECONDS,
    WORKER_ID,
)

_logger = get_logger(__name__)


def _payload_key(raw_key: str) -> str:
    normalized = re.sub(r"[^a-z0-9_]+", "_", str(raw_key or "payload").lower()).strip("_")
    return (normalized or "payload")[:64]


def _to_payload_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        return {"items": value}
    if value is None:
        return {}
    return {"value": value}


def _extract_storage_planes(report_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    explicit_planes = report_data.pop("__storage_planes", {}) if isinstance(report_data, dict) else {}
    if not isinstance(explicit_planes, dict):
        explicit_planes = {}

    raw_plane = explicit_planes.get("raw") if isinstance(explicit_planes.get("raw"), dict) else {}
    normalized_plane = explicit_planes.get("normalized") if isinstance(explicit_planes.get("normalized"), dict) else {}
    feature_plane = explicit_planes.get("features") if isinstance(explicit_planes.get("features"), dict) else {}

    if not normalized_plane:
        normalized_plane = {
            "request_context": {
                "report_type": report_data.get("report_type", "full"),
                "team_id": report_data.get("team_id"),
                "team_name": report_data.get("team_name"),
                "player_id": report_data.get("player_id"),
                "player_name": report_data.get("player_name"),
                "map_name": report_data.get("map_name"),
                "time_window": report_data.get("time_window"),
            }
        }
        if isinstance(report_data.get("meta"), dict):
            normalized_plane["meta"] = report_data.get("meta")
        if isinstance(report_data.get("detailed_analysis"), dict):
            normalized_plane["detailed_analysis"] = report_data.get("detailed_analysis")

    if not feature_plane:
        feature_plane = {
            "macro_analysis": _to_payload_dict(report_data.get("macro_analysis")),
            "mid_game_analysis": _to_payload_dict(report_data.get("mid_game_analysis")),
            "micro_analysis": _to_payload_dict(report_data.get("micro_analysis")),
            "actionable_insights": _to_payload_dict(report_data.get("actionable_insights")),
        }

    return raw_plane, normalized_plane, feature_plane


def _persist_storage_planes(report_request_id: int, report_data: Dict[str, Any]) -> None:
    raw_plane, normalized_plane, feature_plane = _extract_storage_planes(report_data)

    for key, payload in raw_plane.items():
        upsert_raw_payload(
            report_request_id=report_request_id,
            payload_key=_payload_key(key),
            payload=_to_payload_dict(payload),
            source_stage='INGESTING',
        )

    for key, payload in normalized_plane.items():
        upsert_normalized_payload(
            report_request_id=report_request_id,
            payload_key=_payload_key(key),
            payload=_to_payload_dict(payload),
            source_stage='FEATURIZING',
        )

    metadata = report_data.get("metadata") if isinstance(report_data.get("metadata"), dict) else {}
    feature_version = metadata.get("feature_version", "features-v1")

    for key, payload in feature_plane.items():
        upsert_feature_payload(
            report_request_id=report_request_id,
            payload_key=_payload_key(key),
            payload=_to_payload_dict(payload),
            feature_version=feature_version,
            source_stage='FEATURIZING',
        )


def classify_worker_error(error_message: str) -> Tuple[str, bool]:
    """
    Classify worker failures into taxonomy code + retryable boolean.
    """
    normalized = (error_message or "").lower()

    if any(k in normalized for k in ["timed out", "timeout", "rate limit", "unavailable", "connection reset"]):
        return "RETRYABLE_PROVIDER", True

    if any(k in normalized for k in ["database", "deadlock", "connection refused", "connection pool"]):
        return "RETRYABLE_INFRA", True

    if any(k in normalized for k in ["validation", "schema", "fieldundefined", "contract"]):
        return "NON_RETRYABLE_CONTRACT", False

    if any(k in normalized for k in ["forbidden", "unauthorized", "auth"]):
        return "NON_RETRYABLE_AUTH", False

    if any(k in normalized for k in ["config", "environment", "missing env"]):
        return "NON_RETRYABLE_CONFIG", False

    return "NON_RETRYABLE_DATA", False


async def poll_and_process_reports() -> None:
    """
    Phase 2 orchestration worker:
      - backfills missing report_jobs for legacy pending requests
      - claims next job using SKIP LOCKED leasing
      - updates staged job progress and retries
    """
    runtime_worker_id = f"{WORKER_ID}-{socket.gethostname()}-{os.getpid()}"
    _logger.info(f"🚀 Starting Stratigen AI Analysis Worker (orchestration mode) worker_id={runtime_worker_id}")
    router = GeneralPromptRouter()

    while True:
        try:
            backfilled = ensure_pending_jobs_backfilled(limit=20)
            if backfilled:
                _logger.info(f"Backfilled {backfilled} report_jobs from legacy pending requests")

            job = claim_next_report_job(runtime_worker_id)
            if not job:
                _logger.debug("No runnable report jobs, sleeping...")
                await asyncio.sleep(POLL_TIME_IN_SECONDS)
                continue

            job_id = job['job_id']
            request_id = job['report_request_id']
            user_prompt = job['user_prompt']

            _logger.info(f"Claimed job {job_id} for request {request_id} (attempt {job['attempt']}/{job['max_attempts']}): '{user_prompt}'")
            update_report_request_status(request_id, 'PROCESSING')

            try:
                update_report_job_stage(job_id, 'FEATURIZING')
                _logger.info(f"Routing prompt through LLM for request {request_id}...")
                result = await router.resolve_user_prompt(user_prompt)

                if not (result and isinstance(result, dict)):
                    raise ValueError("Router returned invalid result")

                report_data = result.get('output') or result.get('response')
                if not (report_data and isinstance(report_data, dict)):
                    raise ValueError("Handler returned invalid report structure")

                if 'report_type' not in report_data:
                    if 'player_name' in report_data:
                        report_data['report_type'] = 'player_performance'
                    elif 'map_name' in report_data:
                        report_data['report_type'] = 'map'
                    elif 'team_name_2' in report_data:
                        report_data['report_type'] = 'h2h'
                    else:
                        report_data['report_type'] = 'full'

                if 'error' in report_data:
                    raise ValueError(str(report_data['error']))

                _persist_storage_planes(request_id, report_data)

                full_context = {**report_data}
                if 'detailed_analysis' in report_data and isinstance(report_data['detailed_analysis'], dict):
                    full_context.update(report_data['detailed_analysis'])

                update_report_job_stage(job_id, 'SYNTHESIZING')
                from transforms.insight_generator import generate_90_5_60_report

                _logger.info(f"Synthesizing 90-5-60 report for request {request_id}...")
                synthesized_report = await generate_90_5_60_report(full_context)
                report_data.update(synthesized_report)

                update_report_job_stage(job_id, 'COMPOSING')
                report_data['report_request_id'] = request_id
                finalize_report(request_id, report_data)

                complete_report_job(job_id)
                update_report_request_status(request_id, 'COMPLETED')
                _logger.info(f"Job {job_id} request {request_id} completed successfully")

            except Exception as handler_error:
                error_msg = str(handler_error)
                code, retryable = classify_worker_error(error_msg)
                _logger.error(f"Job {job_id} failed for request {request_id}: [{code}] {error_msg}")

                fail_result = fail_report_job(
                    job_id=job_id,
                    error_code=code,
                    error_message=error_msg,
                    retryable=retryable,
                    retry_delay_seconds=REPORT_JOB_RETRY_DELAY_SECONDS,
                )

                if fail_result['state'] == 'QUEUED':
                    update_report_request_status(request_id, 'PENDING', error_message=error_msg)
                    _logger.info(
                        f"Job {job_id} re-queued for retry (attempt {fail_result['attempt']}/{fail_result['max_attempts']})"
                    )
                else:
                    update_report_request_status(request_id, 'FAILED', error_message=error_msg)

            await asyncio.sleep(POLL_TIME_IN_SECONDS)

        except Exception as ex:
            _logger.error(f"💥 Error in orchestration loop: {ex}", exc_info=True)
            await asyncio.sleep(10)


def start_worker():
    _logger.info("🎬 Starting Stratigen AI Engine...")
    try:
        asyncio.run(poll_and_process_reports())
    except KeyboardInterrupt:
        _logger.info("Commencing Graceful Worker Shutdown")
        time.sleep(5)
        _logger.info("Waiting for active requests to complete")
        time.sleep(5)
        _logger.info("Worker Shutdown Complete")
    except Exception as e:
        _logger.error(f"💀 Worker crashed: {e}", exc_info=True)
        raise


def execute_report_workflow(request_id, team_id, time_window: str) -> Dict[str, Any]:
    """
    Placeholder for future explicit stage-level execution orchestration.
    """
    raise NotImplementedError("execute_report_workflow is not used in phase-2 orchestration path")


def finalize_report(request_id, report_data):
    """
    Converts analysis into ScoutingReport and saves/upserts into scouting_reports.
    """
    _logger.info(f"Finalizing report {request_id}")

    metadata = report_data.get('metadata', {})
    if 'flash_card' in report_data:
        metadata['flash_card'] = report_data.get('flash_card')
    if 'coach_read' in report_data:
        metadata['coach_read'] = report_data.get('coach_read')
    if 'analyst_appendix' in report_data:
        metadata['analyst_appendix'] = report_data.get('analyst_appendix')

    report_data['metadata'] = metadata

    try:
        report_types = ['full', 'map', 'player_performance', 'agent_performance']
        is_standard_report = (
            report_data.get('report_type') in report_types
            or 'macro_analysis' in report_data
            or 'micro_analysis' in report_data
            or 'flash_card' in report_data
        )

        if is_standard_report:
            allowed_fields = ScoutingReport.model_fields.keys()
            filtered_data = {k: v for k, v in report_data.items() if k in allowed_fields}
            filtered_data['report_request_id'] = request_id

            report = ScoutingReport(**filtered_data)
            validated_data = report.model_dump()
            upsert_scouting_report(validated_data)
        else:
            if 'report_request_id' not in report_data:
                report_data['report_request_id'] = request_id
            upsert_scouting_report(report_data)
    except Exception as e:
        _logger.error(f"Validation failed for report {request_id}: {e}")
        if 'report_request_id' not in report_data:
            report_data['report_request_id'] = request_id
        upsert_scouting_report(report_data)

if __name__ == '__main__':
    start_worker()



