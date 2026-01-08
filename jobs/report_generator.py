import asyncio
import time
from typing import Dict, Any
from config.globalutilitylogger import get_logger
from jobs.prompt_router import GeneralPromptRouter
from storage.db import get_db_cursor
from storage.upsert import update_report_request_status, upsert_scouting_report, create_report_request
from models.report import ScoutingReport

_logger = get_logger(__name__)


async def poll_and_process_reports() -> None:
    """
    Main entry point for the Python Analysis Worker.

    What: Continuously polls the report_requests table for pending natural language prompts,
          routes them through the LLM-powered router, and executes the appropriate handler.

    Why: This is the bridge between the database job queue and the LLM-powered analysis system.
         It replaces the old rule-based routing with intelligent prompt understanding.

    Architecture Flow:
        1. Poll database for pending report requests
        2. Extract the natural language prompt from the request
        3. Use GeneralPromptRouter (LLM-powered) to determine the right tool/handler
        4. Execute the handler function (which calls ingestion + transform layers)
        5. Store results back to database
        6. Update request status to 'completed' or 'failed'

    Raises:
        Exception: Logs error and continues polling (resilient design)
    """
    _logger.info("🚀 Starting Python Analysis Worker with LLM-powered routing...")
    router = GeneralPromptRouter()

    while True:
        try:
            # Poll for pending jobs
            _logger.info(f"Polling DB for pending jobs")
            with get_db_cursor() as cursor:
                cursor.execute("""
                               SELECT id, user_prompt, created_at
                               FROM report_requests
                               WHERE status = 'pending'
                               ORDER BY created_at
                               LIMIT 1
                               """)
                job = cursor.fetchone()

            if job:
                request_id = job['id']
                user_prompt = job['user_prompt']

                _logger.info(f"Picked up job {request_id}: '{user_prompt}'")

                # Mark as processing
                update_report_request_status(request_id, 'processing')

                try:
                    # Route the prompt through LLM and execute handler
                    _logger.info(f"Routing prompt through LLM...")
                    result = await router.resolve_user_prompt(user_prompt)

                    # Extract the structured report from result
                    if result and isinstance(result, dict):
                        report_data = result.get('output') or result.get('response')

                        if report_data and isinstance(report_data, dict):
                            # Store the report
                            report_data['report_request_id'] = request_id
                            upsert_scouting_report(report_data)
                            finalize_report(request_id, report_data)
                            # Mark as completed
                            update_report_request_status(request_id, 'completed')
                            _logger.info(f"Job {request_id} completed successfully")
                        else:
                            _logger.warning(f"Handler returned invalid report structure")
                            # raise ValueError("Handler returned invalid report structure")
                    else:
                        raise ValueError("Router returned invalid result")

                except Exception as handler_error:
                    error_msg = str(handler_error)
                    _logger.error(f"Job {request_id} Failed: {error_msg}")
                    update_report_request_status(request_id, 'failed', error_message=error_msg)
            else:
                _logger.debug("No pending jobs, sleeping...")

            # Poll every 5 seconds
            await asyncio.sleep(5)

        except Exception as ex:
            _logger.error(f"💥 Error in polling loop: {ex}", exc_info=True)
            # Sleep longer on error to avoid hammering the database
            await asyncio.sleep(10)


def start_worker():
    """
    Synchronous wrapper to start the async polling loop.

    Usage:
        python -m jobs.report_generator
    """
    _logger.info("🎬 Starting Python Analysis Worker...")

    try:
        # Run the async polling loop
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
    What: Orchestrates the data fetching and transformation.
    Why: Separates the polling logic from the actual execution. It will call the ingestion layer to get raw data and the transforms layer to process it.

    # Orchestrates the data pipeline for a specific report

    Executes a report generation workflow based on the provided request ID, team ID,
    and time window. This workflow is typically used for running analytics or generating
    reports for a given team's data within a specified time period.

    Args:
        request_id (str): The unique identifier for the report generation request.
        team_id (str): The unique identifier for the team for which the report
            will be generated.
        time_window (tuple): A tuple containing the start and end times defining
            the time window for the report, in the format (start_time, end_time).

    Raises:
        ValueError: If any of the provided arguments are invalid or do not meet the
            required conditions for the report generation workflow.

    Returns:
        Dict[str, Any]: A dictionary containing the result of the workflow execution, such as
            the status of the report generation and potentially any relevant metadata.
    """
    pass

def finalize_report(request_id, report_data):
    """
    What: Converts the final analysis into a ScoutingReport model and saves it to the scouting_reports table.
    Why: Ensures that the results are persisted and the job status is updated to 'completed'.
    """
    _logger.info(f"Finalizing report {request_id}")
    report = ScoutingReport(**report_data)
    _logger.info(f"Report saved to DB: {report}")

if __name__ == '__main__':
    request_id_ = create_report_request("Generate a full scouting report for NRG in the last 6 months")
    request_id_1 = create_report_request("Generate a full scouting report for Cloud9 in the last 10 matches")
    request_id_2 = create_report_request("Scout Sentinels based on last 6 months")
    request_id_3 = create_report_request("How do we beat Cloud9?")

    print(f"Created request {request_id_}")
    start_worker()
