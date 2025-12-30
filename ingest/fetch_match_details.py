from typing import Any, Dict


def ingest_series_state(series_id: str) -> Dict[str, Any]:
    """
    Fetch detailed series state, including games, rounds, and player data.
    Enables agent picks, compositions, and round-by-round analysis. Returns a
    normalized stub dict with empty containers until connected to live data.
    Validates the series identifier.
    """
    if not series_id or not series_id.strip():
        raise ValueError("series_id is required")
    return {
        "series_id": series_id.strip(),
        "games": [],
        "rounds": [],
        "players": [],
        "meta": {"kind": "series_state", "status": "stub"},
    }


def ingest_game_details(series_id: str, game_id: str) -> Dict[str, Any]:
    """
    Fetch a single game's details within a series. Use to analyze round
    patterns, site preferences, tempo, and economy flows. Returns a normalized
    stub dict with empty structures until data wiring is added. Validates IDs.
    """
    if not series_id or not series_id.strip() or not game_id or not game_id.strip():
        raise ValueError("series_id and game_id are required")
    return {
        "series_id": series_id.strip(),
        "game_id": game_id.strip(),
        "rounds": [],
        "events": [],
        "meta": {"kind": "game_details", "status": "stub"},
    }