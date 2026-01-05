from typing import Optional

from config.globalutilitylogger import get_logger
from ingestion.fetch_teams import ingest_team_by_name

_logger = get_logger(__name__)

def handle_generate_full_scouting_report(team_name: str, match_count: int, time_window: str):
    """
    """
    _logger.info(f"Ingesting data for team {team_name}...")
    team_info = ingest_team_by_name(team_name=team_name)

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
