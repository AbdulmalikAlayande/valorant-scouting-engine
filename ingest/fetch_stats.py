from typing import Any, Dict, Optional, List

from clients.domain.stats import get_team_game_statistics, get_team_statistics
from config.globalutilitylogger import get_logger

_logger = get_logger(__name__)


def _empty_team_statistics_response(team_id, time_window):
    return {"team_id": team_id, "time_window": time_window, "records": []}


def _extract_win_data(won_param: List[Dict[str, Any]]) -> int:
    """Extract win count from the won array."""
    if not won_param or not isinstance(won_param, list):
        return 0

    for win_item in won_param:
        if isinstance(win_item, dict) and win_item.get("value") is True:
            return win_item.get("count", 0)
    return 0


def _extract_win_percentage(won_param: List[Dict[str, Any]]) -> float:
    """Extract win percentage from the won array."""
    if not won_param or not isinstance(won_param, list):
        return 0.0

    for win_item in won_param:
        if isinstance(win_item, dict) and win_item.get("value") is True:
            return win_item.get("percentage", 0.0)
    return 0.0


def _extract_first_kill_percentage(first_kill: List[Dict[str, Any]]) -> float:
    """Extract first kill percentage (percentage of games where team got first blood)."""
    if not first_kill or not isinstance(first_kill, list):
        return 0.0

    for item in first_kill:
        if isinstance(item, dict) and item.get("value") is True:
            return item.get("percentage", 0.0)
    return 0.0


def _extract_objective_avg(objectives: List[Dict[str, Any]], objective_type: str) -> float:
    """Extract average completions for a specific objective type."""
    if not objectives or not isinstance(objectives, list):
        return 0.0

    for obj in objectives:
        if isinstance(obj, dict) and obj.get("type") == objective_type:
            completion_count = obj.get("completionCount", {})
            if isinstance(completion_count, dict):
                return completion_count.get("avg", 0.0)
    return 0.0


def _extract_win_streak(won_param: List[Dict[str, Any]]) -> Dict[str, int]:
    """Extract win streak data (max, current)."""
    if not won_param or not isinstance(won_param, list):
        return {"max": 0, "current": 0}

    for win_item in won_param:
        if isinstance(win_item, dict) and win_item.get("value") is True:
            streak = win_item.get("streak", {})
            if isinstance(streak, dict):
                return {
                    "max": streak.get("max", 0),
                    "current": streak.get("current", 0)
                }
    return {"max": 0, "current": 0}


