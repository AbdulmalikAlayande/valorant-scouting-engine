from typing import Any, Dict, Optional


def ingest_team_statistics(team_id: str, time_window: str) -> Dict[str, Any]:
    """
    Fetch overall team statistics for a given period. Used to compute headline
    metrics for reports such as win rate, K/D, and streaks. Returns a normalized
    dict with 'meta' and 'records' keys suitable for storage or downstream
    transforms. Validates inputs and returns a stub payload until wired to data.
    """
    if not team_id or not team_id.strip() or not time_window or not time_window.strip():
        raise ValueError("team_id and time_window are required")

    return {
        "team_id": team_id.strip(),
        "time_window": time_window.strip(),
        "records": [],
        "meta": {"kind": "team_overall", "status": "stub"},
    }


def ingest_team_game_statistics(
    team_id: str, time_window: str, map_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch per-game/map statistics for a team in a time window. Use for map
    performance analysis and veto logic (e.g., WR by map/side). Returns a
    normalized dict with optional map filter echoed for traceability. Inputs
    are validated; implementation is a stub to be connected to data later.
    """
    if not team_id or not team_id.strip() or not time_window or not time_window.strip():
        raise ValueError("team_id and time_window are required")
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

