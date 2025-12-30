from clients.domain.teams import get_team_by_name, get_single_team
from models.teams import Team


def fetch_team_data(team_name: str | None = None, team_id: str | None = None):
    if not team_name and not team_id:
        raise ValueError("Team name or ID must be provided.")
    team_data = {}
    if team_name and team_name != "" and team_name != " ":
        data = get_team_by_name(team_name)
        print(data["teams"]["edges"][0]["node"]["title"]["name"])
        if data:
            if len(data["teams"]["edges"]) > 1:
                print("Multiple teams found with the same name. Please provide a more specific team name.")
                for team in data["teams"]["edges"]:
                    if (team["node"]["title"]["name"] == "Valorant"
                            or team["node"]["title"]["id"] == 6):
                        team_data = team["node"]
            elif len(data["teams"]["edges"]) == 1:
                team_data = data["teams"]["edges"][0]["node"]

    if team_data.__len__() < 1 and team_id:
        data = get_single_team(team_id)
        team_data = data["team"] if data else {}

    if team_data.__len__() < 1:
        print("No team found with the provided name or ID.")
        return None

    team: Team = Team.from_grid_response(**team_data)
    print(f"Team: {team}")
    return team

def fetch_team_stats(team_id: str):
    return

from enum import Enum

class TimeUnit(Enum):
    MONTHS = "months"
    YEARS = "years"

def _get_period_key(count: int, unit: TimeUnit) -> str | None:
    match (count, unit):
        case (1, TimeUnit.MONTHS):
            return "LAST_MONTH"
        case (1, TimeUnit.YEARS):
            return "LAST_YEAR"
        case (3, TimeUnit.MONTHS):
            return "LAST_3_MONTHS"
        case (6, TimeUnit.MONTHS):
            return "LAST_6_MONTHS"
        case _:
            return None


def fetch_team_stats_by_period(count: int, unit: TimeUnit):
    period_key = _get_period_key(count, unit)
    team_stats = get_team



def fetch_team_matches(team_id: str):
    return


