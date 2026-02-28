import asyncio
import os
import re
import socket
import time
from typing import Any, Dict, Optional, Tuple

from composer.report_composer import compose_report
from config.globalutilitylogger import get_logger
from config.settings import (
    FEATURE_REGISTRY_VERSION,
    POLL_TIME_IN_SECONDS,
    REPORT_JOB_RETRY_DELAY_SECONDS,
    WORKER_ID,
)
from features.registry import DEFAULT_FEATURE_REGISTRY
from jobs.prompt_router import GeneralPromptRouter
from models.feature_bundle import FeatureBundle
from models.report import ScoutingReport
from models.report_contract import (
    REPORT_CONTRACT_VERSION,
    validate_pre_finalize_contract,
    validate_pre_persist_contract,
)
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
    upsert_report_artifact,
    upsert_scouting_report,
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
        if isinstance(report_data.get("metadata"), dict):
            normalized_plane["metadata"] = report_data.get("metadata")
        if isinstance(report_data.get("detailed_analysis"), dict):
            normalized_plane["detailed_analysis"] = report_data.get("detailed_analysis")

    if not feature_plane:
        feature_plane = {
            "macro_analysis": _to_payload_dict(report_data.get("macro_analysis")),
            "mid_game_analysis": _to_payload_dict(report_data.get("mid_game_analysis")),
            "micro_analysis": _to_payload_dict(report_data.get("micro_analysis")),
            "actionable_insights": _to_payload_dict(report_data.get("actionable_insights")),
            "report_specific": _to_payload_dict(report_data.get("report_specific")),
        }

    return raw_plane, normalized_plane, feature_plane


def _persist_storage_planes(
    report_request_id: int,
    report_data: Dict[str, Any],
    feature_bundle: Optional[FeatureBundle] = None,
) -> None:
    raw_plane, normalized_plane, feature_plane = _extract_storage_planes(report_data)

    if feature_bundle is not None:
        feature_plane.update(feature_bundle.to_feature_plane_payloads())

    for key, payload in raw_plane.items():
        upsert_raw_payload(
            report_request_id=report_request_id,
            payload_key=_payload_key(key),
            payload=_to_payload_dict(payload),
            source_stage="INGESTING",
        )

    for key, payload in normalized_plane.items():
        upsert_normalized_payload(
            report_request_id=report_request_id,
            payload_key=_payload_key(key),
            payload=_to_payload_dict(payload),
            source_stage="FEATURIZING",
        )

    metadata = report_data.get("metadata") if isinstance(report_data.get("metadata"), dict) else {}
    feature_version = feature_bundle.feature_version if feature_bundle else metadata.get("feature_version", "features-v1")

    for key, payload in feature_plane.items():
        upsert_feature_payload(
            report_request_id=report_request_id,
            payload_key=_payload_key(key),
            payload=_to_payload_dict(payload),
            feature_version=feature_version,
            source_stage="FEATURIZING",
        )


