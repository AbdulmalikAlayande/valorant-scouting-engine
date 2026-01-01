import json
from typing import Dict, Any
from clients.grid.graphqlclient import GraphQLClient
from config.settings import GRID_SERIES_STATE_API_URL, GRID_API_KEY, PROJECT_ROOT
from config.utils import load_graphql_query


def get_series_state(series_id: str) -> Dict[str, Any]:
    """
    Fetch detailed series state from Series State API.
    Returns games, rounds, players, agents, etc.
    """
    query = load_graphql_query("seriesstate")

    variables = {"id": series_id}

    client = GraphQLClient(base_url=GRID_SERIES_STATE_API_URL, api_key=GRID_API_KEY)
    data = client.execute(query=query, variables=variables)

    response_file = PROJECT_ROOT / "clients" / "response" / "series-state.json"
    response_file.parent.mkdir(parents=True, exist_ok=True)
    with open(response_file, "w") as f:
        json.dump(data, f, indent=4)

    return data.get("series", {})


if __name__ == "__main__":
    series_state = get_series_state(series_id="2629390")
    print(series_state)
