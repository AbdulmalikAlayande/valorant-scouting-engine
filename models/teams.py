from typing import Optional

from pydantic import BaseModel


class Team(BaseModel):
    id: str
    name: str
    name_shortened: Optional[str]
    logo_url: str | None = None
    color_primary: str | None = None
    organization_name: str | None = None

    @classmethod
    def from_grid_response(cls, node: dict):
        """
        To parse GRID API response
        """
        return cls(
            id=node["id"],
            name=node["name"],
            name_shortened=node.get("shortName"),
            logo_url=node.get("logoUrl"),
            color_primary=node.get("colorPrimary"),
            organization_name=node.get("organization", {}).get("name")
        )

class TeamStats(BaseModel):
    team_id: str
    total_matches: int
    win_rate: float
    kills_avg: float
    deaths_avg: float

