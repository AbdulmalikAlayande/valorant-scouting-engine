from pydantic import BaseModel


class Team(BaseModel):
    id: str
    name: str
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
            logo_url=node.get("logoUrl"),
            color_primary=node.get("colorPrimary"),
            organization_name=node.get("organization", {}).get("name")
        )