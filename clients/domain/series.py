# Series State API
import json
from typing import Dict, Any, List

from clients.grid.graphqlclient import GraphQLClient
from config.settings import GRID_QUERY_API_URL, GRID_API_KEY, PROJECT_ROOT
from config.utils import load_graphql_query


def get_recent_series(limit: int = 50) -> Dict[str, Any]:
    """
    Get recent VALORANT professional matches.

    Args:
        limit: Number of series to fetch (default 50)

    Returns:
        Dict containing series data and pagination info
    """
    query = load_graphql_query("series")

    # Base filter for VALORANT (titleId "6") and ESPORTS type
    variables = {
        "first": limit,
        "filter": {
            "types": ["ESPORTS"],
            "titleIds": {"in": ["6"]}
        }
    }

    client = GraphQLClient(base_url=GRID_QUERY_API_URL, api_key=GRID_API_KEY)
    data = client.execute(query=query, variables=variables)

    response_file = PROJECT_ROOT / "clients" / "response" / "recent-series.json"
    response_file.parent.mkdir(parents=True, exist_ok=True)
    with open(response_file, "w") as f:
        json.dump(data, f, indent=4)

    return data.get("allSeries", {})


def get_series_by_id(series_id: str) -> Dict[str, Any]:
    """
    Get a specific GRID series by its ID.

    Args:
        series_id: The GRID series identifier

    Returns:
        Dict containing detailed series data
    """
    query = load_graphql_query("seriesbyid")
    variables = {"id": series_id}

    client = GraphQLClient(base_url=GRID_QUERY_API_URL, api_key=GRID_API_KEY)
    data = client.execute(query=query, variables=variables)

    response_file = PROJECT_ROOT / "clients" / "response" / "single-series.json"
    response_file.parent.mkdir(parents=True, exist_ok=True)
    with open(response_file, "w") as f:
        json.dump(data, f, indent=4)

    return data.get("series", {})


def get_team_recent_series(team_id: str, limit: int = 50) -> Dict[str, Any]:
    """
    Get recent series for a specific team.

    Args:
        team_id: GRID team identifier
        limit: Number of series to fetch (default 50)

    Returns:
        Dict containing the team's recent series
    """

    query = load_graphql_query("series")

    all_series: List[Dict[str, Any]] = []
    has_next_page = True
    after_cursor = None
    page_count = 0
    max_pages = 10

    client = GraphQLClient(base_url=GRID_QUERY_API_URL, api_key=GRID_API_KEY)

    while has_next_page and page_count < max_pages:
        variables = {
            "first": min(limit, 50),
            "filter": {
                "teamIds": {"in": [team_id]},
                "titleIds": {"in": ["6"]},  # VALORANT
                "types": ["ESPORTS"]
            }
        }

        if after_cursor:
            variables["after"] = after_cursor

        data = client.execute(query=query, variables=variables)
        series_data = data.get("allSeries", {})
        edges = series_data.get("edges", [])

        for edge in edges:
            if isinstance(edge, dict):
                node = edge.get("node")
                if node:
                    all_series.append(node)

        if len(all_series) >= limit:
            all_series = all_series[:limit]
            break

        page_info = series_data.get("pageInfo", {})
        has_next_page = page_info.get("hasNextPage", False)
        after_cursor = page_info.get("endCursor")
        page_count += 1

    response_file = PROJECT_ROOT / "clients" / "response" / "team-recent-series.json"
    response_file.parent.mkdir(parents=True, exist_ok=True)
    with open(response_file, "w") as f:
        json.dump({"total": len(all_series), "series": all_series}, f, indent=4)

    return {"total": len(all_series), "series": all_series}


