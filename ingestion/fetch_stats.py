from typing import Any, Dict, Optional, List

from clients.domain.stats import get_player_statistics, get_team_game_statistics, get_team_statistics
from config.globalutilitylogger import get_logger

_logger = get_logger(__name__)


def _empty_team_statistics_response(team_id, time_window):
    return {"team_id": team_id, "time_window": time_window, "records": []}


def _extract_win_data(won_param: List[Dict[str, Any]]) -> int:
    """Extract the win count from the won array."""
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
    """Extract first kill percentage (percentage of games where a team got first blood)."""
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


def _extract_objective_data(objectives: List[Dict[str, Any]], objective_type: str) -> Dict[str, Any]:
    """Extract completion count and first completion data for a specific objective."""
    if not objectives or not isinstance(objectives, list):
        return {
            "count_sum": 0,
            "count_avg": 0.0,
            "completed_first_percentage": 0.0
        }

    for obj in objectives:
        if isinstance(obj, dict) and obj.get("type") == objective_type:
            completion_count = obj.get("completionCount", {})
            completed_first = obj.get("completedFirst", [])

            count_sum = completion_count.get("sum", 0) if isinstance(completion_count, dict) else 0
            count_avg = completion_count.get("avg", 0.0) if isinstance(completion_count, dict) else 0.0

            # Get percentage where value is True
            first_percentage = 0.0
            if isinstance(completed_first, list):
                for item in completed_first:
                    if isinstance(item, dict) and item.get("value") is True:
                        first_percentage = item.get("percentage", 0.0)
                        break

            return {
                "count_sum": count_sum,
                "count_avg": count_avg,
                "completed_first_percentage": first_percentage
            }

    return {
        "count_sum": 0,
        "count_avg": 0.0,
        "completed_first_percentage": 0.0
    }


