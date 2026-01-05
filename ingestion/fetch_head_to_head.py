from typing import Any, Dict, List
from clients.domain.series import get_team_recent_series
from config.globalutilitylogger import get_logger

_logger = get_logger(__name__)

def ingest_head_to_head_matches(team_id_1: str, team_id_2: str, limit: int = 100) -> Dict[str, Any]:
    """
    Fetch historical head-to-head series/games for two teams.
    """
    if not team_id_1 or not team_id_1.strip() or not team_id_2 or not team_id_2.strip():
        raise ValueError("team_id_1 and team_id_2 are required")
    
    team_id_1 = team_id_1.strip()
    team_id_2 = team_id_2.strip()
    
    if team_id_1 == team_id_2:
        raise ValueError("team_id_1 and team_id_2 must be different")

    try:
        # Fetch recent series for team_id_1 and filter for matches against team_id_2
        data = get_team_recent_series(team_id=team_id_1, limit=limit)
        series_list = data.get("series", [])
        
        matchups = []
        for series in series_list:
            teams = series.get("teams", [])
            team_ids = [t.get("baseInfo", {}).get("id") for t in teams if isinstance(t, dict)]
            
            if team_id_2 in team_ids:
                matchups.append(series)

        _logger.info(f"Found {len(matchups)} head-to-head matches between {team_id_1} and {team_id_2}")
        
        return {
            "team_id_1": team_id_1,
            "team_id_2": team_id_2,
            "matchups": matchups,
            "meta": {
                "kind": "head_to_head",
                "status": "success",
                "count": len(matchups)
            },
        }
    except Exception as e:
        _logger.error(f"Failed to ingest head-to-head matches: {e}")
        return {
            "team_id_1": team_id_1,
            "team_id_2": team_id_2,
            "matchups": [],
            "meta": {
                "kind": "head_to_head",
                "status": "error",
                "error": str(e)
            },
        }
