# Stats Feed API
import json
from typing import Dict, Any, Optional

from clients.grid.graphqlclient import GraphQLClient
from config.settings import GRID_STATS_API_URL, GRID_API_KEY, PROJECT_ROOT
from config.utils import load_graphql_query


def get_team_statistics(
        team_id: str,
        time_window: Optional[str] = None,
        tournament_ids: Optional[list[str]] = None
) -> Dict[str, Any]:
    """
    Get aggregated team statistics from Stats Feed API.

    Args:
        team_id: Team ID
        time_window: "LAST_MONTH", "LAST_3_MONTHS", "LAST_6_MONTHS", "LAST_YEAR"
        tournament_ids: List of tournament IDs to filter by

    Returns:
        Team statistics including series, game, and segment-level aggregations

    Note: time_window and tournament_ids are mutually exclusive
    """
    query = load_graphql_query("teamstats")

    # Build filter - time_window OR tournament_ids, not both
    filter_ = {}
    if time_window:
        filter_["startedAt"] = {"period": time_window}
    elif tournament_ids:
        filter_["tournament"] = {"id": {"in": tournament_ids}}
    else:
        filter_["startedAt"] = {"period": "LAST_3_MONTHS"}  # Default

    variables = {"teamId": team_id, "filter": filter_}

    client = GraphQLClient(base_url=GRID_STATS_API_URL, api_key=GRID_API_KEY)
    data = client.execute(query=query, variables=variables)

    response_file = PROJECT_ROOT / "clients" / "response" / "team-statistics.json"
    response_file.parent.mkdir(parents=True, exist_ok=True)
    with open(response_file, "w") as f:
        json.dump(data, f, indent=4)

    return data.get("teamStatistics", {})


def get_team_game_statistics(
        team_id: str,
        time_window: Optional[str] = None,
        map_ids: Optional[list[str]] = None,
        opponent_team_ids: Optional[list[str]] = None,
        limit: int = 50
) -> Dict[str, Any]:
    """
    Get aggregated team game (map-level) statistics.

    Args:
        team_id: Team ID
        time_window: "LAST_MONTH", "LAST_3_MONTHS", "LAST_6_MONTHS", "LAST_YEAR".
        map_ids: Filter by specific map IDs
        opponent_team_ids: Filter by specific opponent teams
        limit: Number of games to aggregate (default 50)

    Returns:
        Team game statistics including map-specific data
    """
    query = load_graphql_query("teamgamestats")

    # Build selection filters
    selection: Dict[str, Any] = {"first": limit}

    game_filter = {}
    if time_window:
        game_filter["startedAt"] = {"period": time_window}
    if map_ids:
        game_filter["mapIds"] = {"in": map_ids}
    if opponent_team_ids:
        game_filter["teams"] = {"id": {"in": opponent_team_ids}}

    if game_filter:
        selection["filter"] = game_filter

    # Order by most recent
    selection["orderBy"] = [{"field": "STARTED_AT", "direction": "DESC"}]

    variables = {"teamId": team_id, "selection": selection}

    client = GraphQLClient(base_url=GRID_STATS_API_URL, api_key=GRID_API_KEY)
    data = client.execute(query=query, variables=variables)

    response_file = PROJECT_ROOT / "clients" / "response" / "team-game-statistics.json"
    response_file.parent.mkdir(parents=True, exist_ok=True)
    with open(response_file, "w") as f:
        json.dump(data, f, indent=4)

    return data.get("teamGameStatistics", {})