def _extract_side_data(segment_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract attack/defense side statistics from segment data."""
    attack_stats = {"rounds": 0, "wins": 0, "win_rate": 0.0}
    defense_stats = {"rounds": 0, "wins": 0, "win_rate": 0.0}

    if not segment_data or not isinstance(segment_data, list):
        return {"attack": attack_stats, "defense": defense_stats}

    for segment in segment_data:
        if not isinstance(segment, dict):
            continue

        segment_type = segment.get("type")
        if segment_type not in ["attack", "defense"]:
            continue

        count = segment.get("count", 0)
        won_list = segment.get("won", [])

        wins = 0
        win_rate = 0.0
        for win_item in won_list:
            if isinstance(win_item, dict) and win_item.get("value") is True:
                wins = win_item.get("count", 0)
                win_rate = win_item.get("percentage", 0.0)
                break

        if segment_type == "attack":
            attack_stats = {
                "rounds": count,
                "wins": wins,
                "win_rate": win_rate
            }
        elif segment_type == "defense":
            defense_stats = {
                "rounds": count,
                "wins": wins,
                "win_rate": win_rate
            }

    return {"attack": attack_stats, "defense": defense_stats}


def ingest_team_statistics(team_id: str, time_window: str) -> Dict[str, Any]:
    """
    Fetch overall team statistics for a given period. Used to compute headline
    metrics for reports such as win rate, K/D, and streaks. Returns a normalized
    dict with TeamStats model and metadata for storage or downstream transforms.

    Handles cases where no data exists (returns zeros/empty values).

    Args:
        team_id: Team ID
        time_window: "LAST_MONTH", "LAST_3_MONTHS", "LAST_6_MONTHS", "LAST_YEAR"

    Returns:
        Dict[str, Any]: Normalized dict with TeamStats model and metadata
    """

    if not team_id or not team_id.strip():
        raise ValueError("team_id is required")
    if not time_window or not time_window.strip():
        raise ValueError("time_window is required")

    team_id = team_id.strip()
    time_window = time_window.strip()

    try:
        data = get_team_statistics(team_id=team_id, time_window=time_window)
        if not data or not isinstance(data, dict) or len(data.get("aggregationSeriesIds", [])) == 0:
            _logger.warning(f"No statistics found for team {team_id} in {time_window}")
            return _empty_team_statistics_response(team_id, time_window)

        # Extract nested data with safe defaults
        series_data = data.get("series", {})
        game_data = data.get("game", {})
        segment_data = data.get("segment", [])

        # Extract aggregation IDs (which series were included)
        aggregated_series_ids = data.get("aggregationSeriesIds", [])

        # Series-level metrics
        total_series = series_data.get("count", 0)
        series_won = _extract_win_data(series_data.get("won", []))
        series_win_rate = _extract_win_percentage(series_data.get("won", []))

        # Game-level metrics
        total_games = game_data.get("count", 0)
        games_won = _extract_win_data(game_data.get("won", []))
        game_win_rate = _extract_win_percentage(game_data.get("won", []))

        # Win streaks
        win_streak = _extract_win_streak(game_data.get("won", []))

        # Combat stats
        kills = game_data.get("kills", {})
        deaths = game_data.get("deaths", {})
        assists = game_data.get("assists", {})

        kills_total = kills.get("sum", 0)
        deaths_total = deaths.get("sum", 0)
        assists_total = assists.get("sum", 0)

        kills_avg = kills.get("avg", 0.0)
        deaths_avg = deaths.get("avg", 0.0)
        assists_avg = assists.get("avg", 0.0)

        kills_max = kills.get("max", 0)
        deaths_min = deaths.get("min", 0)

        # Calculate K/D ratio safely
        kd_ratio = round(kills_total / deaths_total, 2) if deaths_total > 0 else 0.0

        # First bloods
        first_kill = game_data.get("firstKill", [])
        first_bloods_percentage = _extract_first_kill_percentage(first_kill)

        # VALORANT-specific objectives (check if exists in response)
        objectives = game_data.get("objectives", [])

        spikes_planted_avg = _extract_objective_avg(objectives, "plantBomb")
        spikes_defused_avg = _extract_objective_avg(objectives, "defuseBomb")
        bomb_explosions_avg = _extract_objective_avg(objectives, "explodeBomb")
        ultimate_orbs_avg = _extract_objective_avg(objectives, "captureUltimateOrb")

        # Economy
        net_worth = game_data.get("netWorth", {})
        money = game_data.get("money", {})

        avg_net_worth = net_worth.get("avg", 0.0)
        avg_spend = money.get("avg", 0.0)

        # Tactical tendencies from segments (attack/defense split)
        side_stats = _extract_side_data(segment_data)

        # Build the normalized response
        team_stats = {
            # Identifiers
            "team_id": team_id,
            "time_window": time_window,
            "aggregated_series_ids": aggregated_series_ids,

            # Series metrics
            "total_series": total_series,
            "series_won": series_won,
            "series_win_rate": series_win_rate,

            # Game metrics
            "total_games": total_games,
            "games_won": games_won,
            "game_win_rate": game_win_rate,
            "win_streak_max": win_streak["max"],
            "win_streak_current": win_streak["current"],

            # Combat stats
            "kills_total": kills_total,
            "kills_avg": kills_avg,
            "kills_max": kills_max,
            "deaths_total": deaths_total,
            "deaths_avg": deaths_avg,
            "deaths_min": deaths_min,
            "assists_total": assists_total,
            "assists_avg": assists_avg,
            "kd_ratio": kd_ratio,

            # First bloods
            "first_bloods_percentage": first_bloods_percentage,

            # VALORANT objectives
            "spikes_planted_avg": spikes_planted_avg,
            "spikes_defused_avg": spikes_defused_avg,
            "bomb_explosions_avg": bomb_explosions_avg,
            "ultimate_orbs_avg": ultimate_orbs_avg,

            # Economy
            "avg_net_worth": avg_net_worth,
            "avg_spend": avg_spend,

            # Side splits
            "attack_rounds": side_stats["attack"]["rounds"],
            "attack_wins": side_stats["attack"]["wins"],
            "attack_win_rate": side_stats["attack"]["win_rate"],
            "defense_rounds": side_stats["defense"]["rounds"],
            "defense_wins": side_stats["defense"]["wins"],
            "defense_win_rate": side_stats["defense"]["win_rate"],
        }

        _logger.info(f"Successfully ingested team statistics for {team_id} ({time_window}): "
                     f"{total_games} games, {game_win_rate:.1f}% win rate")

        return {
            "team_id": team_id,
            "time_window": time_window,
            "records": [team_stats],
            "meta": {
                "kind": "team_overall",
                "status": "success",
                "series_count": total_series,
                "game_count": total_games
            },
        }

    except Exception as e:
        _logger.error(f"Failed to ingest team statistics for {team_id} ({time_window}): {str(e)}")
        return {
            "team_id": team_id,
            "time_window": time_window,
            "records": [],
            "meta": {
                "kind": "team_overall",
                "status": "error",
                "error": str(e)
            },
        }


def ingest_team_game_statistics(
        team_id: str, time_window: str, map_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch per-game/map statistics for a team in a time window. Use for map
    performance analysis and veto logic (e.g., WR by map/side). Returns a
    normalized dict with an optional map filter echoed for traceability. Inputs
    are validated; implementation is a stub to be connected to data later.
    """
    if not team_id or not team_id.strip() or not time_window or not time_window.strip():
        raise ValueError("team_id and time_window are required")

    data = get_team_game_statistics(team_id=team_id, time_window=time_window, map_ids=[map_filter])

    return {
        "team_id": team_id.strip(),
        "time_window": time_window.strip(),
        "map_filter": map_filter.strip() if isinstance(map_filter, str) else None,
        "records": [],
        "meta": {"kind": "team_game", "status": "stub"},
    }


def ingest_player_statistics(player_id: str, time_window: str) -> Dict[str, Any]:
    """
    Fetch player-level stats over a time window. Use to build player tendencies,
    agent pools, and outlier detection. Returns a normalized dict with metadata
    for downstream transforms. Validates inputs and returns a stub until actual
    data wiring is added.
    """
    if not player_id or not player_id.strip() or not time_window or not time_window.strip():
        raise ValueError("player_id and time_window are required")
    return {
        "player_id": player_id.strip(),
        "time_window": time_window.strip(),
        "records": [],
        "meta": {"kind": "player_overall", "status": "stub"},
    }
