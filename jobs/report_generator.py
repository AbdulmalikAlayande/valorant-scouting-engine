import time
from typing import Dict, Any, List
from config.globalutilitylogger import get_logger
from jobs.prompt_router import GeneralPromptRouter
from storage.db import get_db_cursor
from storage.upsert import update_report_request_status, upsert_scouting_report
from models.report import (
    ScoutingReport, AgentPick, MapPerformance, PlayerStat, 
    TeamComposition, HeadToHeadMatchup
)

from ingestion.fetch_match_details import ingest_game_details, ingest_series_state
from ingestion.fetch_stats import ingest_team_statistics, ingest_team_game_statistics, ingest_player_statistics
from ingestion.fetch_series import ingest_team_recent_series, ingest_series_by_time_range
from ingestion.fetch_teams import ingest_team_by_name, ingest_team_by_id, ingest_team_players
from ingestion.fetch_head_to_head import ingest_head_to_head_matches

from transforms.insight_generator import generate_how_to_win, format_actionable_bullets
from transforms.player_analysis import aggregate_player_performance, identify_high_impact_threats, map_player_to_agents
from transforms.team_analysis import calculate_win_rates, analyze_map_veto_strategy, detect_strategic_trends

_logger = get_logger(__name__)

def poll_and_process_jobs() -> None:
    """
    What: The main entry point that runs in a loop.
    Why: It checks the report_requests table for pending status, marks them as processing, and triggers the workflow.

    #Main loop for the Python worker.

    Polls and processes jobs from the job queue (report_requests table with status = 'pending').

    This function continuously polls for any pending jobs in the job queue and processes
    them according to predefined logic. It serves as the main entry point for handling
    job processing in the system.

    Raises:
        Exception: If an error occurs during job processing.
    """
    _logger.info("Starting Python Analysis Worker polling loop...")

    while True:
        try:
            with get_db_cursor() as cursor:
                cursor.execute("SELECT id, team_id, time_window FROM report_requests WHERE status = 'pending' LIMIT 1")
                job = cursor.fetchone()
            if job:
                _logger.info(f"Picking up job {job['id']} for team {job['team_id']}")
                router = GeneralPromptRouter()
                router.resolve_user_prompt("")
                execute_report_workflow(job['id'], job['team_id'], job['time_window'])

            time.sleep(5)
        except Exception as ex:
            _logger.error(f"Error processing job: {ex}")
            time.sleep(10)


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

    try:
        # The Ingestion Layer:
        _logger.info(f"Ingesting data for team {team_id}...")
        team_info = ingest_team_by_id(team_id=team_id)
        team_stats = ingest_team_statistics(team_id=team_id, time_window=time_window)
        team_game_stats = ingest_team_game_statistics(team_id=team_id, time_window=time_window)
        team_recent_series = ingest_team_recent_series(team_id=team_id)
        team_roster = ingest_team_players(team_id=team_id)

        # Ingesting Individual Player Statistics
        player_performances = []
        for player in team_roster.get("players", []):
            player_stats = ingest_player_statistics(player_id=player.get("id"), time_window=time_window)
            player_stats.update(
                {
                    "team_id": team_id,
                    "team_name": team_info.get("name", "Unknown Team")
                }
            )
            player_performances.append(PlayerStat(player_id=player.get("id"), **player_stats))

        # The Transformation Layer:
        _logger.info("Running analysis transformations...")
        map_dataframe = calculate_win_rates(team_game_stats=team_game_stats)
        map_veto_data = analyze_map_veto_strategy(map_stats=map_dataframe)
        strategic_trends = detect_strategic_trends(team_recent_series)

        player_dataframe = aggregate_player_performance(player_performances)
        player_threats = identify_high_impact_threats(player_dataframe)
        player_agents = map_player_to_agents(player_performances)

        # The Actionable Insights Generation Layer
        _logger.info("Generating actionable insights...")
        raw_insights = generate_how_to_win(map_veto_data, player_threats)
        final_actionable_insights = format_actionable_bullets(raw_insights)

        # Report Finalization and Persistence
        _logger.info("Finalizing report and persisting results...")
        report_data = {
            "report_request_id": request_id,
            "team_id": team_id,
            "team_name": team_info.name,
            "total_matches": team_stats['records'][0]['total_series'],
            "win_rate": team_stats['records'][0]['game_win_rate'],
            "current_streak": strategic_trends['win_streak'],
            "top_agents": team_game_stats['records'][0]['top_agents'],
            "map_performance": map_dataframe.to_dict(orient='records'),
            "player_stats": player_dataframe.to_dict(orient='records'),
            "actionable_insights": final_actionable_insights,
            "time_window": time_window,
            "map_veto_data": map_veto_data,
            "strategic_trends": strategic_trends,
            "player_agents": player_agents
        }

        upsert_scouting_report(report_data)
        update_report_request_status(request_id, "completed")
        _logger.info(f"Successfully completed report for request {request_id}")
        finalize_report(request_id, report_data)
    except Exception as ex:
        _logger.error(f"Workflow failed for request {request_id}: {ex}")
        update_report_request_status(request_id, 'failed', error_message=str(ex))

def execute_report_workflow_for_player(request_id, player_id, time_window: str) -> Dict[str, Any]:
    pass

def finalize_report(request_id, report_data) -> ScoutingReport:
    """
    What: Converts the final analysis into a ScoutingReport model and saves it to the scouting_reports table.
    Why: Ensures that the results are persisted and the job status is updated to 'completed'.
    """
    pass
