import json
from typing import Any, Dict, Optional

from config.globalutilitylogger import get_logger
from ingestion.fetch_teams import ingest_team_by_name, ingest_team_players
from ingestion.fetch_stats import (
    ingest_team_statistics,
    ingest_team_game_statistics,
    ingest_player_statistics
)
from ingestion.fetch_match_details import ingest_series_state
from ingestion.fetch_series import ingest_team_recent_series

from transforms.team_analysis import get_team_analysis_summary
from transforms.map_analysis import get_map_analysis_summary
from transforms.player_analysis import get_player_analysis_summary
from transforms.composition_analysis import get_composition_analysis_summary
from transforms.weakness_detection import get_weakness_detection_summary
from transforms.insight_generator import generate_how_to_win

_logger = get_logger(__name__)

def handle_generate_full_scouting_report(team_name: str, match_count: int, time_window: str) -> Dict[str, Any]:
    """
    Generate a complete scouting report for a team.

    This is the MASTER HANDLER that orchestrates all data fetching and analysis.
    It follows the Full Scouting Report Data Checklist exactly.

    Args:
        team_name: Name of the team (e.g., "Cloud9", "Team Liquid")
        match_count: Number of recent matches to analyze (not currently used - using time_window instead)
        time_window: "LAST_MONTH", "LAST_3_MONTHS", "LAST_6_MONTHS", "LAST_YEAR"

    Returns:
        Dict containing the complete scouting report:
        {
            "team_id": "1079",
            "team_name": "Cloud9",
            "time_window": "LAST_3_MONTHS",
            "macro_analysis": {...},
            "mid_game_analysis": {...},
            "micro_analysis": {...},
            "actionable_insights": ["✓ BAN Icebox...", ...],
            "meta": {"status": "success"}
        }
    """
    try:
        _logger.info(f"Generating full scouting report for {team_name}")

        # STEP 1: Resolve team name to ID
        _logger.info(f"Step 1: Resolving team '{team_name}'")
        team = ingest_team_by_name(team_name)

        if not team:
            _logger.error(f"Team '{team_name}' not found")
            return {
                "team_id": None,
                "team_name": team_name,
                "meta": {"status": "error", "error": "Team not found"}
            }

        team_id = team.id
        _logger.info(f"✓ Team resolved: {team.name} (ID: {team_id})")

        # STEP 2: Fetch all required data
        _logger.info("Step 2: Fetching data from GRID APIs")

        # Team-level aggregated stats
        team_stats = ingest_team_statistics(team_id=team_id, time_window=time_window)

        # Game-level stats (all maps)
        team_game_stats = ingest_team_game_statistics(
            team_id=team_id,
            time_window=time_window
        )

        # Get the team roster for player analysis
        roster = ingest_team_players(team_id=team_id)
        player_stats_list = []

        if roster.get('players'):
            _logger.info(f"Found {len(roster['players'])} players on roster")
            # Fetch stats for each player
            for player in roster['players'][:5]:  # Limit to 5 for performance
                player_id = player.get('id')
                if player_id:
                    player_stats = ingest_player_statistics(
                        player_id=player_id,
                        time_window=time_window
                    )
                    player_stats_list.append(player_stats)

        # Get recent series for composition analysis
        recent_series = ingest_team_recent_series(team_id=team_id, limit=5)

        # Get series state for at least one series
        series_state = {'series': None}
        if recent_series.get('series'):
            for series in recent_series['series']:
                series_id = series.get('series_id')
                if series_id:
                    series_state = ingest_series_state(series_id)
                    if series_state.get('series'):
                        break  # Got valid series state

        _logger.info("✓ All data fetched successfully")

        # STEP 3: Run all transform analyses
        _logger.info("Step 3: Running transform analyses")

        team_analysis = get_team_analysis_summary(team_stats)
        map_analysis = get_map_analysis_summary(team_game_stats)
        player_analysis = get_player_analysis_summary(player_stats_list)
        composition_analysis = get_composition_analysis_summary(series_state)
        weakness_analysis = get_weakness_detection_summary(team_stats, team_game_stats)

        _logger.info("✓ All analyses complete")

        # STEP 4: Generate actionable insights
        _logger.info("Step 4: Generating actionable insights")

        insights = generate_how_to_win(
            team_analysis,
            map_analysis,
            player_analysis,
            composition_analysis,
            weakness_analysis
        )

        _logger.info(f"✓ Generated {len(insights)} insights")

        # STEP 5: Package the complete report
        report = {
            "team_id": team_id,
            "team_name": team.name,
            "time_window": time_window,

            # MACRO ANALYSIS (The "Why")
            "macro_analysis": {
                "pistol_rounds": team_analysis.get('pistol_rounds'),
                "map_vetoes": map_analysis.get('veto_strategy'),
                "default_compositions": composition_analysis.get('default_comps', [])[:3],
                "early_aggression": weakness_analysis.get('early_aggression')
            },

            # MID-GAME ANALYSIS (The "How")
            "mid_game_analysis": {
                "side_balance": team_analysis.get('side_balance'),
                "objective_control": team_analysis.get('objective_control'),
                "economy_patterns": weakness_analysis.get('economy_patterns')
            },

            # MICRO ANALYSIS (The "Who")
            "micro_analysis": {
                "star_player": player_analysis.get('star_player'),
                "weak_link": player_analysis.get('weak_link'),
                "agent_pools": player_analysis.get('agent_pools')
            },

            # ACTIONABLE INSIGHTS (The "How to Win")
            "actionable_insights": insights,

            # Full detailed analysis (for advanced users)
            "detailed_analysis": {
                "team": team_analysis,
                "maps": map_analysis,
                "players": player_analysis,
                "compositions": composition_analysis,
                "weaknesses": weakness_analysis
            },

            # Metadata
            "meta": {
                "status": "success",
                "generated_at": None,  # Would use datetime.now()
                "data_sources": {
                    "team_stats": team_stats.get('meta'),
                    "team_game_stats": team_game_stats.get('meta'),
                    "player_stats_count": len(player_stats_list),
                    "series_state": series_state.get('meta')
                }
            }
        }

        _logger.info(f"✅ Full scouting report generated for {team.name}")

        return report

    except Exception as e:
        _logger.error(f"Failed to generate scouting report for {team_name}: {e}")
        import traceback
        traceback.print_exc()

        return {
            "team_id": None,
            "team_name": team_name,
            "meta": {
                "status": "error",
                "error": str(e)
            }
        }

