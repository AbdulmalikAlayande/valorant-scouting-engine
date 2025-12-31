from typing import Any, Dict, Optional, Self, List

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
    def from_grid_response(cls, node: Dict[str, Any]) -> Self:
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
    aggregated_series_ids: List[str]

    # --- General Performance ---
    total_series: int
    series_win_rate: float
    total_games: int
    game_win_rate: float

    # --- Combat Metrics (Totals) ---
    kills_total: int
    deaths_total: int
    assists_total: int

    # --- Combat Metrics (Averages) ---
    kills_avg: float
    deaths_avg: float
    assists_avg: float
    kd_ratio: float
    first_bloods_avg: float

    # --- VALORANT Specific Objectives (Averages) ---
    spikes_planted_avg: float
    spikes_defused_avg: float
    bomb_explosions_avg: float
    ultimate_orbs_captured_avg: float

    # --- Economy and Sustainability (Averages) ---
    avg_net_worth: float
    avg_spend: float

    # --- Tactical Tendencies (Win Rates) ---
    pistol_round_win_rate: float
    attack_win_rate: float
    defense_win_rate: float