def validate_feature_registry_compatibility(registry_version: str, expected_version: str) -> None:
    if registry_version != expected_version:
        raise RuntimeError(
            f"Feature registry version mismatch: registry={registry_version}, expected={expected_version}"
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


async def _run_job_pipeline(job_id: int, request_id: int, user_prompt: str, router: GeneralPromptRouter) -> None:
    update_report_job_stage(job_id, "FEATURIZING")
    _logger.info(f"Routing prompt through LLM for request {request_id}...")
    result = await router.resolve_user_prompt(user_prompt)

    if not (result and isinstance(result, dict)):
        raise ValueError("Router returned invalid result")

    report_data = result.get("output") or result.get("response")
    if not (report_data and isinstance(report_data, dict)):
        raise ValueError("Handler returned invalid report structure")

    if "report_type" not in report_data:
        if "player_name" in report_data:
            report_data["report_type"] = "player_performance"
        elif "map_name" in report_data:
            report_data["report_type"] = "map"
        elif "team_name_2" in report_data:
            report_data["report_type"] = "h2h"
        else:
            report_data["report_type"] = "full"

    if "error" in report_data:
        raise ValueError(str(report_data["error"]))

    feature_bundle = DEFAULT_FEATURE_REGISTRY.build(report_data)
    validate_pre_persist_contract(report_data=report_data, feature_bundle=feature_bundle)
    _persist_storage_planes(request_id, report_data, feature_bundle=feature_bundle)

    full_context = DEFAULT_FEATURE_REGISTRY.build_synthesis_context(report_data, feature_bundle)

    update_report_job_stage(job_id, "SYNTHESIZING")
    from transforms.insight_generator import generate_90_5_60_report

    _logger.info(f"Synthesizing 90-5-60 report for request {request_id}...")
    synthesized_report = await generate_90_5_60_report(full_context)

    update_report_job_stage(job_id, "COMPOSING")
    report_data = compose_report(
        base_report=report_data,
        feature_bundle=feature_bundle,
        synthesized_report=synthesized_report,
    )
    report_data["report_request_id"] = request_id
    validate_pre_finalize_contract(report_data)
    finalize_report(request_id, report_data)


async def _process_claimed_job(job: Dict[str, Any], router: GeneralPromptRouter) -> None:
    job_id = job["job_id"]
    request_id = job["report_request_id"]
    user_prompt = job["user_prompt"]

    _logger.info(
        f"Claimed job {job_id} for request {request_id} (attempt {job['attempt']}/{job['max_attempts']}): '{user_prompt}'"
    )
    update_report_request_status(request_id, "PROCESSING")

    try:
        await _run_job_pipeline(
            job_id=job_id,
            request_id=request_id,
            user_prompt=user_prompt,
            router=router,
        )

        complete_report_job(job_id)
        update_report_request_status(request_id, "COMPLETED")
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

        if fail_result["state"] == "QUEUED":
            update_report_request_status(request_id, "PENDING", error_message=error_msg)
            _logger.info(
                f"Job {job_id} re-queued for retry (attempt {fail_result['attempt']}/{fail_result['max_attempts']})"
            )
        else:
            update_report_request_status(request_id, "FAILED", error_message=error_msg)


async def process_next_job_once(runtime_worker_id: str, router: GeneralPromptRouter) -> bool:
    backfilled = ensure_pending_jobs_backfilled(limit=20)
    if backfilled:
        _logger.info(f"Backfilled {backfilled} report_jobs from legacy pending requests")

    job = claim_next_report_job(runtime_worker_id)
    if not job:
        return False

    await _process_claimed_job(job=job, router=router)
    return True


async def poll_and_process_reports() -> None:
    """
    Phase 2 orchestration worker:
      - backfills missing report_jobs for legacy pending requests
      - claims next job using SKIP LOCKED leasing
      - updates staged job progress and retries

    Phase 4 orchestration extension:
      - feature registry extraction (typed bundle)
      - synthesis using feature bundle context
      - report composition from feature bundle + synthesis output
    """
    runtime_worker_id = f"{WORKER_ID}-{socket.gethostname()}-{os.getpid()}"
    _logger.info(f"🚀 Starting Stratigen AI Analysis Worker (orchestration mode) worker_id={runtime_worker_id}")
    router = GeneralPromptRouter()

    while True:
        try:
            processed = await process_next_job_once(runtime_worker_id=runtime_worker_id, router=router)
            if not processed:
                _logger.debug("No runnable report jobs, sleeping...")
            await asyncio.sleep(POLL_TIME_IN_SECONDS)

        except Exception as ex:
            _logger.error(f"💥 Error in orchestration loop: {ex}", exc_info=True)
            await asyncio.sleep(10)


def start_worker():
    _logger.info("🎬 Starting Stratigen AI Engine...")
    validate_feature_registry_compatibility(
        registry_version=DEFAULT_FEATURE_REGISTRY.feature_version,
        expected_version=FEATURE_REGISTRY_VERSION,
    )
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

    metadata = report_data.get("metadata", {})
    if "flash_card" in report_data:
        metadata["flash_card"] = report_data.get("flash_card")
    if "coach_read" in report_data:
        metadata["coach_read"] = report_data.get("coach_read")
    if "analyst_appendix" in report_data:
        metadata["analyst_appendix"] = report_data.get("analyst_appendix")

    report_data["metadata"] = metadata

    report_payload_for_plane: Dict[str, Any] = {}

    try:
        report_types = ["full", "map", "player_performance", "agent_performance"]
        is_standard_report = (
            report_data.get("report_type") in report_types
            or "macro_analysis" in report_data
            or "micro_analysis" in report_data
            or "flash_card" in report_data
        )

        if is_standard_report:
            allowed_fields = ScoutingReport.model_fields.keys()
            filtered_data = {k: v for k, v in report_data.items() if k in allowed_fields}
            filtered_data["report_request_id"] = request_id

            report = ScoutingReport(**filtered_data)
            validated_data = report.model_dump()
            report_payload_for_plane = validated_data
            upsert_scouting_report(validated_data)
        else:
            if "report_request_id" not in report_data:
                report_data["report_request_id"] = request_id
            report_payload_for_plane = report_data
            upsert_scouting_report(report_data)
    except Exception as e:
        _logger.error(f"Validation failed for report {request_id}: {e}")
        if "report_request_id" not in report_data:
            report_data["report_request_id"] = request_id
        report_payload_for_plane = report_data
        upsert_scouting_report(report_data)

    model_version = metadata.get("model_version") if isinstance(metadata, dict) else None
    feature_version = metadata.get("feature_version") if isinstance(metadata, dict) else None
    contract_version = metadata.get("contract_version") if isinstance(metadata, dict) else REPORT_CONTRACT_VERSION

    upsert_report_artifact(
        report_request_id=request_id,
        report_type=report_data.get("report_type", "full"),
        report_payload=report_payload_for_plane,
        summary=report_data.get("generated_report", ""),
        model_version=model_version,
        feature_version=feature_version,
        contract_version=contract_version,
    )


if __name__ == "__main__":
    start_worker()