def get_player_statistics(
        player_id: str,
        time_window: Optional[str] = None,
        tournament_ids: Optional[list[str]] = None
) -> Dict[str, Any]:
    """
    Get aggregated player statistics.

    Args:
        player_id: Player ID
        time_window: "LAST_MONTH", "LAST_3_MONTHS", "LAST_6_MONTHS", "LAST_YEAR".
        tournament_ids: List of tournament IDs to filter by

    Returns:
        Player statistics including series and game-level aggregations
    """
    query = load_graphql_query("playerstats")

    # Build filter
    filter_ = {}
    if time_window:
        filter_["startedAt"] = {"period": time_window}
    elif tournament_ids:
        filter_["tournament"] = {"id": {"in": tournament_ids}}
    else:
        filter_["startedAt"] = {"period": "LAST_3_MONTHS"}

    variables = {"playerId": player_id, "filter": filter_}

    client = GraphQLClient(base_url=GRID_STATS_API_URL, api_key=GRID_API_KEY)
    data = client.execute(query=query, variables=variables)

    response_file = PROJECT_ROOT / "clients" / "response" / "player-statistics.json"
    response_file.parent.mkdir(parents=True, exist_ok=True)
    with open(response_file, "w") as f:
        json.dump(data, f, indent=4)

    return data.get("playerStatistics", {})


def get_game_statistics(
        title_id: str,
        time_window: Optional[str] = None,
        tournament_ids: Optional[list[str]] = None,
        include_children: bool = True
) -> Dict[str, Any]:
    """
    Get aggregated game statistics across the entire title / tournament.
    Used for meta-analysis, not team-specific scouting.

    Args:
        title_id: Game title ID (6 for VALORANT)
        time_window: "LAST_MONTH", "LAST_3_MONTHS", "LAST_6_MONTHS", "LAST_YEAR".
        tournament_ids: List of tournament IDs
        include_children: Include child tournaments

    Returns:
        Game-level statistics including draft actions, map picks, etc.

    Note: Filters are mutually exclusive
    """
    query = load_graphql_query("gamestats")

    # Build filter - only one can be used
    filter_ = {}
    if time_window:
        filter_["startedAt"] = {"period": time_window}
    elif tournament_ids:
        filter_["tournament"] = {
            "id": {"in": tournament_ids},
            "includeChildren": include_children
        }
    else:
        filter_["startedAt"] = {"period": "LAST_3_MONTHS"}

    variables = {"titleId": title_id, "filter": filter_}

    client = GraphQLClient(base_url=GRID_STATS_API_URL, api_key=GRID_API_KEY)
    data = client.execute(query=query, variables=variables)

    response_file = PROJECT_ROOT / "clients" / "response" / "game-statistics.json"
    response_file.parent.mkdir(parents=True, exist_ok=True)
    with open(response_file, "w") as f:
        json.dump(data, f, indent=4)

    return data.get("gameStatistics", {})


# Simplified helper functions for common use cases
def get_team_stats_last_3_months(team_id: str) -> Dict[str, Any]:
    """Shortcut: Get team stats for the last 3 months"""
    return get_team_statistics(team_id, time_window="LAST_3_MONTHS")


def get_team_stats_by_tournament(team_id: str, tournament_id: str) -> Dict[str, Any]:
    """Shortcut: Get team stats for a specific tournament"""
    return get_team_statistics(team_id, tournament_ids=[tournament_id])


def get_team_map_performance(team_id: str, map_ids: list[str]) -> Dict[str, Any]:
    """Shortcut: Get team performance on specific maps"""
    return get_team_game_statistics(
        team_id,
        map_ids=map_ids,
        time_window="LAST_3_MONTHS"
    )


if __name__ == '__main__':
    # Test: Team stats with a time window
    team_stats = get_team_statistics(team_id="1079", time_window="LAST_3_MONTHS")
    print(f"Team stats games count: {team_stats.get('game', {}).get('count')}")

    # Test: Team game stats (map-specific)
    team_game_stats = get_team_game_statistics(
        team_id="1079",
        time_window="LAST_MONTH",
        limit=30
    )
    print(f"Team game stats count: {team_game_stats.get('count')}")

    # Test: Player stats
    player_stats = get_player_statistics(player_id="2512", time_window="LAST_3_MONTHS")
    print(f"Player series count: {player_stats.get('series', {}).get('count')}")
