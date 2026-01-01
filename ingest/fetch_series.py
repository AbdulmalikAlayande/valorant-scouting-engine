from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from clients.domain.series import (
    get_series_by_time_range,
    get_series_by_tournament,
    get_team_recent_series,
)
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
            normalized_series.append(
                {
                    "series_id": series.get("id"),
                    "start_time": series.get("startTimeScheduled"),
                    "tournament_id": (series.get("tournament") or {}).get("id"),
                    "tournament_name": (series.get("tournament") or {}).get("name"),
                    "format": (series.get("format") or {}).get("nameShortened"),
                    "teams": [
                        {
                            "team_id": (team.get("baseInfo") or {}).get("id"),
                            "team_name": (team.get("baseInfo") or {}).get("name"),
                            "won": team.get("won", False),
                            "score_advantage": team.get("scoreAdvantage"),
                        }
                        for team in series.get("teams", [])
                        if isinstance(team, dict)
                    ],
                }
            )

        _logger.info(f"Ingested {len(normalized_series)} series for team {team_id}")

        return {
            "team_id": team_id.strip(),
            "limit": limit,
            "series": normalized_series,
            "meta": {
                "kind": "team_recent_series",
                "status": "success",
                "count": len(normalized_series),
            },
        }

    except Exception as e:
        _logger.error(f"Failed to ingest team recent series for {team_id}: {str(e)}")
        return {
            "team_id": team_id.strip(),
            "limit": limit,
            "series": [],
            "meta": {"kind": "team_recent_series", "status": "error", "error": str(e)},
        }


def ingest_series_by_tournament(team_id: str, tournament_id: str, limit: int = 50) -> Dict[str, Any]:
    """
    Fetch series for a team within a specific tournament.

    Implementation notes:
    - clients.domain.series.get_series_by_tournament filters by tournament, not team
    - We additionally filter the returned series to those that include `team_id`
      to satisfy "for a team within a tournament".
    """
    team_id = _require_non_empty(team_id, "team_id")
    tournament_id = _require_non_empty(tournament_id, "tournament_id")
    if not isinstance(limit, int) or limit <= 0:
        raise ValueError("limit must be a positive integer")

    try:
        data = get_series_by_tournament(tournament_id=tournament_id, limit=limit) or {}
        series_list = data.get("series", []) if isinstance(data, dict) else []

        # Filter to series where team appears
        filtered = [s for s in series_list if _series_contains_team(s, team_id)]
        normalized = _normalize_series_list(filtered)

        status = "success" if normalized else "no_data"
        if not normalized:
            _logger.warning(
                f"No tournament series found for team_id={team_id} in tournament_id={tournament_id}"
            )

        return {
            "team_id": team_id,
            "tournament_id": tournament_id,
            "limit": limit,
            "series": normalized,
            "meta": {
                "kind": "tournament_series",
                "status": status,
                "count": len(normalized),
                "source_total": len(series_list),
            },
        }

    except Exception as e:
        _logger.error(
            f"Failed to ingest series by tournament for team_id={team_id}, tournament_id={tournament_id}: {e}"
        )
        return {
            "team_id": team_id,
            "tournament_id": tournament_id,
            "limit": limit,
            "series": [],
            "meta": {"kind": "tournament_series", "status": "error", "error": str(e)},
        }


def ingest_series_by_time_range(
        team_id: str, start_date: str, end_date: str, limit: int = 50
) -> Dict[str, Any]:
    """
    Fetch series for a team between two ISO date strings.

    Implementation notes:
    - clients.domain.series.get_series_by_time_range filters by date range, not team
    - We additionally filter the returned series to those that include `team_id`
    - We validate that the date strings are parseable ISO-8601 and that start <= end
    """
    team_id = _require_non_empty(team_id, "team_id")
    start_date = _require_non_empty(start_date, "start_date")
    end_date = _require_non_empty(end_date, "end_date")
    if not isinstance(limit, int) or limit <= 0:
        raise ValueError("limit must be a positive integer")

    # Validate ISO format (best-effort) + range sanity
    start_dt = _parse_iso_datetime(start_date)
    end_dt = _parse_iso_datetime(end_date)
    if start_dt and end_dt and start_dt > end_dt:
        raise ValueError("start_date must be <= end_date")

    try:
        data = get_series_by_time_range(start_date=start_date, end_date=end_date, limit=limit) or {}
        series_list = data.get("series", []) if isinstance(data, dict) else []

        filtered = [s for s in series_list if _series_contains_team(s, team_id)]
        normalized = _normalize_series_list(filtered)

        status = "success" if normalized else "no_data"
        if not normalized:
            _logger.warning(
                f"No time-range series found for team_id={team_id} within {start_date}..{end_date}"
            )

        return {
            "team_id": team_id,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "series": normalized,
            "meta": {
                "kind": "series_by_time",
                "status": status,
                "count": len(normalized),
                "source_total": len(series_list),
            },
        }

    except Exception as e:
        _logger.error(
            f"Failed to ingest series by time range for team_id={team_id} ({start_date}..{end_date}): {e}"
        )
        return {
            "team_id": team_id,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "series": [],
            "meta": {"kind": "series_by_time", "status": "error", "error": str(e)},
        }


# ----------------------------
# Helpers (shared normalization)
# ----------------------------


def _require_non_empty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def _parse_iso_datetime(value: str) -> Optional[datetime]:
    """
    Best-effort ISO-8601 parser:
    - supports trailing 'Z'
    - returns None if parsing fails (we still allow the domain client to attempt)
    """
    if not isinstance(value, str) or not value.strip():
        return None
    v = value.strip()
    try:
        if v.endswith("Z"):
            v = v[:-1] + "+00:00"
        return datetime.fromisoformat(v)
    except Exception:
        return None


def _series_contains_team(series_node: Any, team_id: str) -> bool:
    if not isinstance(series_node, dict):
        return False
    teams = series_node.get("teams", [])
    if not isinstance(teams, list):
        return False

    for t in teams:
        if not isinstance(t, dict):
            continue
        base = t.get("baseInfo") or {}
        if isinstance(base, dict) and (base.get("id") == team_id):
            return True
    return False


def _normalize_series_list(series_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize series payloads from the Central Data Feed (allSeries->edges->node).

    Returns a stable shape used by downstream pipeline steps.
    """
    normalized: List[Dict[str, Any]] = []

    for series in series_list:
        if not isinstance(series, dict):
            continue

        normalized.append(
            {
                "series_id": series.get("id"),
                "start_time": series.get("startTimeScheduled"),
                "tournament_id": (series.get("tournament") or {}).get("id"),
                "tournament_name": (series.get("tournament") or {}).get("name"),
                "format": (series.get("format") or {}).get("nameShortened"),
                "teams": [
                    {
                        "team_id": ((team.get("baseInfo") or {}) if isinstance(team, dict) else {}).get("id"),
                        "team_name": ((team.get("baseInfo") or {}) if isinstance(team, dict) else {}).get("name"),
                        "name_shortened": ((team.get("baseInfo") or {}) if isinstance(team, dict) else {}).get(
                            "nameShortened"
                        ),
                        "score_advantage": team.get("scoreAdvantage") if isinstance(team, dict) else None,
                    }
                    for team in (series.get("teams") or [])
                    if isinstance(team, dict)
                ],
            }
        )

    return normalized
