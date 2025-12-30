from typing import Optional, Self

from pydantic import BaseModel


class Team(BaseModel):
    id: str
    name: str
    name_shortened: Optional[str] = None
    logo_url: Optional[str] = None
    color_primary: Optional[str] = None
    data_provider: Optional[str] = None
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None

    @classmethod
    def from_grid_response(cls, node: dict) -> Self:
        """
        Parse a GRID API team node (GraphQL 'node' dict) into a Team model.

        Expected keys include:
        - id (str), name (str)
        - optional shortName, logoUrl, colorPrimary
        - optional externalLinks.dataProvider.name
        - optional organization.{id,name}
        """

        return cls(
            id=node["id"],
            name=node["name"],
            name_shortened=node.get("nameShortened"),
            logo_url=node.get("logoUrl"),
            color_primary=node.get("colorPrimary"),
            data_provider=node.get("dataProvider"),
            organization_id=node.get("organizationId"),
            organization_name=node.get("organizationName"),
        )


class TeamStats(BaseModel):
    team_id: str
    total_matches: int
    win_rate: float
    kills_avg: float
    deaths_avg: float

