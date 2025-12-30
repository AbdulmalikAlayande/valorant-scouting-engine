from typing import Any, Dict, List


def ingest_head_to_head_matches(team_id_1: str, team_id_2: str) -> Dict[str, Any]:
    """
    Fetch historical head-to-head series/games for two teams. Useful for
    prompts like 'Team A vs Team B history', exposing outcomes, maps, and
    recency. Validates IDs (non-empty and distinct) and returns a normalized
    stub payload with an empty 'matchups' list for downstream analysis.
    """
    if not team_id_1 or not team_id_1.strip() or not team_id_2 or not team_id_2.strip():
        raise ValueError("team_id_1 and team_id_2 are required")
    if team_id_1.strip() == team_id_2.strip():
        raise ValueError("team_id_1 and team_id_2 must be different")
    return {
        "team_id_1": team_id_1.strip(),
        "team_id_2": team_id_2.strip(),
        "matchups": [],
        "meta": {"kind": "head_to_head", "status": "stub"},
    }