def _extract_character_picks(players_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract agent pick rates from players.characters data."""
    if not players_data or not isinstance(players_data, dict):
        return []

    characters = players_data.get("characters", [])
    if not isinstance(characters, list):
        return []

    agent_picks = []
    for char_data in characters:
        if not isinstance(char_data, dict):
            continue

        character = char_data.get("character", {})
        if not isinstance(character, dict):
            continue

        agent_picks.append({
            "agent_id": character.get("id", "unknown"),
            "agent_name": character.get("name", "Unknown"),
            "count": char_data.get("count", 0),
            "percentage": char_data.get("percentage", 0.0)
        })

    # Sort by count descending (most picked first)
    agent_picks.sort(key=lambda x: x["count"], reverse=True)
    return agent_picks


def _parse_duration_to_seconds(duration_str: str) -> float:
    """Parse ISO 8601 duration string to seconds (e.g., 'PT49M28.05372S' -> 2968.05)."""
    if not duration_str or not isinstance(duration_str, str):
        return 0.0

    try:
        # Simple parser for PT format: PT[hours]H[minutes]M[seconds]S
        import re

        # Remove PT prefix
        duration = duration_str.replace("PT", "")

        hours = 0
        minutes = 0
        seconds = 0.0

        # Extract hours
        hour_match = re.search(r'(\d+)H', duration)
        if hour_match:
            hours = int(hour_match.group(1))

        # Extract minutes
        minute_match = re.search(r'(\d+)M', duration)
        if minute_match:
            minutes = int(minute_match.group(1))

        # Extract seconds
        second_match = re.search(r'([\d.]+)S', duration)
        if second_match:
            seconds = float(second_match.group(1))

        return hours * 3600 + minutes * 60 + seconds
    except Exception as e:
        _logger.error(f"Failed to parse duration string {duration_str}: {str(e)}")
        return 0.0


def ingest_team_game_statistics(
        team_id: str, time_window: str, map_filter: Optional[Dict[str, str]] = None, opponent_team_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Fetch per-game/map statistics for a team in a time window. Use for map
    performance analysis and veto logic (e.g., WR by map/side). Returns a
    normalized dict with an optional map filter echoed for traceability.

    Includes agent pick rates, objective completion rates, and game-level combat stats.

    Args:
        team_id: Team ID
        time_window: "LAST_MONTH", "LAST_3_MONTHS", "LAST_6_MONTHS", "LAST_YEAR"
        map_filter: Optional map ID to filter by specific map
        opponent_team_ids: Optional list of opponent team IDs to filter by specific opponent teams

    Returns:
        Dict[str, Any]: Normalized dict with game-level stats and metadata
    """
    if not team_id or not team_id.strip():
        raise ValueError("team_id is required")
    if not time_window or not time_window.strip():
        raise ValueError("time_window is required")

    team_id = team_id.strip()
    time_window = time_window.strip()

    try:
        # Call the actual API with map filter if provided
        game_stats = get_team_game_statistics(
            team_id=team_id,
            time_window=time_window,
            map_name_contains_or_eq=map_filter if map_filter else None,
            opponent_team_ids=opponent_team_ids if opponent_team_ids else None
        )

        if not game_stats:
            _logger.warning(f"No game statistics found for team {team_id} in {time_window}")
            return {
                "team_id": team_id,
                "time_window": time_window,
                "map_filter": map_filter,
                "records": [],
                "meta": {"kind": "team_game", "status": "no_data"}
            }

        if not isinstance(game_stats, dict):
            _logger.warning(f"Invalid game statistics structure for team {team_id}")
            return {
                "team_id": team_id,
                "time_window": time_window,
                "map_filter": map_filter,
                "records": [],
                "meta": {"kind": "team_game", "status": "invalid_structure"}
            }

        # Extract game count
        game_count = game_stats.get("count", 0)
        if game_count == 0:
            _logger.info(f"No games found for team {team_id} in {time_window}")
            return {
                "team_id": team_id,
                "time_window": time_window,
                "map_filter": map_filter,
                "records": [],
                "meta": {"kind": "team_game", "status": "no_games"}
            }

        # Extract win data
        won_list = game_stats.get("won", [])
        games_won = _extract_win_data(won_list)
        game_win_rate = _extract_win_percentage(won_list)
        win_streak = _extract_win_streak(won_list)

        # Extract combat stats
        kills = game_stats.get("kills", {})
        deaths = game_stats.get("deaths", {})
        kill_assists = game_stats.get("killAssistsGiven", {})

        kills_total = kills.get("sum", 0)
        kills_avg = kills.get("avg", 0.0)
        kills_min = kills.get("min", 0)
        kills_max = kills.get("max", 0)

        deaths_total = deaths.get("sum", 0)
        deaths_avg = deaths.get("avg", 0.0)
        deaths_min = deaths.get("min", 0)
        deaths_max = deaths.get("max", 0)

        assists_total = kill_assists.get("sum", 0)
        assists_avg = kill_assists.get("avg", 0.0)

        # Calculate K/D ratio
        kd_ratio = round(kills_total / deaths_total, 2) if deaths_total > 0 else 0.0

        # Extract first blood data
        first_kill = game_stats.get("firstKill", [])
        first_bloods_percentage = _extract_first_kill_percentage(first_kill)

        # Extract economy stats
        money = game_stats.get("money", {})
        inventory_value = game_stats.get("inventoryValue", {})
        net_worth = game_stats.get("netWorth", {})

        avg_money = money.get("avg", 0.0)
        avg_inventory_value = inventory_value.get("avg", 0.0)
        avg_net_worth = net_worth.get("avg", 0.0)

        # Extract team kills (friendly fire) and self-kills
        teamkills = game_stats.get("teamkills", {})
        selfkills = game_stats.get("selfkills", {})

        teamkills_total = teamkills.get("sum", 0)
        selfkills_total = selfkills.get("sum", 0)

        # Extract score
        score = game_stats.get("score", {})
        score_total = score.get("sum", 0)
        score_avg = score.get("avg", 0.0)

        # Extract objective data
        objectives = game_stats.get("objectives", [])

        plant_bomb = _extract_objective_data(objectives, "plantBomb")
        defuse_bomb = _extract_objective_data(objectives, "defuseBomb")
        explode_bomb = _extract_objective_data(objectives, "explodeBomb")
        begin_defuse = _extract_objective_data(objectives, "beginDefuseBomb")
        stop_defuse = _extract_objective_data(objectives, "stopDefuseBomb")
        reach_defuse_checkpoint = _extract_objective_data(objectives, "reachDefuseBombCheckpoint")
        capture_ultimate_orb = _extract_objective_data(objectives, "captureUltimateOrb")

        # Extract agent picks
        players_data = game_stats.get("players", {})
        agent_picks = _extract_character_picks(players_data)

        # Extract duration
        duration = game_stats.get("duration", {})
        duration_avg_str = duration.get("avg", "PT0S")
        avg_game_duration_seconds = _parse_duration_to_seconds(duration_avg_str)

        # Build normalized game statistics
        # Extract map name from filter if present
        map_name = None
        if map_filter:
            if isinstance(map_filter, dict):
                map_name = map_filter.get("equals") or map_filter.get("contains")
            else:
                map_name = str(map_filter)

        game_data = {
            "team_id": team_id,
            "time_window": time_window,
            "map_filter": map_name,

            # Game count and wins
            "game_count": game_count,
            "games_won": games_won,
            "game_win_rate": game_win_rate,
            "win_streak_max": win_streak["max"],
            "win_streak_current": win_streak["current"],

            # Combat stats
            "kills_total": kills_total,
            "kills_avg": kills_avg,
            "kills_min": kills_min,
            "kills_max": kills_max,
            "deaths_total": deaths_total,
            "deaths_avg": deaths_avg,
            "deaths_min": deaths_min,
            "deaths_max": deaths_max,
            "assists_total": assists_total,
            "assists_avg": assists_avg,
            "kd_ratio": kd_ratio,

            # First bloods
            "first_bloods_percentage": first_bloods_percentage,

            # Mistakes
            "teamkills_total": teamkills_total,
            "selfkills_total": selfkills_total,

            # Score
            "score_total": score_total,
            "score_avg": score_avg,

            # Economy
            "avg_money": avg_money,
            "avg_inventory_value": avg_inventory_value,
            "avg_net_worth": avg_net_worth,

            # Objectives - Plant
            "plant_bomb_total": plant_bomb["count_sum"],
            "plant_bomb_avg": plant_bomb["count_avg"],
            "plant_bomb_first_percentage": plant_bomb["completed_first_percentage"],

            # Objectives - Defuse
            "defuse_bomb_total": defuse_bomb["count_sum"],
            "defuse_bomb_avg": defuse_bomb["count_avg"],
            "defuse_bomb_first_percentage": defuse_bomb["completed_first_percentage"],

            "begin_defuse_total": begin_defuse["count_sum"],
            "begin_defuse_avg": begin_defuse["count_avg"],

            "stop_defuse_total": stop_defuse["count_sum"],
            "stop_defuse_avg": stop_defuse["count_avg"],

            "reach_defuse_checkpoint_total": reach_defuse_checkpoint["count_sum"],
            "reach_defuse_checkpoint_avg": reach_defuse_checkpoint["count_avg"],

            # Objectives - Explode
            "explode_bomb_total": explode_bomb["count_sum"],
            "explode_bomb_avg": explode_bomb["count_avg"],
            "explode_bomb_first_percentage": explode_bomb["completed_first_percentage"],

            # Objectives - Ultimate orbs
            "capture_ultimate_orb_total": capture_ultimate_orb["count_sum"],
            "capture_ultimate_orb_avg": capture_ultimate_orb["count_avg"],

            # Agent picks (top 5 for brevity)
            "top_agents": agent_picks[:5] if agent_picks else [],
            "total_unique_agents": len(agent_picks),

            # Duration
            "avg_game_duration_seconds": avg_game_duration_seconds,
        }

        _logger.info(f"Successfully ingested game statistics for {team_id} ({time_window}): "
                     f"{game_count} games, {game_win_rate:.1f}% win rate")

        return {
            "team_id": team_id,
            "time_window": time_window,
            "map_filter": map_filter,
            "records": [game_data],
            "meta": {
                "kind": "team_game",
                "status": "success",
                "game_count": game_count,
                "unique_agents_played": len(agent_picks)
            }
        }

    except Exception as e:
        _logger.error(f"Failed to ingest game statistics for {team_id} ({time_window}): {str(e)}")
        return {
            "team_id": team_id,
            "time_window": time_window,
            "map_filter": map_filter,
            "records": [],
            "meta": {
                "kind": "team_game",
                "status": "error",
                "error": str(e)
            }
        }


# python
def ingest_player_statistics(player_id: str, time_window: str) -> Dict[str, Any]:
    """
    Fetch player-level stats over a time window. Returns a normalized dict with
    a single record (or empty records list) and metadata.

    Uses helper extractors in this module to pull wins, percentages, objectives,
    and first-kill rates from the GRID response shape (see clients/response/player-statistics.json).
    """
    if not player_id or not player_id.strip():
        raise ValueError("player_id is required")
    if not time_window or not time_window.strip():
        raise ValueError("time_window is required")

    player_id = player_id.strip()
    time_window = time_window.strip()

    try:
        data = get_player_statistics(player_id=player_id, time_window=time_window)
        if not data or not isinstance(data, dict):
            _logger.warning(f"No player statistics found for {player_id} ({time_window})")
            return {
                "player_id": player_id,
                "time_window": time_window,
                "records": [],
                "meta": {"kind": "player_statistics", "status": "not_found"},
            }

        # GRID returns a shape with 'series' and 'game' keys
        series = data.get("series", {}) or {}
        game = data.get("game", {}) or {}

        # Series-level
        series_count = series.get("count", 0)
        series_wins = _extract_win_data(series.get("won", []))
        series_win_rate = _extract_win_percentage(series.get("won", []))

        # Game-level
        game_count = game.get("count", 0)
        game_wins = _extract_win_data(game.get("won", []))
        game_win_rate = _extract_win_percentage(game.get("won", []))

        # Combat / rates from game bucket (preferred for per-game numbers)
        kills = game.get("kills", {}) or {}
        kills_total = kills.get("sum", 0)
        kills_avg = kills.get("avg", 0.0)
        kills_min = kills.get("min", 0)
        kills_max = kills.get("max", 0)

        deaths = game.get("deaths", {}) or {}
        deaths_total = deaths.get("sum", 0)
        deaths_avg = deaths.get("avg", 0.0)
        deaths_min = deaths.get("min", 0)
        deaths_max = deaths.get("max", 0)

        kill_assists_given = game.get("killAssistsGiven", {}) or {}
        kag_total = kill_assists_given.get("sum", 0)
        kag_avg = kill_assists_given.get("avg", 0.0)

        kill_assists_received = game.get("killAssistsReceived", {}) or {}
        kar_total = kill_assists_received.get("sum", 0)
        kar_avg = kill_assists_received.get("avg", 0.0)

        # First kill / first blood
        first_kill_pct = _extract_first_kill_percentage(game.get("firstKill", []))

        # Objectives (game-level)
        objectives = game.get("objectives", []) or []
        plant_avg = _extract_objective_avg(objectives, "plantBomb")
        defuse_avg = _extract_objective_avg(objectives, "defuseBomb")
        explode_avg = _extract_objective_avg(objectives, "explodeBomb")
        begin_defuse_avg = _extract_objective_avg(objectives, "beginDefuseBomb")
        capture_ultimate_avg = _extract_objective_avg(objectives, "captureUltimateOrb")

        # Assemble normalized record
        record: Dict[str, Any] = {
            "player_id": player_id,
            "time_window": time_window,
            "series": {
                "count": series_count,
                "wins": series_wins,
                "win_rate": series_win_rate,
            },
            "games": {
                "count": game_count,
                "wins": game_wins,
                "win_rate": game_win_rate,
                "first_kill_percentage": first_kill_pct,
            },
            "combat": {
                "kills": {"total": kills_total, "avg": kills_avg, "min": kills_min, "max": kills_max},
                "deaths": {"total": deaths_total, "avg": deaths_avg, "min": deaths_min, "max": deaths_max},
                "kill_assists_given": {"total": kag_total, "avg": kag_avg},
                "kill_assists_received": {"total": kar_total, "avg": kar_avg},
            },
            "objectives": {
                "plant_avg": plant_avg,
                "defuse_avg": defuse_avg,
                "explode_avg": explode_avg,
                "begin_defuse_avg": begin_defuse_avg,
                "capture_ultimate_avg": capture_ultimate_avg,
            },
            "raw": data,
        }

        _logger.info(f"Ingested player statistics for {player_id} ({time_window})")
        return {
            "player_id": player_id,
            "time_window": time_window,
            "records": [record],
            "meta": {"kind": "player_statistics", "status": "ok", "record_count": 1},
        }

    except Exception as e:
        _logger.error(f"Failed to ingest player statistics for {player_id} ({time_window}): {str(e)}")
        return {
            "player_id": player_id,
            "time_window": time_window,
            "records": [],
            "meta": {"kind": "player_statistics", "status": "error", "error": str(e)},
        }


if __name__ == '__main__':
    result = ingest_team_game_statistics("1079", time_window="LAST_6_MONTHS", opponent_team_ids=["79", "94"])
    print(result)
