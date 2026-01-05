from typing import Any, Dict, List

from clients.domain.players import get_team_players
from clients.domain.teams import get_team_by_name, get_single_team
from models.teams import Team
from config.globalutilitylogger import get_logger


logger = get_logger(__name__)

def ingest_team_by_name(team_name: str) -> Team:
    """
    Resolve a team by name and return normalized identifiers/basic info. Uses
    the team-by-name shape (teams->edges->node) and, when multiple matches
    exist, prefers the VALORANT entry. Returns a dict with 'team', 'candidates',
    and 'meta' to support downstream selection and storage.
    """
    if not team_name or not team_name.strip():
        raise ValueError("team_name is required")

    query = team_name.strip()
    data = get_team_by_name(query) or {}
    edges: List[Dict[str, Any]] = (
        data.get("teams", {}).get("edges", []) if isinstance(data, dict) else []
    )

    # Collect candidate nodes
    candidates: List[Dict[str, Any]] = []
    for edge in edges:
        node = (edge or {}).get("node", {})
        if node:
            candidates.append(
                {
                    "id": node.get("id"),
                    "name": node.get("name"),
                    "nameShortened": node.get("nameShortened"),
                    "logoUrl": node.get("logoUrl"),
                    "colorPrimary": node.get("colorPrimary"),
                    "title": {
                        "id": (node.get("title") or {}).get("id"),
                        "name": (node.get("title") or {}).get("name"),
                    },
                    "dataProvider": next(
                        (
                            (link.get("dataProvider") or {}).get("name")
                            for link in node.get("externalLinks") or []
                            if "riot esports api"
                            in ((link.get("dataProvider") or {}).get("description") or "").lower()
                        ),
                        None,
                    ),
                    "organizationId": (node.get("organization") or {}).get("id"),
                    "organizationName": (node.get("organization") or {}).get("name"),
                    "raw": node,
                }
            )

    # Prefer VALORANT when ambiguous
    selected = None
    if len(candidates) == 1:
        selected = candidates[0]
    elif len(candidates) > 1:
        valorant_matches = [
            c
            for c in candidates
            if isinstance(c.get("title"), dict)
            and isinstance(c["title"].get("name"), str)
            and c["title"]["name"].strip().lower() == "valorant"
        ]
        selected = valorant_matches[0] if valorant_matches else candidates[0]

    status = "ok" if selected else ("not_found" if not candidates else "ambiguous")
    selected["meta"] = {"kind": "team_lookup", "status": status}

    team = Team.from_grid_response(selected) if selected else None
    logger.info(f"Team lookup: {team}")
    return team


def ingest_team_by_id(team_id: str) -> Team:
    """

    """
    if not team_id or not team_id.strip():
        raise ValueError("team_id is required")

    query = team_id.strip()
    data = get_single_team(query) or {}
    team_data = data.get("team", {})
    status = "ok" if team_data else "not_found"
    team_data["meta"] = {"kind": "team_lookup", "status": status}
    return Team.from_grid_response(team_data)


def ingest_team_players(team_id: str) -> Dict[str, Any]:
    """
    Fetch the current roster for a team. Used for player-level analysis and
    role detection. Returns a normalized dict containing player data ready
    for downstream transforms and database storage.
    """
    if not team_id or not team_id.strip():
        raise ValueError("team_id is required")

    team_id = team_id.strip()
    data = get_team_players(team_id=team_id)

    if not data:
        logger.warning(f"No player data found for team_id: {team_id}")
        return {
            "team_id": team_id,
            "players": [],
            "meta": {"kind": "team_roster", "status": "not_found"},
        }

    # Extract players from response
    players = [_normalize_player(player_node) for player_node in data]

    logger.info(f"Ingested {len(players)} players for team {team_id}")

    return {
        "team_id": team_id,
        "players": players,
        "meta": {"kind": "team_roster", "status": "ok", "count": len(players)},
    }


def _normalize_player(player_node: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and normalize player data from GRID response node.
    Finds VALORANT Riot Esports API external ID if available.
    """
    # Find VALORANT Riot Esports API external ID
    external_id = _extract_valorant_external_id(player_node.get("externalLinks", []))

    return {
        "id": player_node.get("id"),
        "nickname": player_node.get("nickname"),
        "title_id": player_node.get("title", {}).get("id"),
        "title_name": player_node.get("title", {}).get("name"),
        "team_id": player_node.get("team", {}).get("id"),
        "team_name": player_node.get("team", {}).get("name"),
        "external_entity_id": external_id,  # Riot's player ID
        "roles": [role.get("name") for role in player_node.get("roles", [])],
        "image_url": player_node.get("imageUrl"),
    }


def _extract_valorant_external_id(external_links: List[Dict[str, Any]]) -> str | None:
    """
    Extract VALORANT Riot Esports API external entity ID from links.
    Returns None if not found.
    """
    for link in external_links:
        provider = link.get("dataProvider", {})
        provider_name = (provider.get("name") or "").lower()
        provider_desc = (provider.get("description") or "").lower()

        # Match VALORANT + Riot Esports API
        if provider_name == "valorant" and "riot esports api" in provider_desc:
            return link.get("externalEntity", {}).get("id")

    return None
