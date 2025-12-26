# Series State API
import json
from clients.grid.graphqlclient import GraphQLClient
from config.settings import GRID_QUERY_API_URL, GRID_API_KEY, PROJECT_ROOT


def get_recent_series():
    """
    GraphQL query to get recent VALORANT professional matches.
    """
    query = """
        query GetRecentSeries ($first: Int!) {
            allSeries (
                first: $first
                filter: {
                    types: [ESPORTS]  
                    titleIds: {
                        in: ["6"]
                    }
                }
            ) {
                totalCount,
                pageInfo {
                    hasPreviousPage
                    hasNextPage
                    startCursor
                    endCursor
                }
                edges {
                    cursor
                    node {
                        ...seriesFields
                    }
                }
            }
        }
        fragment seriesFields on Series {
            id
            title {
                name
                nameShortened
            }
            tournament {
                id
                name
                nameShortened
                startDate
                endDate
                titles {
                    id
                    name
                    nameShortened
                }
                teams {
                    id
                    name 
                    title {
                        id
                        name
                        nameShortened
                    }
                    rating
                    titles {
                        id
                        name
                        nameShortened
                    }
                    organization {
                        id
                        name
                    }
                }
                venueType
                prizePool {
                  amount
                }
            }
            startTimeScheduled
            format {
                id
                name
                nameShortened
            }
            teams {
                baseInfo {
                    name
                }
                scoreAdvantage
            }
        }
    """

    client = GraphQLClient(base_url=GRID_QUERY_API_URL, api_key=GRID_API_KEY)
    data = client.execute(query=query, variables={"first": 50})
    response_file = PROJECT_ROOT / "clients" / "response" / "recent-series.json"
    response_file.parent.mkdir(parents=True, exist_ok=True)
    with open(response_file, "w") as f:
        json.dump(data, f, indent=4)

    return data


def get_series_by_id(series_id: str):
    """
    GraphQL query to get a GRID series by ID, For VALORANT professional match.
    """

    query = """
        query GetSeriesById ($id: ID!) {
            series (id: $id) {
                ...seriesFields
            }
        }
        fragment seriesFields on Series {
            id
            title {
                name
                nameShortened
            }
            tournament {
                id
                name
                nameShortened
                startDate
                endDate
                titles {
                    id
                    name
                    nameShortened
                }
                teams {
                    id
                    name 
                    title {
                        id
                        name
                        nameShortened
                    }
                    rating
                    titles {
                        id
                        name
                        nameShortened
                    }
                    organization {
                        id
                        name
                    }
                }
                venueType
                prizePool {
                  amount
                }
            }
            startTimeScheduled
            format {
                id
                name
                nameShortened
            }
            teams {
                baseInfo {
                    name
                }
                scoreAdvantage
            }
        }
    """

    client = GraphQLClient(base_url=GRID_QUERY_API_URL, api_key=GRID_API_KEY)
    data = client.execute(query=query, variables={"id": series_id})
    response_file = PROJECT_ROOT / "clients" / "response" / "single-series.json"
    response_file.parent.mkdir(parents=True, exist_ok=True)
    with open(response_file, "w") as f:
        json.dump(data, f, indent=4)

    return data


def get_team_recent_series(team_id: str):
    """
    GraphQL query to get recent series for a specific team with the team ID.
    """
    query = """
        query GetTeamRecentSeries ($teamId: ID!, $first: Int!) {
            allSeries (
                first: $first
                filter: {
                    teamIds: {
                        in: [$teamId]
                    }
                    types: [ESPORTS] 
                    titleIds: {
                        in: ["6"]
                    }
                }
            ) {
                totalCount,
                pageInfo {
                    hasPreviousPage
                    hasNextPage
                    startCursor
                    endCursor
                }
                edges {
                    cursor
                    node {
                        ...seriesFields
                    }
                }
            }
        }
        fragment seriesFields on Series {
            id
            title {
                name
                nameShortened
            }
            tournament {
                id
                name
                nameShortened
                startDate
                endDate
                titles {
                    id
                    name
                    nameShortened
                }
                teams {
                    id
                    name 
                    title {
                        id
                        name
                        nameShortened
                    }
                    rating
                    titles {
                        id
                        name
                        nameShortened
                    }
                    organization {
                        id
                        name
                    }
                }
                venueType
                prizePool {
                  amount
                }
            }
            startTimeScheduled
            format {
                id
                name
                nameShortened
            }
            teams {
                baseInfo {
                    name
                }
                scoreAdvantage
            }
        }
    """

    variables = {"teamId": team_id, "first": 10}

    client = GraphQLClient(base_url=GRID_QUERY_API_URL, api_key=GRID_API_KEY)
    data = client.execute(query=query, variables=variables)
    response_file = PROJECT_ROOT / "clients" / "response" / "team-recent-series.json"
    response_file.parent.mkdir(parents=True, exist_ok=True)
    with open(response_file, "w") as f:
        json.dump(data, f, indent=4)
    return data


if __name__ == "__main__":
    print("🚀 Connecting To GRID API...")
    print("-" * 50)
    print("\n📊 TEST 1: Getting recent VALORANT series...")
    s = get_recent_series()
    print(s)
    print("\n" + "-" * 50)
    print("\n📊 TEST 2: Getting VALORANT series by ID...")
    s1 = get_series_by_id("2629390")
    print(s1)
    print("\n" + "-" * 50)
    print("\n📊 TEST 3: Getting recent series for a specific team...")
    s2 = get_team_recent_series("60")
    print(s2)


