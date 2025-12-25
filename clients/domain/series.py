# Series State API
import json
from pathlib import Path
from clients.grid.graphqlclient import GraphQLClient
from config.environment import env


API_KEY = env.str("GRID_API_KEY")
API_URL = env.str("GRID_QUERY_API")
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def get_recent_series():
    """
    GraphQL query to get recent VALORANT professional matches.
    """
    query = """
        query GetRecentSeries ($first: Int!) {
            allSeries (
                first: $first
                filter: {
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

    client = GraphQLClient(base_url=API_URL, api_key=API_KEY)
    data = client.execute(query=query, variables={"first": 50})
    response_file = PROJECT_ROOT / "response" / "recent-series.json"
    response_file.parent.mkdir(parents=True, exist_ok=True)
    with open(response_file, "w") as f:
        json.dump(data, f, indent=4)

    return data


def get_series_by_id():
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

    client = GraphQLClient(base_url=API_URL, api_key=API_KEY)
    data = client.execute(query=query, variables={"id": "2629390"})
    response_file = PROJECT_ROOT / "response" / "single-series.json"
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
    s1 = get_series_by_id()
    print(s1)