def get_series_by_tournament(tournament_id: str, limit) -> Dict[str, Any]:
    query = load_graphql_query("series")

    all_series: List[Dict[str, Any]] = []
    has_next_page = True
    after_cursor = None
    page_count = 0
    max_pages = 10

    client = GraphQLClient(base_url=GRID_QUERY_API_URL, api_key=GRID_API_KEY)
    while has_next_page and page_count < max_pages:
        variables = {
            "first": min(limit, 50),
            "filter": {
                "tournament": {"id": {"in": [tournament_id]}},
                "titleIds": {"in": ["6"]},  # VALORANT
                "types": ["ESPORTS"]
            }
        }

        if after_cursor:
            variables["after"] = after_cursor

        data = client.execute(query=query, variables=variables)
        series_data = data.get("allSeries", {})
        edges = series_data.get("edges", [])

        for edge in edges:
            if isinstance(edge, dict):
                node = edge.get("node")
                if node:
                    all_series.append(node)

        if len(all_series) >= limit:
            all_series = all_series[:limit]
            break

        page_info = series_data.get("pageInfo", {})
        has_next_page = page_info.get("hasNextPage", False)
        after_cursor = page_info.get("endCursor")
        page_count += 1

    response_file = PROJECT_ROOT / "clients" / "response" / "series-by-tournament.json"
    response_file.parent.mkdir(parents=True, exist_ok=True)
    with open(response_file, "w") as f:
        json.dump({"total": len(all_series), "series": all_series}, f, indent=4)

    return {"total": len(all_series), "series": all_series}


def get_series_by_time_range(start_date: str, end_date: str, limit: int = 50) -> Dict[str, Any]:
    query = load_graphql_query("series")

    all_series: List[Dict[str, Any]] = []
    has_next_page = True
    after_cursor = None
    page_count = 0
    max_pages = 10

    client = GraphQLClient(base_url=GRID_QUERY_API_URL, api_key=GRID_API_KEY)
    while has_next_page and page_count < max_pages:
        variables = {
            "first": min(limit, 50),
            "filter": {
                "startTimeScheduled": {
                    "gte": start_date,  # In ISO format: e.g. "2024-04-24T15:00:07+02:00",
                    "lte": end_date  # In ISO format: e.g. "2024-04-25T15:00:07+02:00"
                },
                "titleIds": {"in": ["6"]},  # VALORANT
                "types": ["ESPORTS"]
            }
        }

        if after_cursor:
            variables["after"] = after_cursor

        data = client.execute(query=query, variables=variables)
        series_data = data.get("allSeries", {})
        edges = series_data.get("edges", [])

        for edge in edges:
            if isinstance(edge, dict):
                node = edge.get("node")
                if node:
                    all_series.append(node)

        if len(all_series) >= limit:
            all_series = all_series[:limit]
            break

        page_info = series_data.get("pageInfo", {})
        has_next_page = page_info.get("hasNextPage", False)
        after_cursor = page_info.get("endCursor")
        page_count += 1

    response_file = PROJECT_ROOT / "clients" / "response" / "series-by-time-range.json"
    response_file.parent.mkdir(parents=True, exist_ok=True)
    with open(response_file, "w") as f:
        json.dump({"total": len(all_series), "series": all_series}, f, indent=4)

    return {"total": len(all_series), "series": all_series}


if __name__ == "__main__":
    print("🚀 Fetching recent series...")
    recent_series = get_recent_series(limit=5)
    print(f"Total count available: {recent_series.get('totalCount')}")

    print("\n📊 Fetching recent series for team 1079...")
    team_series = get_team_recent_series(team_id="1079", limit=5)
    print(team_series.get("total"))

    print("\n📊 Fetching series in a specific tournament: ID is 826660...")
    tournament_series = get_series_by_tournament(tournament_id="757074", limit=5)
    print(tournament_series.get("total"))

    print("\n📊 Fetching series in a given time range/window")
    series_in_given_time_range = get_series_by_time_range(start_date="2024-04-24T15:00:07+02:00", end_date="2024-10-25T15:00:07+02:00", limit=5)
    print(series_in_given_time_range.get("total"))