def handle_generate_player_performance_analysis(player_name: str, match_count: int, time_window: str):
    pass

def handle_generate_tournament_performance_analysis(tournament_name: str, team_name: str):
    pass

def handle_generate_map_analysis(team_name: str, map_name: str, time_window: Optional[str]):
    pass

def handle_generate_team_head_to_head_analysis(team_name_1: str, team_name_2: str, match_count: int, time_window: str):
    pass

def handle_detect_and_exploit_weaknesses(team_name: str, match_count: int, time_window: str):
    pass

def handle_player_head_to_head_analysis(player_name_1: str, player_name_2: str, match_count: int, time_window: str):
    pass

def handle_composition_analysis(team_name: str):
    pass

def handle_generate_agent_performance_analysis(team_name: str):
    pass

def handle_generate_in_game_strategy_call(team_name: str, game_state_event: str, context_time_minutes: int):
    pass

def handle_exploit_specific_opponent_tell(opponent_name: str, tell_description: str):
    pass

def handle_time_period_analysis(period: str, player_name: Optional[str], team_name: Optional[str]):
    pass


if __name__ == '__main__':
    report = handle_generate_full_scouting_report("Team Liquid", 10, "LAST_6_MONTHS")
    with open("test_report.json", "w") as f:
        json.dump(report, f, indent=4)
