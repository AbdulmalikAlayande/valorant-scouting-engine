# Stats Feed API
import json

from clients.grid.graphqlclient import GraphQLClient
from config.settings import GRID_STATS_API_URL, GRID_API_KEY, PROJECT_ROOT


def load_graphql_query(query_name: str):
    """
    Loads a GraphQL query from a file based on the provided query name. The function constructs
    the file path using the given query name and reads the content of the file.

    Parameters:
    query_name: str
        The name of the GraphQL query file (without extension).

    Returns:
    str
        The content of the specified GraphQL query file as a string.

    Raises:
    FileNotFoundError
        If the specified query file does not exist.
    """
    query_file = PROJECT_ROOT / "clients" / "grid" / "queries" / f"{query_name}.graphql"
    return query_file.read_text()


def get_team_stats(team_id: str, filter_: dict):
    """
    Fetches team statistics based on the provided team ID and an optional filter.

    This function loads a GraphQL query to retrieve team statistics, executes the query
    using a GraphQL client, and saves the response data to a specified JSON file. The
    data is then returned as Python objects.

    Parameters:
    team_id: str
        The unique identifier of the team whose statistics are to be fetched.
    filter_: dict, optional
        A dictionary containing filter criteria for the statistics query. Defaults to None.

    Returns:
    dict
        The fetched team statistics as a dictionary.
    """
    query = load_graphql_query("teamstats")
    variables = {"teamId": team_id, "filter": filter_}

    client = GraphQLClient(base_url=GRID_STATS_API_URL, api_key=GRID_API_KEY)
    data = client.execute(query=query, variables=variables)
    response_file = PROJECT_ROOT / "clients" / "response" / "team-stats.json"
    response_file.parent.mkdir(parents=True, exist_ok=True)
    with open(response_file, "w") as f:
        json.dump(data, f, indent=4)
    return data


def get_team_stats_filter_by_tournament_id(team_id: str, tournament_id: str):
    """
    Retrieves team statistics filtered by tournament ID.

    Fetches and returns statistics for a specific team, filtered by the tournament
    ID provided.

    Parameters:
    team_id : str
        The unique identifier of the team whose statistics are to be retrieved.
    tournament_id : str
        The unique identifier of the tournament used for filtering the statistics.

    Returns:
    dict
        The statistics of the specified team filtered by tournament ID.
    """
    filter_ = {"tournamentId": tournament_id}
    return get_team_stats(team_id, filter_)


def get_team_stats_filter_by_start_date(team_id: str, start_date: str):
    """
    Retrieves team statistics filtered by a specific start date.

    This function fetches the statistics of a team identified by the given
    `team_id` and filters the results based on the provided `start_date`.
    The filtered statistics are acquired using an underlying utility to fetch
    team statistics with the applied criteria.

    Parameters:
    team_id: str
        The unique identifier of the team for which statistics need to
        be fetched.
    start_date: str
        The start date to filter team statistics, formatted as a string.

    Returns:
    Any
        The statistics of the team filtered by the provided start date. The
        exact return type depends on the implementation of the
        `get_team_stats` method.
    """
    filter_ = {"startedAt": start_date}
    return get_team_stats(team_id, filter_)


def get_team_game_stats(team_id: str, selection: dict):
    query = load_graphql_query("teamgamestats")
    variables = {"teamId": team_id, "selection": selection}

    client = GraphQLClient(base_url=GRID_STATS_API_URL, api_key=GRID_API_KEY)
    data = client.execute(query=query, variables=variables)
    response_file = PROJECT_ROOT / "clients" / "response" / "team-game-stats.json"
    response_file.parent.mkdir(parents=True, exist_ok=True)
    with open(response_file, "w") as f:
        json.dump(data, f, indent=4)
    return data

def get_match_stats(match_id: str):
    pass

def get_series_stats(series_id: str):
    pass

def player_stats(player_id: str):
    pass


if __name__ == '__main__':
    team_stats = get_team_stats(team_id="53625", filter_={"startedAt": {"period": "LAST_YEAR"}})
    print(team_stats)

    team_game_stats = get_team_game_stats(
        team_id="53625",
        selection={
            "first": 30,
            # "filter": {
            #
            # },
            "orderBy": [
                {
                    "field": "STARTED_AT",
                    "direction": "DESC"
                }
            ]
        }
    )