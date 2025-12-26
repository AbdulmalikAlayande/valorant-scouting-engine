import json
from clients.grid.graphqlclient import GraphQLClient
from config.settings import GRID_QUERY_API_URL, GRID_API_KEY, PROJECT_ROOT


def get_team_by_name(team_name: str):
    """
    GraphQL query to get team details by team name.
    """
    query = """
        query GetTeamByName ($teamName: String!) {
            teams(
                filter: { 
                    name: {
                        contains: $teamName
                        equals: $teamName
                    } 
                }
            ) {
                totalCount
                pageInfo {
                    hasPreviousPage
                    hasNextPage
                    startCursor
                    endCursor
                }
                totalCount
                edges {
                    cursor
                    node {
                        ...teamFields
                    }
                }
            }
        }
        fragment teamFields on Team {
            id
            name
            title {
                id
                name
                nameShortened
            }
            private
            colorPrimary
            colorSecondary
            logoUrl
            externalLinks {
                dataProvider {
                    name
                    description
                }
                externalEntity {
                    id
                }
            }
            organization {
                id
                name
            }
            updatedAt
        }
    """

    variables = {"teamName": team_name}

    client = GraphQLClient(base_url=GRID_QUERY_API_URL, api_key=GRID_API_KEY)
    data = client.execute(query=query, variables=variables)
    response_file = PROJECT_ROOT / "clients" / "response" / "team-by-name.json"
    response_file.parent.mkdir(parents=True, exist_ok=True)
    with open(response_file, "w") as f:
        json.dump(data, f, indent=4)
    return data


def get_single_team(team_id: str):
    """
    GraphQL query to get a single team by ID.
    """
    query = """
        query GetSingleTeam ($id: ID!) {
            team (id: $id) {
                ...teamFields
            }
        }
        fragment teamFields on Team {
            id
            name
            title {
                id
                name
                nameShortened
            }
            private
            colorPrimary
            colorSecondary
            logoUrl
            externalLinks {
                dataProvider {
                    name
                    description
                }
                externalEntity {
                    id
                }
            }
            organization {
                id
                name
            }
            updatedAt
        }
    """

    variables = {"id": team_id}

    client = GraphQLClient(base_url=GRID_QUERY_API_URL, api_key=GRID_API_KEY)
    data = client.execute(query=query, variables=variables)
    response_file = PROJECT_ROOT / "clients" / "response" / "team-by-id.json"
    response_file.parent.mkdir(parents=True, exist_ok=True)
    with open(response_file, "w") as f:
        json.dump(data, f, indent=4)
    return data


if __name__ == "__main__":
    get_team_by_name(team_name="Team Liquid")
    get_single_team(team_id="53625")
