from typing import Any, Dict, List
from clients.domain.series import get_team_recent_series
from config.globalutilitylogger import get_logger

_logger = get_logger(__name__)


def ingest_team_recent_series(team_id: str, limit: int = 50) -> Dict[str, Any]:
    """
    Fetch a team's recent series list to determine which matches to analyze.
    Supports a limit for recency control. Returns a normalized dict containing
    an empty 'series' list as a stub until wired to data. Validates inputs and
    ensures the limit is a positive integer.
    """
    if not team_id or not team_id.strip():
        raise ValueError("team_id is required")
    if not isinstance(limit, int) or limit <= 0:
        raise ValueError("limit must be a positive integer")

    try:
        data = get_team_recent_series(team_id=team_id, limit=limit)

        series_list = data.get("series", [])

        if not series_list:
            _logger.warning(f"No series found for team {team_id}")
            return {
                "team_id": team_id.strip(),
                "limit": limit,
                "series": [],
                "meta": {"kind": "team_recent_series", "status": "no_data"},
            }

        normalized_series = []
        for series in series_list:
            normalized_series.append({
                "series_id": series.get("id"),
                "start_time": series.get("startTimeScheduled"),
                "tournament_id": series.get("tournament", {}).get("id"),
                "tournament_name": series.get("tournament", {}).get("name"),
                "format": series.get("format", {}).get("nameShortened"),
                "teams": [
                    {
                        "team_id": team.get("baseInfo", {}).get("id"),
                        "team_name": team.get("baseInfo", {}).get("name"),
                        "won": team.get("won", False)
                    }
                    for team in series.get("teams", [])
                ]
            })

        _logger.info(f"Ingested {len(normalized_series)} series for team {team_id}")

        return {
            "team_id": team_id.strip(),
            "limit": limit,
            "series": normalized_series,
            "meta": {"kind": "team_recent_series", "status": "success", "count": len(normalized_series)},
        }

    except Exception as e:
        _logger.error(f"Failed to ingest team recent series for {team_id}: {str(e)}")
        return {
            "team_id": team_id.strip(),
            "limit": limit,
            "series": [],
            "meta": {"kind": "team_recent_series", "status": "error", "error": str(e)},
        }


def ingest_series_by_tournament(team_id: str, tournament_id: str) -> Dict[str, Any]:
    """
    Fetch series for a team within a specific tournament. Useful for focused
    scouting tied to an event. Returns a normalized dict with an empty series
    list as a stub. Validates both IDs for non-empty values.

    Fetch series for a team in a specific tournament"""
    if not team_id or not team_id.strip() or not tournament_id or not tournament_id.strip():
        raise ValueError("team_id and tournament_id are required")

    # TODO: Add GraphQL query with tournament filter
    return {
        "team_id": team_id.strip(),
        "tournament_id": tournament_id.strip(),
        "series": [],
        "meta": {"kind": "tournament_series", "status": "stub"},
    }


def ingest_series_by_time_range(team_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Fetch series for a team between two ISO date strings. Enables time-bounded
    scouting (e.g., last month, split). Returns a normalized dict with an
    empty series list as a stub. Validates inputs but does not parse dates yet.
    Fetch series in a date range
    """
    if not team_id or not team_id.strip() or not start_date or not start_date.strip() or not end_date or not end_date.strip():
        raise ValueError("team_id, start_date, and end_date are required")

    # TODO: Add GraphQL query with date range filter
    return {
        "team_id": team_id.strip(),
        "start_date": start_date.strip(),
        "end_date": end_date.strip(),
        "series": [],
        "meta": {"kind": "series_by_time", "status": "stub"},
    }
