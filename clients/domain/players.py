# Query & Mutation API
import json
from typing import Optional

from clients.grid.graphqlclient import GraphQLClient
from config.settings import GRID_QUERY_API_URL, GRID_API_KEY, PROJECT_ROOT
from config.utils import load_graphql_query


def get_player_by_id():
    pass


def get_player_by_name():
    pass


def get_player_by_external_id():
    """
    """
    pass


def get_team_players(team_id: Optional[str], filter_: dict | None = None, limit: int = 50):
    """
    Query to.

    filterable by:

    │Field        │ Type                   │ description
    ┌─────────────────────────────────────────────────────────┐
    │ roles       │ PlayerPlayerRoleFilter │ Filter players by role.
    │ teamIdFilter│ NullableIdFilter       │ Filter by a specific team ID. If this is null, no filter will be applied. If titleId
    │ titleId     │ ID                     │ Filter by a specific title ID.
    └─────────────────────────────────────────────────────────┘
    """

    if filter_ is None:
        filter_ = {}
    if not filter_.get("teamIdFilter"):
        filter_["teamIdFilter"] = {"id": team_id}

    query = load_graphql_query(query_name="player")

    all_players = []
    has_next_page = True
    after_cursor = None

    client = GraphQLClient(base_url=GRID_QUERY_API_URL, api_key=GRID_API_KEY)

    while has_next_page:
        variables = {"first": min(limit, 50), "filter": filter_, "after": after_cursor}
        data = client.execute(query=query, variables=variables)

        players_data = data.get("players", {})
        edges = players_data.get("edges", {})
        all_players.extend(edge.get("node", {}) for edge in edges)

        page_info = players_data.get('pageInfo', {})
        has_next_page = page_info.get('hasNextPage', False)
        after_cursor = page_info.get('endCursor')

        if len(all_players) >= limit:
            all_players = all_players[:limit]
            break

    response_file = PROJECT_ROOT / "clients" / "response" / "players.json"
    response_file.parent.mkdir(parents=True, exist_ok=True)
    with open(response_file, "w") as f:
        json.dump({"players": all_players, "total": len(all_players)}, f, indent=4)
    return all_players


if __name__ == "__main__":
    team_player = get_team_players(team_id="1079", filter_={})
    print(team_player)
